import ctypes

import mpv
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QOpenGLContext
from PySide6.QtOpenGLWidgets import QOpenGLWidget

_no_fence = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint)(lambda condition, flags: None)


def fence_free_lookup(lookup):
    """mpv's get_proc_address over lookup, but glFenceSync makes no fence: libmpv 0.40/0.41 leaks one per frame
    (mpv#17217, fixed upstream in f74adc4, unreleased); on the Pi each holds a file descriptor until the app dies.
    glFenceSync must still resolve — it is core in GLES 3 and mpv refuses to start without it."""

    def resolve(_, name):
        if name == b"glFenceSync":
            return ctypes.cast(_no_fence, ctypes.c_void_p).value
        return lookup(name.decode())

    return resolve


class MpvSurface(QOpenGLWidget):
    """Draws an mpv player's frames through libmpv's render API (the player must use vo=libmpv)."""

    frame_ready = Signal()

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.render_context = None
        self._ready = False
        self._pending = None
        self.frame_ready.connect(self.update, Qt.ConnectionType.QueuedConnection)

    def initializeGL(self):
        def real_address(name):
            address = QOpenGLContext.currentContext().getProcAddress(name)
            return int(address) if address else 0

        self._get_proc_address = mpv.MpvGlGetProcAddressFn(fence_free_lookup(real_address))
        self.render_context = mpv.MpvRenderContext(
            self.engine, "opengl", opengl_init_params={"get_proc_address": self._get_proc_address}
        )
        self.render_context.update_cb = self.frame_ready.emit
        self.became_ready()

    def when_ready(self, load):
        """Run load now if the surface can render, else once it can: mpv drops the video of a clip loaded earlier."""
        if self._ready:
            load()
        else:
            self._pending = load

    def cancel_pending(self):
        self._pending = None

    def became_ready(self):
        """The render context exists (initializeGL calls this; tests call it to stand in for a GL context)."""
        self._ready = True
        pending, self._pending = self._pending, None
        if pending:
            pending()

    def paintGL(self):
        if self.render_context is None:
            return
        ratio = self.devicePixelRatio()
        self.render_context.render(
            flip_y=True,
            opengl_fbo={
                "w": int(self.width() * ratio),
                "h": int(self.height() * ratio),
                "fbo": self.defaultFramebufferObject(),
            },
        )

    def release(self):
        """Free the render context; libmpv requires this before its player is terminated."""
        if self.render_context is None:
            return
        self.makeCurrent()
        self.render_context.free()
        self.render_context = None
        self.doneCurrent()
