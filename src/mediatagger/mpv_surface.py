import mpv
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QOpenGLContext
from PySide6.QtOpenGLWidgets import QOpenGLWidget


class MpvSurface(QOpenGLWidget):
    """Draws an mpv player's frames through libmpv's render API (the player must use vo=libmpv)."""

    frame_ready = Signal()

    def __init__(self, engine, parent=None, on_ready=lambda: None):
        """on_ready runs once the render context exists: a clip loaded before then played without its video."""
        super().__init__(parent)
        self.engine = engine
        self.on_ready = on_ready
        self.render_context = None
        self.frame_ready.connect(self.update, Qt.ConnectionType.QueuedConnection)

    def initializeGL(self):
        def get_proc_address(_, name):
            address = QOpenGLContext.currentContext().getProcAddress(name.decode())
            return int(address) if address else 0

        self._get_proc_address = mpv.MpvGlGetProcAddressFn(get_proc_address)
        self.render_context = mpv.MpvRenderContext(
            self.engine, "opengl", opengl_init_params={"get_proc_address": self._get_proc_address}
        )
        self.render_context.update_cb = self.frame_ready.emit
        self.on_ready()

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
