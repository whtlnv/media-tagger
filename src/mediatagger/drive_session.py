import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from mediatagger.backup import back_up, default_backup_root, failure_reason, newest_backup, restore
from mediatagger.drive_config import required_roots
from mediatagger.library import Library, tags_db_path
from mediatagger.status_bar import NO_LIBRARY_TEXT
from mediatagger.thumbnail_cache import open_thumbnail_cache

APP_PACKAGE = Path(__file__).parent  # its drive is never written while the app runs
_FULLSCREEN_SETTLE_MS = 1000
NO_LIBRARY_VIEWING_ONLY_TEXT = "No library — viewing only"
DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT = "{} has no tag library — viewing only"
LIBRARY_CANT_BE_OPENED_TEXT = "Library on {} can't be opened — viewing only"
CREATE_LIBRARY_QUESTION = "Create a tag library on {}?"
DELETE_QUESTION = 'Delete "{}"? It can\'t be undone.'
RESTORE_LIBRARY_QUESTION = "The tag library on {} is missing or damaged. Restore the backup from {:%Y-%m-%d %H:%M}?"
BACKING_UP_TEXT = "⟳ Backing up database…"
BACKED_UP_TEXT = "✓ Backed up"
BACKUP_FAILED_TEXT = "✗ Backup failed: {}"
RESTORED_BACKUP_TEXT = "✓ Restored backup from {:%Y-%m-%d %H:%M}"
RESTORE_FAILED_TEXT = "✗ Restore failed: {}"
CANT_RESTORE_TO_READ_ONLY_DRIVE_TEXT = "{} is read-only — its backup can't be restored"


