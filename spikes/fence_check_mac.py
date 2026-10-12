"""fence_check.py <with-fix|without-fix> <clip>: mpv render API in a QOpenGLWidget redrawn per frame (like the app);
counts frames drawn and GL fences mpv creates, and sync_file fds."""
import ctypes, os, sys, time, locale
fix, clip = sys.argv[1] == "with-fix", sys.argv[2]
import mpv
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QOpenGLContext
from PySide6.QtWidgets import QApplication
from PySide6.QtOpenGLWidgets import QOpenGLWidget
app = QApplication(sys.argv[:1]); locale.setlocale(locale.LC_NUMERIC, "C")
player = mpv.MPV(vo="libmpv", loop_file="inf", ao="null", **({"vd_lavc_dr": "no"} if fix else {}))
counts = {"paints": 0, "fences": 0}
FENCE = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint)
real = {}
DELETE = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
counts["deleted"] = 0; counts["created"] = 0
def counting_fence(cond, flags):
    counts["fences"] += 1
    if fix: return None
    counts["created"] += 1
    return real["fn"](cond, flags)
def counting_delete(sync):
    if sync: counts["deleted"] += 1
    real["del"](sync)
fake = FENCE(counting_fence); fake_delete = DELETE(counting_delete)
def sync_files():
    n = 0
    for fd in os.listdir("/dev/fd"):
        try: n += False
        except OSError: pass
    return n
class Surface(QOpenGLWidget):
    frame_ready = Signal()
    def __init__(self):
        super().__init__(); self.frame_ready.connect(self.update, Qt.ConnectionType.QueuedConnection)
    def initializeGL(self):
        def get(_, name):
            address = int(QOpenGLContext.currentContext().getProcAddress(name.decode()) or 0)
            if name == b"glFenceSync" and address:
                real["fn"] = FENCE(address)
                return ctypes.cast(fake, ctypes.c_void_p).value
            if name == b"glDeleteSync" and address:
                real["del"] = DELETE(address)
                return ctypes.cast(fake_delete, ctypes.c_void_p).value
            return address
        self._get = mpv.MpvGlGetProcAddressFn(get)
        self.ctx = mpv.MpvRenderContext(player, "opengl", opengl_init_params={"get_proc_address": self._get})
        self.ctx.update_cb = self.frame_ready.emit
    def paintGL(self):
        counts["paints"] += 1
        r = self.devicePixelRatio()
        self.ctx.render(flip_y=True, opengl_fbo={"w": int(self.width() * r), "h": int(self.height() * r), "fbo": self.defaultFramebufferObject()})
w = Surface(); w.resize(640, 360); w.show()
start = time.time()
def report(): print(f"  {'with' if fix else 'without'}-fix t={time.time()-start:3.0f}s frames={counts['paints']} fence_calls={counts['fences']} live_fences={counts['created']-counts['deleted']} pos={player.time_pos}", flush=True)
for s in (5, 10, 15): QTimer.singleShot(s * 1000, report)
QTimer.singleShot(15500, app.quit)
QTimer.singleShot(300, lambda: player.play(clip))
app.exec()
w.ctx.free(); player.terminate()
