"""Third Pi diagnostic: mpv-in-QOpenGLWidget alone doesn't leak; which app ingredient makes it leak? Run via diag-video3.sh."""
import os, sys, time, locale
variant, clip = sys.argv[1], sys.argv[2]
def sync_files():
    n = 0
    for fd in os.listdir("/proc/self/fd"):
        try: n += os.readlink(f"/proc/self/fd/{fd}") == "anon_inode:sync_file"
        except OSError: pass
    return n
start = time.time()
def report(): print(f"  t={time.time()-start:4.0f}s sync_files={sync_files()}", flush=True)

import mpv
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QOpenGLContext
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QStackedWidget, QVBoxLayout
from PySide6.QtOpenGLWidgets import QOpenGLWidget
app = QApplication(sys.argv[:1])
locale.setlocale(locale.LC_NUMERIC, "C")
for s in (5, 10, 15, 20, 25): QTimer.singleShot(s * 1000, report)
QTimer.singleShot(26000, app.quit)

fullscreen = "fullscreen" in variant
overlay = "overlay" in variant
sound = "sound" in variant
player = mpv.MPV(vo="libmpv", loop_file="inf", **({} if sound else {"ao": "null"}))
holder = {}
class Surface(QOpenGLWidget):
    def initializeGL(self):
        get = mpv.MpvGlGetProcAddressFn(lambda _, name: int(QOpenGLContext.currentContext().getProcAddress(name.decode()) or 0))
        holder["get"] = get
        holder["ctx"] = mpv.MpvRenderContext(player, "opengl", opengl_init_params={"get_proc_address": get})
        holder["ctx"].update_cb = lambda: QTimer.singleShot(0, self.update)
    def paintGL(self):
        r = self.devicePixelRatio()
        holder["ctx"].render(flip_y=True, opengl_fbo={"w": int(self.width() * r), "h": int(self.height() * r), "fbo": self.defaultFramebufferObject()})

top = QWidget(); top.resize(800, 450)
layout = QVBoxLayout(top); layout.setContentsMargins(0, 0, 0, 0)
stack = QStackedWidget(); layout.addWidget(stack)
page = QWidget(); stack.addWidget(page)
surface = Surface(page)
def place(): surface.setGeometry(page.rect())
page.resizeEvent = lambda e: place()
if overlay:  # translucent labels over the video, like the app's status bar and tag overlay
    for i, text in enumerate(("Library: MEDIATAGGER", "beach family")):
        label = QLabel(text, top)
        label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 160); padding: 8px 12px; border-radius: 6px; font-size: 18px;")
        label.adjustSize(); label.move(16 + i * 260, 16); label.raise_(); label.show()
if fullscreen: top.setWindowState(Qt.WindowState.WindowFullScreen)
top.show()
QTimer.singleShot(500, lambda: player.play(clip))
app.exec()