class DriveSession:
    """The drive whose media is open: finding its library, asking to create or restore it, backing it up, and saying
    so in the status bar. One per window, shared by everything that shows that drive's media."""

    def __init__(self, status_bar, window, is_mount_point=os.path.ismount, ask_to_create_library=None, app_location=APP_PACKAGE,
        backup_root=None, backup_clock=lambda: datetime.now(timezone.utc), ask_to_restore_library=None, home=None, ask_to_delete=None,
    ):
        self.status_bar = status_bar
        self.window = window  # questions are asked over it
        self.is_mount_point = is_mount_point
        self.app_location = app_location
        self.backup_root = backup_root or default_backup_root()
        self.backup_clock = backup_clock
        self.ask_to_create_library = ask_to_create_library or self._ask_yes_or_no
        self.ask_to_restore_library = ask_to_restore_library or self._ask_yes_or_no
        self.ask_to_delete = ask_to_delete or self._ask_to_delete
        self.declined_create_drives = set()
        self.declined_restore_drives = set()
        self.library = None  # the open Library of the current drive, if it has one
        self.drive = None
        self.required_roots = ()  # the tag roots the current drive's config says every file should have
        self.read_only = False
        self.home = home or Path.home()  # the cache home falls back to its .cache folder
        self._thumbnail_cache = None
        self._thumbnail_cache_for = None

    def open_library(self, path):
        drive = next(folder for folder in (path, *path.parents) if self.is_mount_point(folder))
        if self.library and drive == self.drive:
            return
        if self.library:
            self.back_up_library()
        self.library = None
        self.drive = drive
        self.required_roots, problem = required_roots(drive)
        self.status_bar.show_config_problem(problem or "")
        if self._never_holds_a_library(drive):
            self.status_bar.show_library(NO_LIBRARY_VIEWING_ONLY_TEXT, read_only=False)
            return
        read_only = not os.access(drive, os.W_OK)
        if not tags_db_path(drive).exists():
            if not self._open_missing_library(drive, read_only):
                return
        elif not self._open_existing_library(drive, read_only):
            return
        self._show_library_status("", read_only)

    def thumbnail_cache(self):
        """The current drive's thumbnails: on disk under its drive id when it has a library, else in memory for the
        session. One per drive, kept while it stays the current one."""
        drive_id = self.library.drive_id if self.library else None
        if self._thumbnail_cache_for != (self.drive, drive_id):
            self._thumbnail_cache = open_thumbnail_cache(drive_id, self.home, self.app_drive(), self.drive)
            self._thumbnail_cache_for = (self.drive, drive_id)
        return self._thumbnail_cache

    def app_drive(self):
        """The drive the app runs from, unless that is the system disk, which the home folder (and with it the cache
        home and the state file) may well be on."""
        app_drive = next((folder for folder in self.app_location.parents if self.is_mount_point(folder)), Path("/"))
        return None if app_drive == Path("/") else app_drive

    def tags_can_be_saved(self):
        return self.library is not None and not self.read_only

    def close(self):
        if self.library:
            self.back_up_library()

    def _open_missing_library(self, drive, read_only):
        """Whether the drive without a tags.db ended up with one open, restored from a backup or created; if not, says why."""
        if read_only:
            self._show_library_status(NO_LIBRARY_TEXT, read_only=True)
            return False
        if tags_db_path(drive).parent.is_dir() and self._offer_to_restore_library(drive):
            return True
        if not self._agrees_to_create_library(drive):
            self._show_library_status(DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT.format(drive.name), read_only=False)
            return False
        self.library = Library.create(drive)
        return True

    def _open_existing_library(self, drive, read_only):
        """Whether the drive's tags.db ended up open, as it was or restored from a backup; if not, says why."""
        try:
            self.library = Library.open(drive)
        except (sqlite3.DatabaseError, OSError):
            if read_only:
                text = CANT_RESTORE_TO_READ_ONLY_DRIVE_TEXT if newest_backup(self.backup_root, drive.name) else LIBRARY_CANT_BE_OPENED_TEXT
                self._show_library_status(text.format(drive.name), read_only=True)
                return False
            if not self._offer_to_restore_library(drive):
                self._show_library_status(LIBRARY_CANT_BE_OPENED_TEXT.format(drive.name), read_only=False)
                return False
            return True
        self.back_up_library()
        return True

    def back_up_library(self):
        """Backs up the open library, saying so in the status bar; whether the backup was made."""
        self.status_bar.show_background(BACKING_UP_TEXT)
        # Paint it before the backup blocks the event loop; user input waits, so no queued key runs mid-open or mid-close.
        # Not while the window is still unshown (being built): there is nothing to paint, and a caller's timer would fire too early.
        if self.window.isVisible():
            QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        outcome = back_up(self.library, self.backup_root, clock=self.backup_clock)
        if outcome is not None:
            self.status_bar.show_background(BACKUP_FAILED_TEXT.format(outcome.failure))
            return False
        self.status_bar.show_background(BACKED_UP_TEXT, finished=True)
        return True

    def _show_library_status(self, text, read_only):
        self.read_only = read_only
        self.status_bar.show_library(text, read_only)

    def _never_holds_a_library(self, drive):
        return drive == Path("/") or drive in self.app_location.parents

    def _offer_to_restore_library(self, drive):
        backup = newest_backup(self.backup_root, drive.name)
        if not backup or drive in self.declined_restore_drives:
            return False
        taken_at = backup.taken_at.astimezone()
        if not self.ask_to_restore_library(RESTORE_LIBRARY_QUESTION.format(drive.name, taken_at)):
            self.declined_restore_drives.add(drive)
            return False
        try:
            restore(drive, backup.path, self.backup_clock)
            self.library = Library.open(drive)
        except (OSError, sqlite3.Error) as error:
            self.status_bar.show_background(RESTORE_FAILED_TEXT.format(failure_reason(error)))
            return False
        self.status_bar.show_background(RESTORED_BACKUP_TEXT.format(taken_at), finished=True)
        return True

    def _agrees_to_create_library(self, drive):
        if drive in self.declined_create_drives:
            return False
        if not self.ask_to_create_library(CREATE_LIBRARY_QUESTION.format(drive.name)):
            self.declined_create_drives.add(drive)
            return False
        return True

    def _ask_yes_or_no(self, question):
        if not self.window.isVisible():
            self._show_and_settle()
        buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        return QMessageBox(QMessageBox.Icon.Question, "", question, buttons, self.window).exec() == QMessageBox.StandardButton.Yes

    def _ask_to_delete(self, question):
        """Enter deletes, Esc keeps: Delete is the default button, and has the focus."""
        box = QMessageBox(QMessageBox.Icon.Question, "", question, QMessageBox.StandardButton.NoButton, self.window)
        delete = box.addButton("Delete", QMessageBox.ButtonRole.DestructiveRole)
        box.setEscapeButton(box.addButton("Keep", QMessageBox.ButtonRole.RejectRole))
        box.setDefaultButton(delete)
        box.exec()
        return box.clickedButton() is delete

    def _show_and_settle(self):
        """macOS animates the switch to fullscreen; a modal opened mid-animation leaves the window at 100x30."""
        self.window.show()
        settling = QEventLoop()
        QTimer.singleShot(_FULLSCREEN_SETTLE_MS, settling.quit)
        settling.exec()
