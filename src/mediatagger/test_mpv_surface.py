import ctypes

from mediatagger.mpv_surface import fence_free_lookup

GL_SYNC_GPU_COMMANDS_COMPLETE = 0x9117
FENCE_SYNC = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint)


def test_glfencesync_resolves_to_a_stand_in_that_returns_no_fence():
    lookup = fence_free_lookup(lambda name: 0x1234)

    address = lookup(None, b"glFenceSync")

    assert address
    assert FENCE_SYNC(address)(GL_SYNC_GPU_COMMANDS_COMPLETE, 0) is None
