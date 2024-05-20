import moderngl
from moderngl_window import geometry
from OpenGL.GL import *

import outline_shaders

from pyrr import Matrix44

import numpy as np

class OutlineRenderer:
    def __init__(self, ctx: moderngl.Context, window_size):
        self.ctx = ctx
        self.window_size = window_size

        self.vaos = {}

        self.prog_unlit = ctx.program(
            vertex_shader=outline_shaders.UNLIT_VERT_SHADER,
            fragment_shader=outline_shaders.UNLIT_FRAG_SHADER
        )

        self.prog_blur = ctx.program(
            vertex_shader=outline_shaders.BLUR_VERT_SHADER,
            fragment_shader=outline_shaders.BLUR_FRAG_SHADER
        )

        self.pr_m_vp = self.prog_unlit['m_vp']
        self.pr_m_model = self.prog_unlit['m_model']
        self.pr_color = self.prog_unlit['color']

        self.prb_pixel_size = self.prog_blur['pixelSize']

        self.offscreen_texture = self.ctx.texture(self.window_size, 4)
        self.offscreen_texture.repeat_x = False
        self.offscreen_texture.repeat_y = False
        self.offscreen = self.ctx.framebuffer(
            color_attachments=[self.offscreen_texture],
        )
        self.quad = geometry.quad_2d(size=(1.0, 1.0), pos=(0.5, 0.5))

    def write_mats(self, m_vp: Matrix44, m_model: Matrix44):
        self.pr_m_vp.write(m_vp.astype('f4'))
        self.pr_m_model.write(m_model.astype('f4'))

    def load_vao(self, model_name, model):
        self.vaos[model_name] = model.root_nodes[0].mesh.vao.instance(self.prog_unlit)

    def use_framebuf(self):
        self.offscreen.use()

    def clear(self):
        self.offscreen.clear()

    def render_quad(self):

        self.prb_pixel_size.write((1 / np.array(self.window_size)).astype('f4'))

        # Use additive blending, this way darker outlines are dimmer and don't actually darken
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        # No depth
        glDisable(GL_DEPTH_TEST)

        self.write_mats(Matrix44.identity(), Matrix44.identity())
        self.offscreen_texture.use()
        self.quad.render(self.prog_blur)