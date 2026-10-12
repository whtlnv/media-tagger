import ctypes
import gc

from mediatagger import mpv_surface
from mediatagger.mpv_surface import MpvSurface, fence_free_lookup

GL_SYNC_GPU_COMMANDS_COMPLETE = 0x9117
FENCE_SYNC = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint)


def test_glfencesync_resolves_to_a_stand_in_that_returns_no_fence():
    lookup = fence_free_lookup(lambda name: 0x1234)

    address = lookup(None, b"glFenceSync")

    assert address
    assert FENCE_SYNC(address)(GL_SYNC_GPU_COMMANDS_COMPLETE, 0) is None


def test_any_other_gl_function_resolves_to_the_address_the_real_context_reports():
    lookup = fence_free_lookup({"glClear": 0x5678}.get)

    assert lookup(None, b"glClear") == 0x5678


def test_the_glfencesync_stand_in_is_still_callable_after_a_garbage_collection():
    lookup = fence_free_lookup(lambda name: 0x1234)
    address = lookup(None, b"glFenceSync")

    gc.collect()

    assert FENCE_SYNC(address)(GL_SYNC_GPU_COMMANDS_COMPLETE, 0) is None


def test_the_surface_hands_mpv_the_fence_free_gl_lookup_when_it_creates_its_render_context(qtbot, monkeypatch):
    real_addresses = {"glFenceSync": 0x1111, "glClear": 0x5678}

    class GlContext:
        @staticmethod
        def currentContext():
            return GlContext()

        def getProcAddress(self, name):
            return real_addresses.get(name, 0)

    received = {}

    class RenderContext:
        def __init__(self, engine, api_type, opengl_init_params):
            received.update(opengl_init_params)

    monkeypatch.setattr(mpv_surface, "QOpenGLContext", GlContext)
    monkeypatch.setattr(mpv_surface.mpv, "MpvRenderContext", RenderContext)
    surface = MpvSurface(engine=None)
    qtbot.addWidget(surface)

    surface.initializeGL()

    get_proc_address = received["get_proc_address"]
    fence_sync = get_proc_address(None, b"glFenceSync")
    assert fence_sync != 0x1111
    assert FENCE_SYNC(fence_sync)(GL_SYNC_GPU_COMMANDS_COMPLETE, 0) is None
    assert get_proc_address(None, b"glClear") == 0x5678
