"""Second Pi diagnostic: which piece leaks one sync_file per frame? Run via diag-video2.sh, not directly."""
import os, sys, time, locale
variant, clip = sys.argv[1], sys.argv[2]

def sync_files():
    n = 0
    for fd in os.listdir("/proc/self/fd"):
        try:
            n += os.readlink(f"/proc/self/fd/{fd}") == "anon_inode:sync_file"
        except OSError:
            pass
    return n

start = time.time()
def report(done=False):
    print(f"  t={time.time()-start:4.0f}s sync_files={sync_files()}", flush=True)

if variant == "mpv-standalone":  # mpv's own window and GL, no Qt at all
    import mpv
    locale.setlocale(locale.LC_NUMERIC, "C")
    player = mpv.MPV(vo="gpu", loop_file="inf", ao="null")
    player.play(clip)
    for _ in range(5):
        time.sleep(5); report()
    player.terminate(); sys.exit(0)

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QOpenGLContext, QGuiApplication
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtOpenGL import QOpenGLWindow
app = QApplication(sys.argv[:1])
for s in (5, 10, 15, 20, 25):
    QTimer.singleShot(s * 1000, report)
QTimer.singleShot(26000, app.quit)

def gl_clear(ctx, r):
    f = ctx.functions(); f.glClearColor(r, 0.2, 0.4, 1.0); f.glClear(0x4000)

if variant in ("qt-widget-only", "qt-window-only"):  # Qt's GL path, redrawn every frame, no mpv
    frame = [0]
    if variant == "qt-widget-only":
        class W(QOpenGLWidget):
            def paintGL(self):
                frame[0] += 1; gl_clear(self.context(), (frame[0] % 60) / 60)
        w = W(); w.resize(800, 450); w.show()
    else:
        class W(QOpenGLWindow):
            def paintGL(self):
                frame[0] += 1; gl_clear(self.context(), (frame[0] % 60) / 60)
        w = W(); w.resize(800, 450); w.show()
    t = QTimer(); t.timeout.connect(w.update); t.start(33)
    app.exec(); sys.exit(0)

import mpv
locale.setlocale(locale.LC_NUMERIC, "C")

if variant == "mpv-wid-xcb":  # mpv draws into a native X11 child window (run with QT_QPA_PLATFORM=xcb)
    w = QWidget(); w.resize(800, 450); w.setAttribute(Qt.WidgetAttribute.WA_NativeWindow); w.show()
    player = mpv.MPV(wid=str(int(w.winId())), vo="gpu", loop_file="inf", ao="null")
    player.play(clip)
    app.exec(); player.terminate(); sys.exit(0)

# mpv's render API inside Qt: as the app does it (widget), or in a QOpenGLWindow
player = mpv.MPV(vo="libmpv", loop_file="inf", ao="null")
holder = {}
def make_ctx():
    get = mpv.MpvGlGetProcAddressFn(lambda _, name: int(QOpenGLContext.currentContext().getProcAddress(name.decode()) or 0))
    holder["get"] = get
    holder["ctx"] = mpv.MpvRenderContext(player, "opengl", opengl_init_params={"get_proc_address": get})
def render(widget, fbo):
    r = widget.devicePixelRatio()
    holder["ctx"].render(flip_y=True, opengl_fbo={"w": int(widget.width() * r), "h": int(widget.height() * r), "fbo": fbo})
if variant == "mpv-in-qt-widget":
    class W(QOpenGLWidget):
        def initializeGL(self):
            make_ctx(); holder["ctx"].update_cb = lambda: QTimer.singleShot(0, self.update)
        def paintGL(self): render(self, self.defaultFramebufferObject())
else:  # mpv-in-qt-window
    class W(QOpenGLWindow):
        def initializeGL(self):
            make_ctx(); holder["ctx"].update_cb = lambda: QTimer.singleShot(0, self.update)
        def paintGL(self): render(self, self.defaultFramebufferObject())
w = W(); w.resize(800, 450); w.show()
QTimer.singleShot(500, lambda: player.play(clip))
app.exec()
