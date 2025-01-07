import os
import math
import random
import threading
import sys 
import argparse
import copy
import struct

from const import *
from shaders import *
from arena_shaders import *
from socket_listener import SocketListener
from state_manager import *
from ribbon import *
from outline_renderer import OutlineRenderer
import ui
from ui import get_ui, QUIBarWidget, QRSVWindow
from config import Config, ConfigVal

import moderngl
import moderngl_window
import moderngl_window.loaders.scene.wavefront as wvf
from moderngl_window import resources
from moderngl_window.meta import TextureDescription

from PyQt5 import QtOpenGL, QtWidgets
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QScreen, QColor

from OpenGL.GL import *
from OpenGL.GLU import *

import numpy as np

from pyrr import Quaternion, Matrix33, Matrix44, Vector3, Vector4

import pywavefront

# TODO: Move
def safe_normalize(vec: pyrr.Vector3):
    length = max(vec.length, 1e-6)
    return vec / length

# TODO: Move game logic out of here
class QRSVGLWidget(QtOpenGL.QGLWidget):
    def __init__(self, screen: QScreen):

        self.config = Config()

        self.spectate_count = 0
        self.spectate_idx = 0
        self.prev_interp_ratio = 0
        self.car_cam_time = 0
        self.last_render_time = time.time()
        self.fps_counter = 0
        self.last_fps = 0
        self.prev_state = None # type: GameState

        ########################################################################

        self.samples = 4

        fmt = QtOpenGL.QGLFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QtOpenGL.QGLFormat.CoreProfile)
        fmt.setDepthBufferSize(24)
        fmt.setStencilBufferSize(8)
        fmt.setDoubleBuffer(True)
        fmt.setSwapInterval(1)

        if self.samples > 1:
            fmt.setSampleBuffers(True)
            fmt.setSamples(int(self.samples))

        super(QRSVGLWidget, self).__init__(fmt, None)

        self.setMouseTracking(True)

    def load_texture_2d(self, path: str) -> moderngl.Texture:
        return resources.textures.load(TextureDescription(path=path))

    def initializeGL(self):

        self.ctx = moderngl.create_context()
        moderngl_window.activate_context(None, self.ctx)

        ##########################################

        print("Creating shader programs...")

        self.prog = self.ctx.program(
            vertex_shader=VERT_SHADER,
            fragment_shader=FRAG_SHADER,
        )

        self.prog_arena = self.ctx.program(
            vertex_shader=ARENA_VERT_SHADER,
            fragment_shader=ARENA_FRAG_SHADER,
            geometry_shader=ARENA_GEOM_SHADER
        )

        print("Creating outline renderer...")
        #self.outline_renderer = OutlineRenderer(self.ctx, (self.width(), self.height())) # TODO: Fix resizing bugs
        self.outline_renderer = None # Disabled due to weird shader compilation issues

        print("Linking shader varaibles...")
        self.pr_m_vp = self.prog['m_vp']
        self.pr_m_model = self.prog['m_model']
        self.pr_global_color = self.prog['globalColor']
        self.pr_camera_pos = self.prog['cameraPos']

        self.pra_m_vp = self.prog_arena['m_vp']
        self.pra_m_model = self.prog_arena['m_model']
        self.pra_ball_pos = self.prog_arena['ballPos']

        ##########################################

        self.ball_ribbon = RibbonEmitter()
        self.car_ribbons = []

        print("Data path:", DATA_DIR_PATH)
        print("Loading models and textures...")

        self.vaos = {}
        self.load_vao("ArenaMeshCustom.obj", self.prog_arena)

        self.load_vao("Octane.obj")
        self.load_vao("Ball.obj")

        self.load_vao("BoostPad_Small_0.obj")
        self.load_vao("BoostPad_Small_1.obj")
        self.load_vao("BoostPad_Big_0.obj")
        self.load_vao("BoostPad_Big_1.obj")

        self.ts_octane = [
            self.load_texture_2d(DATA_DIR_PATH + "T_Octane_B.png"),
            self.load_texture_2d(DATA_DIR_PATH + "T_Octane_O.png")
        ]
        self.t_ball = self.load_texture_2d(DATA_DIR_PATH + "T_Ball.png")
        self.t_boostpad = self.load_texture_2d(DATA_DIR_PATH + "T_BoostPad.png")
        self.t_boost_glow = self.load_texture_2d(DATA_DIR_PATH + "T_Boost_Glow.png")
        self.t_black = self.load_texture_2d(DATA_DIR_PATH + "T_Black.png")
        self.t_none = self.load_texture_2d(DATA_DIR_PATH + "T_None.png")

        ############################################

        # Make ribbon mesh
        self.ribbon_max_verts = 1000
        self.ribbon_verts = np.random.randn(self.ribbon_max_verts * 3) * 100
        self.ribbon_vbo = self.ctx.buffer(self.ribbon_verts.astype('f4'))
        self.ribbon_vao = self.ctx.simple_vertex_array(self.prog, self.ribbon_vbo, "in_position")
        self.vaos['ribbon'] = self.ribbon_vao

        # Make debug lines mesh
        self.lines_max_verts = RenderState.MAX_LINES * 2
        self.lines_verts = np.random.randn(self.lines_max_verts * 3) * 100
        self.lines_vbo = self.ctx.buffer(self.lines_verts.astype('f4'))
        self.lines_vao = self.ctx.simple_vertex_array(self.prog, self.lines_vbo, "in_position")
        self.vaos['render_lines'] = self.lines_vao

        ############################################

        # Auto-enable multisampling if we have multiple samples
        self.ctx.multisample = self.samples > 1

        ############################################

        print("Done.")

    def load_vao(self, model_name, program = None):
        loader = wvf.Loader(wvf.SceneDescription(path = DATA_DIR_PATH + "/" + model_name))
        model = loader.load()
        self.vaos[model_name] = model.root_nodes[0].mesh.vao.instance(self.prog if (program is None) else program)
        if not (self.outline_renderer is None):
            self.outline_renderer.load_vao(model_name, model)

    def render_model(self,
                     pos, forward, up,
                     model_name, texture, scale = 1.0, global_color = None,
                     mode = moderngl.TRIANGLES, outline_color: Vector3 = None, vert_amount = None):

        if pos is None:
            model_mat = Matrix44.identity()
        else:
            pos = Vector3(pos)
            forward = Vector3(forward)
            up = Vector3(up)
            right = Vector3(pyrr.vector3.cross(forward, up))

            forward *= scale
            right *= scale
            up *= scale

            model_mat = Matrix44([
                forward[0], forward[1], forward[2], 0,
                -right[0], -right[1], -right[2], 0,
                up[0], up[1], up[2], 0,
                pos[0], pos[1], pos[2], 1
            ])

        self.pr_m_model.write(model_mat.astype('f4'))
        self.pra_m_model.write(model_mat.astype('f4'))

        if global_color is None:
            global_color = Vector4((0, 0, 0, 0))
        self.pr_global_color.write(global_color.astype('f4'))

        if texture is not None:
            texture.use()
        else:
            self.t_none.use()

        self.ctx.screen.use()
        self.vaos[model_name].render(mode, vertices=(-1 if (vert_amount is None) else vert_amount))

        if outline_color is not None:
            self.outline_renderer.use_framebuf()
            self.outline_renderer.pr_m_model.write(model_mat.astype('f4'))
            self.outline_renderer.pr_color.write(Vector4((outline_color.x, outline_color.y, outline_color.z, 1)).astype('f4'))
            self.outline_renderer.vaos[model_name].render(mode)

    def render_ribbon(self, ribbon: RibbonEmitter, camera_pos, lifetime, width, start_taper_time, color):
        if len(ribbon.points) == 0:
            return

        vertices = []

        first_point = ribbon.points[0]
        cam_to_ribbon_dir = safe_normalize(-(first_point.pos - camera_pos))
        ribbon_away_dir = safe_normalize(first_point.vel)
        ribbon_sideways_dir = ribbon_away_dir.cross(cam_to_ribbon_dir)

        for point in ribbon.points: # type: RibbonPoint
            if not point.connected:
                continue

            if point.time_active < start_taper_time:
                width_scale = point.time_active / start_taper_time
            else:
                width_scale = 1 - (point.time_active / lifetime)

            offset = ribbon_sideways_dir * width * width_scale
            for i in range(2):
                offset_scale = 1 if (i == 1) else -1
                vertex_pos = point.pos + (offset * offset_scale)
                if len(vertices) < self.ribbon_max_verts:
                    vertices.append(vertex_pos)
                else:
                    break

        if len(vertices) > 0:
            while len(vertices) < self.ribbon_max_verts:
                vertices.append(vertices[-1])
        else:
            return

        self.ribbon_vbo.write(np.array(vertices).astype('f4'), 0)

        glDisable(GL_CULL_FACE)
        self.render_model(
            None, None, None,
            "ribbon", self.t_none, scale=20,
            global_color=color,
            mode=moderngl.TRIANGLE_STRIP
        )
        glEnable(GL_CULL_FACE)

    def calc_camera_state(self, state, interp_ratio, delta_time):
        pos = Vector3((-4000, 0, 1000))
        ball_pos = state.ball_state.get_pos(interp_ratio)

        cam_dir = safe_normalize(ball_pos - pos)

        is_spectating_car = self.spectate_idx > -1 and len(state.car_states) > self.spectate_idx
        if is_spectating_car:
            car_pos = state.car_states[self.spectate_idx].phys.get_pos(interp_ratio)
            car_vel = state.car_states[self.spectate_idx].phys.get_vel(interp_ratio)
            car_forward = state.car_states[self.spectate_idx].phys.get_forward(interp_ratio)

            # Calculate ball cam
            if True:
                height = self.config.camera_height.val
                dist = self.config.camera_distance.val

                ball_cam_offset_dir = safe_normalize(safe_normalize(ball_pos - car_pos) * Vector3((1, 1, 0))).normalized

                # As we tilt up, move the camera down
                lean_scale = safe_normalize(ball_pos - car_pos).z
                height_clamp = abs(ball_pos.z - car_pos.z) / self.config.camera_lean_min_height_clamp.val
                if lean_scale > 0:
                    height *= 1 - min(lean_scale * self.config.camera_lean_height_scale.val, height_clamp)

                    # As we tilt up, move the camera closer
                    dist *= 1 - lean_scale * self.config.camera_lean_dist_scale.val

                ball_cam_offset = -ball_cam_offset_dir * dist
                ball_cam_offset.z += height

                # Make sure we are actually of the correct distance
                ball_cam_offset = safe_normalize(ball_cam_offset) * dist
                ball_cam_pos = car_pos + ball_cam_offset
                ball_cam_dir = safe_normalize(ball_pos - ball_cam_pos)

            # Calculate car cam dir
            if True:
                if car_vel.length > 0:
                    car_cam_dir = safe_normalize(car_vel * Vector3((1, 1, 0)))
                else:
                    car_cam_dir = (car_forward * Vector3((1, 1, 0)))
                    if car_cam_dir.length > 0:
                        car_cam_dir = safe_normalize(car_cam_dir)
                    else:
                        car_cam_dir = Vector3((1, 1, 0))
                car_cam_offset = -car_cam_dir * self.config.camera_distance.val
                car_cam_offset.z = self.config.camera_height.val
                car_cam_pos = car_pos + car_cam_offset

            # Determine if dribbling
            car_ball_delta = ball_pos - car_pos
            dribbling = False
            if car_vel.length > 500:
                if 90 < car_ball_delta.z < 200:
                    if (car_ball_delta * Vector3((1, 1, 0))).length < 135:
                        if ball_pos.z < 300:
                            dribbling = True

            car_cam_start_delay = 0.25
            car_cam_max_time = 0.65
            car_cam_inc_speed = 0.8
            car_cam_dec_speed = 0.5
            if car_ball_delta.length > 1000:
                car_cam_dec_speed *= 2 # Speed up when ball moved away quickly

            if dribbling:
                self.car_cam_time += car_cam_inc_speed * delta_time
            else:
                self.car_cam_time = min(self.car_cam_time, car_cam_max_time)
                self.car_cam_time = max(0, self.car_cam_time - car_cam_dec_speed * delta_time)

            # TODO: Auto car-cam is annoying, activates at bad times
            car_cam_ratio = np.clip((self.car_cam_time - car_cam_start_delay) / (car_cam_max_time - car_cam_start_delay), 0, 1)

            pos = ball_cam_pos*(1-car_cam_ratio) + car_cam_pos*car_cam_ratio
            cam_dir = safe_normalize(ball_cam_dir*(1-car_cam_ratio) + car_cam_dir*car_cam_ratio)
        else:
            self.car_cam_time = 0

        return pos, pos + cam_dir, (self.config.camera_fov.val if is_spectating_car else self.config.camera_bird_fov.val)

    def paintGL(self):
        width, height = self.width(), self.height()
        self.ctx.viewport = (0, 0, width, height)

        cur_time = time.time()
        delta_time = cur_time - self.last_render_time
        self.render(cur_time, delta_time, width, height)

        self.fps_counter += 1

        if int(cur_time) > int(self.last_render_time):
            self.last_fps = self.fps_counter
            self.fps_counter = 2

        self.last_render_time = cur_time

        self.update()

    def render(self, total_time, delta_time, width, height):
        with global_state_mutex:
            if not global_state_manager.state.ball_state.has_rot:
                global_state_manager.state.ball_state.rotate_with_ang_vel(delta_time)

            state = copy.deepcopy(global_state_manager.state)
        self.prev_state = state
        self.spectate_count = len(state.car_states)

        while len(self.car_ribbons) != len(state.car_states):
            if len(self.car_ribbons) < len(state.car_states):
                self.car_ribbons.append(RibbonEmitter())
            else:
                self.car_ribbons.pop()

        cur_time = time.time()
        interp_interval = max(state.recv_interval, 1e-6)
        interp_ratio = min(max((cur_time - state.recv_time) / interp_interval, 0), 1)

        if not (self.outline_renderer is None):
            self.outline_renderer.clear()

        self.ctx.clear(0, 0, 0)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)

        self.ctx.cull_face = "back"
        self.ctx.front_face = "cw"
        self.ctx.enable(moderngl.CULL_FACE)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA) # Normal blending
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR) # Use linear interpolation of pixels for supersampling

        camera_pos, camera_target_pos, camera_fov = self.calc_camera_state(state, interp_ratio, delta_time)
        proj = Matrix44.perspective_projection(camera_fov, -width/height, 0.1, 50 * 1000.0)
        lookat = Matrix44.look_at(
            camera_pos,
            camera_target_pos,
            (0.0, 0.0, 1.0),
        )

        self.pr_camera_pos.write(camera_pos.astype('f4'))
        self.pr_m_vp.write((proj * lookat).astype('f4'))
        self.pra_m_vp.write((proj * lookat).astype('f4'))
        if not (self.outline_renderer is None):
            self.outline_renderer.pr_m_vp.write((proj * lookat).astype('f4'))

        if not (state.boost_pad_states is None) and state.gamemode != "heatseeker": # Render boost pads
            for i in range(len(state.boost_pad_states)):
                is_big = state.is_boost_big(i)

                is_active = state.boost_pad_states[i]

                pos = state.boost_pad_locations[i].copy()
                pos.z = 0

                model_name = "BoostPad"
                model_name += "_Big_" if is_big else "_Small_"
                model_name += "1" if is_active else "0"
                model_name += ".obj"

                self.render_model(
                    pos, Vector3((1, 0, 0)), Vector3((0, 0, 1)),
                    model_name,
                    self.t_boostpad,
                    scale=2.5,
                )

        if True: # Render ball
            ball_phys = state.ball_state
            ball_pos = ball_phys.get_pos(interp_ratio)
            self.render_model(
                ball_pos,
                ball_phys.get_forward(interp_ratio), ball_phys.get_up(interp_ratio), 'Ball.obj', self.t_ball,

                #outline_color = Vector4((1, 1, 1, 1))
            )

            if state.gamemode == "heatseeker": # Update and render ball ribbon
                ball_speed = ball_phys.get_vel(interp_ratio).length
                speed_frac = (max(0, min(1, ball_speed / 2800)) ** 2)
                ribbon_alpha = 0.75
                ribbon_lifetime = 0.8

                self.ball_ribbon.update(
                    ball_speed > 600,
                    0,
                    ball_pos,
                    Vector3((100,0,0)),
                    ribbon_lifetime,
                    delta_time
                )

                if ball_phys.is_teleporting():
                    self.ball_ribbon.points.clear()

                self.render_ribbon(
                    self.ball_ribbon,
                    camera_pos,
                    ribbon_lifetime,
                    width=50,
                    start_taper_time=ribbon_lifetime / 10,
                    color=Vector4((1, 1, 1, ribbon_alpha))
                )

        if True: # Render cars
            for i in range(len(state.car_states)):
                car_state = state.car_states[i]
                if car_state.is_demoed:
                    continue

                car_ribbon = self.car_ribbons[i]

                car_pos = car_state.phys.get_pos(interp_ratio)
                car_forward = car_state.phys.get_forward(interp_ratio)
                car_up = car_state.phys.get_up(interp_ratio)
                outline_brightness = 1 - (1 / (1 + (car_pos - camera_pos).length / 1000))
                self.render_model(
                    car_pos, car_forward, car_up,
                    model_name='Octane.obj', texture=self.ts_octane[car_state.team_num],

                    #outline_color = (Vector3((0, 0.5, 1)) if (car_state.team_num == 0) else Vector3((1, 0.5, 0))) * outline_brightness
                )

                if True: # Update and render car ribbon
                    RIBBON_LIFETIME = 0.3
                    ribbon_emit_pos = car_pos - (car_forward * 40) + (car_up * 10)
                    ribbon_vel = car_forward * -100
                    car_ribbon.update(
                        car_state.is_boosting,
                        0,
                        ribbon_emit_pos,
                        ribbon_vel,
                        RIBBON_LIFETIME,
                        delta_time
                    )

                    if car_state.phys.is_teleporting():
                        car_ribbon.points.clear()

                    self.render_ribbon(
                        car_ribbon,
                        camera_pos,
                        RIBBON_LIFETIME,
                        20,
                        RIBBON_LIFETIME / 10,
                        Vector4((1, 0.9, 0.4, 1))
                    )

        ###########################################

        self.pra_ball_pos.write(state.ball_state.get_pos(interp_ratio).astype('f4'))
        self.render_model(
            None, None, None,
            model_name='ArenaMeshCustom.obj', texture=self.t_none, scale=1, global_color=Vector4((1,1,1,1))
        )

        if not (self.outline_renderer is None):
            self.outline_renderer.render_quad()

        ###########################################

        if len(state.render_state.lines) > 0:

            vertices_flat = np.array(state.render_state.lines).flatten()
            num_verts = vertices_flat.shape[0] // 3

            # TODO: Manual construction of VBO and VAO every frame is very inefficient
            # Instead, maybe keep a buffer of the max number of vertices and do a partial render from the occupied regions
            self.lines_vbo.write(vertices_flat.astype('f4'))

            self.ctx.disable(moderngl.DEPTH_TEST)

            self.render_model(
                None, None, None,
                "render_lines", self.t_boost_glow, 1, Vector4((1, 1, 1, 1)),
                mode=GL_LINES,
                vert_amount=num_verts
            )
            self.ctx.enable(moderngl.DEPTH_TEST)

        ###########################################

        ui_text = ""
        ui_text += "Render FPS: {}".format(self.last_fps) + "\n"
        ui_text += "Connected: {}".format(state.recv_time > 0) + "\n"
        if state.recv_interval > 0:
            ui_text += "Network rate: {:.2f}fps".format(1 / state.recv_interval) + "\n"
        ui_text += "Ball speed: {:.2f}kph".format(state.ball_state.prev_vel.length * (9 / 250)) + "\n"
        get_ui().set_text(ui_text)

        ###########################################

        self.prev_interp_ratio = interp_ratio

        ####################################################

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.spectate_count == 0:
                return

            self.spectate_idx += 1;
            if self.spectate_idx >= self.spectate_count:
                self.spectate_idx = -1

    def keyPressEvent(self, event):
        # Switch to player closest to ball
        if event.key() == Qt.Key_P:
            if not (self.prev_state is None):
                closest_idx = -1
                closest_dist = 100_000
                for i in range(len(self.prev_state.car_states)):
                    player = self.prev_state.car_states[i] # type: CarState
                    dist_to_ball = (player.phys.next_pos - self.prev_state.ball_state.next_pos).length
                    if dist_to_ball < closest_dist:
                        closest_idx = i
                        closest_dist = dist_to_ball

                self.spectate_idx = closest_idx


g_socket_listener = None
def run_socket_thread(port):
    global g_socket_listener
    g_socket_listener = SocketListener()
    g_socket_listener.run(port)

def main():
    #cmd_args = arg_parser.parse_args()
    port = 9273
    
    print("Starting RocketSimVis...")

    print("Starting socket thread...")
    socket_thread = threading.Thread(target=run_socket_thread, args=(int(port),))
    socket_thread.start()

    print("Starting visualizer window...")

    app = QtWidgets.QApplication([])
    ui.update_scaling_factor(app)

    window = QRSVWindow(QRSVGLWidget(app.primaryScreen()))
    window.showNormal()
    app.exec_()

    print("Shutting down...")
    g_socket_listener.stop_async()
    exit()

if __name__ == "__main__":
    main()