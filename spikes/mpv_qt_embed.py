"""Spike: play videos through libmpv inside a Qt window (render API + QOpenGLWidget).

Interactive:  uv run python spikes/mpv_qt_embed.py FILE...   (Space = next, Esc = quit)
Self-check:   uv run python spikes/mpv_qt_embed.py --check FILE...
              Plays each file for a few seconds and reports whether playback
              advanced and whether the widget actually shows non-black pixels.
"""

import locale
import sys

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QOpenGLContext
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QApplication

import mpv


class MpvWidget(QOpenGLWidget):
    frame_ready = Signal()

    def __init__(self):
        super().__init__()
        self.player = mpv.MPV(vo="libmpv", hwdec="auto-safe", loop_file="inf", keep_open="yes")
        self.render_ctx = None
        self.frame_ready.connect(self.update, Qt.QueuedConnection)

    def initializeGL(self):
        def get_proc_address(_, name):
            address = QOpenGLContext.currentContext().getProcAddress(name.decode())
            return int(address) if address else 0

        self._proc_fn = mpv.MpvGlGetProcAddressFn(get_proc_address)
        self.render_ctx = mpv.MpvRenderContext(
            self.player, "opengl", opengl_init_params={"get_proc_address": self._proc_fn}
        )
        self.render_ctx.update_cb = self.frame_ready.emit

    def paintGL(self):
        if self.render_ctx is None:
            return
        ratio = self.devicePixelRatio()
        self.render_ctx.render(
            flip_y=True,
            opengl_fbo={
                "w": int(self.width() * ratio),
                "h": int(self.height() * ratio),
                "fbo": self.defaultFramebufferObject(),
            },
        )

    def play(self, path):
        self.player.play(path)

    def shutdown(self):
        self.makeCurrent()
        if self.render_ctx is not None:
            self.render_ctx.free()
            self.render_ctx = None
        self.doneCurrent()
        self.player.terminate()


class Viewer(MpvWidget):
    def __init__(self, files, check):
        super().__init__()
        self.files = files
        self.index = 0
        self.check = check
        self.results = []

    def start(self):
        self.play(self.files[0])
        if self.check:
            QTimer.singleShot(3000, self.record_and_advance)

    def next_file(self):
        self.index += 1
        if self.index >= len(self.files):
            self.close()
            return
        self.play(self.files[self.index])
        if self.check:
            QTimer.singleShot(3000, self.record_and_advance)

    def record_and_advance(self):
        image = self.grabFramebuffer()
        centre = image.pixelColor(image.width() // 2, image.height() // 2)
        non_black = sum(
            1
            for x in range(0, image.width(), 20)
            for y in range(0, image.height(), 20)
            if image.pixelColor(x, y).lightness() > 16
        )
        self.results.append(
            {
                "file": self.files[self.index].rsplit("/", 1)[-1],
                "time_pos": round(self.player.time_pos or 0, 2),
                "codec": self.player.video_codec,
                "hwdec": self.player.hwdec_current,
                "non_black_samples": non_black,
                "centre": centre.name(),
            }
        )
        self.next_file()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.next_file()
        elif event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.shutdown()
        super().closeEvent(event)


def main():
    args = sys.argv[1:]
    check = "--check" in args
    files = [a for a in args if a != "--check"]
    if not files:
        sys.exit(__doc__)

    app = QApplication(sys.argv)
    locale.setlocale(locale.LC_NUMERIC, "C")  # libmpv refuses to start under a non-C numeric locale
    viewer = Viewer(files, check)
    viewer.resize(960, 540)
    viewer.show()
    QTimer.singleShot(0, viewer.start)
    app.exec()

    for result in viewer.results:
        ok = result["time_pos"] > 0.5 and result["non_black_samples"] > 50
        print(("PASS " if ok else "FAIL ") + str(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
