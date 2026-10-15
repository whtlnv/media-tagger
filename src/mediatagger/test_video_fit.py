import ctypes
import sys
import time
from contextlib import contextmanager

import mpv
import pytest
from PySide6.QtCore import QPointF, QRect

from mediatagger.mpv_surface import fence_free_lookup
from mediatagger.test_video import make_clip, wait_until_playing
from mediatagger.video import VideoPlayer, new_engine
from mediatagger.zoom import Zoom, video_fitted

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="draws through a headless macOS OpenGL context")

GL_FRAMEBUFFER, GL_RENDERBUFFER, GL_COLOR_ATTACHMENT0, GL_RGBA8 = 0x8D40, 0x8D41, 0x8CE0, 0x8058
GL_RGBA, GL_UNSIGNED_BYTE = 0x1908, 0x1401
CGL_ACCELERATED, CGL_PROFILE, CGL_CORE_3_2 = 73, 99, 0x3200


@contextmanager
def headless_framebuffer(width, height):
    """A current OpenGL context drawing into a framebuffer of this size, with no window (the offscreen Qt platform
    has no OpenGL); yields the OpenGL library and the framebuffer's id."""
    gl = ctypes.CDLL("/System/Library/Frameworks/OpenGL.framework/OpenGL")
    attributes = (ctypes.c_int * 4)(CGL_ACCELERATED, CGL_PROFILE, CGL_CORE_3_2, 0)
    pixel_format, count, context = ctypes.c_void_p(), ctypes.c_int(), ctypes.c_void_p()
    assert gl.CGLChoosePixelFormat(attributes, ctypes.byref(pixel_format), ctypes.byref(count)) == 0
    assert gl.CGLCreateContext(pixel_format, None, ctypes.byref(context)) == 0
    gl.CGLSetCurrentContext(context)
    framebuffer, renderbuffer = ctypes.c_uint(), ctypes.c_uint()
    gl.glGenFramebuffers(1, ctypes.byref(framebuffer))
    gl.glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
    gl.glGenRenderbuffers(1, ctypes.byref(renderbuffer))
    gl.glBindRenderbuffer(GL_RENDERBUFFER, renderbuffer)
    gl.glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA8, width, height)
    gl.glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, renderbuffer)
    try:
        yield gl, framebuffer.value
    finally:
        gl.CGLSetCurrentContext(None)
        gl.CGLDestroyContext(context)
        gl.CGLDestroyPixelFormat(pixel_format)


@contextmanager
def player_drawing_into(width, height):
    """A silent player rendering through libmpv's OpenGL render API, as the viewer's surface does, and a function
    giving the bounding box (left, top, right, bottom) of what it draws that isn't black, or None."""
    with headless_framebuffer(width, height) as (gl, framebuffer):
        def address(name):
            try:
                return ctypes.cast(getattr(gl, name), ctypes.c_void_p).value or 0
            except AttributeError:
                return 0

        engine = new_engine(vo="libmpv", ao="null", vd_lavc_dr="no")
        get_proc_address = mpv.MpvGlGetProcAddressFn(fence_free_lookup(address))
        render_context = mpv.MpvRenderContext(engine, "opengl", opengl_init_params={"get_proc_address": get_proc_address})
        pixels = ctypes.create_string_buffer(width * height * 4)

        def drawn_box():
            render_context.render(flip_y=False, opengl_fbo={"w": width, "h": height, "fbo": framebuffer})
            gl.glFinish()
            gl.glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
            gl.glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, pixels)
            raw = pixels.raw
            lit = [(i // 4 % width, i // 4 // width) for i in range(0, len(raw), 4) if sum(raw[i:i + 3]) > 30]
            if not lit:
                return None
            xs, ys = [x for x, _ in lit], [y for _, y in lit]
            return min(xs), min(ys), max(xs), max(ys)

        try:
            yield VideoPlayer(engine), drawn_box
        finally:
            render_context.free()
            engine.terminate()


def settled_box(drawn_box, expected, timeout=3):
    """mpv applies a change to what it draws a frame or two later: keep drawing until the box is the expected one."""
    deadline = time.monotonic() + timeout
    box = drawn_box()
    while box != expected and time.monotonic() < deadline:
        time.sleep(0.05)
        box = drawn_box()
    return box


def test_an_unrotated_landscape_video_is_drawn_whole_across_the_full_width_of_a_square_surface(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4", duration=30)  # 64x48: on a 200x200 surface, 200x150 with 25 black above and below
    with player_drawing_into(200, 200) as (player, drawn_box):
        player.show(clip)
        wait_until_playing(player.engine)

        assert settled_box(drawn_box, (0, 25, 199, 174)) == (0, 25, 199, 174)


def test_a_landscape_video_turned_90_degrees_is_drawn_whole_across_the_full_height_of_a_square_surface(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4", duration=30)  # turned, 48x64: on a 200x200 surface, 150x200 with 25 black each side
    with player_drawing_into(200, 200) as (player, drawn_box):
        player.show(clip)
        wait_until_playing(player.engine)

        player.press("r")

        assert settled_box(drawn_box, (25, 0, 174, 199)) == (25, 0, 174, 199)


def test_zooming_in_on_a_playing_video_with_the_mouse_off_its_centre_keeps_the_video_point_under_the_mouse_under_the_mouse(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4", duration=30)  # 64x48: on a 300x150 surface, fitted 200x150 at x 50..249
    window = QRect(0, 0, 300, 150)
    with player_drawing_into(300, 150) as (player, drawn_box):
        player.show(clip)
        wait_until_playing(player.engine)
        assert settled_box(drawn_box, (50, 0, 249, 149)) == (50, 0, 249, 149)
        zoom = Zoom()

        zoom.wheel(120, QPointF(100, 75), video_fitted(player.engine, window), window)
        zoom.apply_to(player.engine)

        # 110 % about x 100: 220 wide from x 45, so the point 50 pixels in from the left edge stays at x 100
        assert settled_box(drawn_box, (45, 0, 264, 149)) == (45, 0, 264, 149)
