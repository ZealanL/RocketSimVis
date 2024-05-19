import os
import math
import random
import threading
import sys 
import argparse
import copy

import pyrr.vector3

from const import *
from shaders import *
from socket_listener import SocketListener
from state_manager import *
from ribbon import *

import moderngl
from OpenGL.GL import *
from OpenGL.GLU import *

import numpy as np

from pyrr import Quaternion, Matrix33, Matrix44, Vector3, Vector4

import moderngl_window as mglw

import pywavefront


# Makes Y up instead of Z
def yup(v):
    v = Vector3(v)
    old_y = v.y
    v.y = v.z
    v.z = old_y
    return v

class RocketSimVisWindow(mglw.WindowConfig):
    gl_version = (4, 0)
    window_size = (WINDOW_SIZE_X, WINDOW_SIZE_Y)
    title = "RocketSimVis"
    samples = 2

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.spectate_count = 0
        self.spectate_idx = 0
        self.prev_interp_ratio = 0

        ##########################################

        print("Initializing shaders...")

        self.prog = self.ctx.program(
            vertex_shader=VERT_SHADER,
            fragment_shader=FRAG_SHADER,
            geometry_shader=GEOM_SHADER
        )

        self.prog_arena = self.ctx.program(
            vertex_shader=VERT_SHADER,
            fragment_shader=FRAG_SHADER_ARENA,
            geometry_shader=GEOM_SHADER
        )

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
        self.vao_arena = self.load_make_vao("ArenaMeshCustom.obj", self.prog_arena)

        self.vao_octane = self.load_make_vao("Octane.obj")
        self.vao_ball = self.load_make_vao("Ball.obj")

        self.vaos_boost_pad = [
            [ self.load_make_vao("BoostPad_Small_0.obj"), self.load_make_vao("BoostPad_Small_1.obj")],
            [ self.load_make_vao("BoostPad_Big_0.obj"), self.load_make_vao("BoostPad_Big_1.obj") ]
        ]

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

        self.ribbon_max_verts = 100
        self.ribbon_verts = np.random.randn(self.ribbon_max_verts * 3) * 1000
        self.ribbon_vbo = self.ctx.buffer(self.ribbon_verts.astype('f4'))
        self.ribbon_vao = self.ctx.simple_vertex_array(self.prog, self.ribbon_vbo, "in_position")

        self.ctx.multisample = True

        print("Done.")

    def load_make_vao(self, model_name, program = None):
        model = self.load_scene(DATA_DIR_PATH + "/" + model_name)
        return model.root_nodes[0].mesh.vao.instance(self.prog if (program is None) else self.prog_arena)

    def render_model(self, pos, forward, up, model_vao, texture, scale = 1.0, global_color = None, mode = moderngl.TRIANGLES):
        if pos is None:
            model_mat = Matrix44.identity()
        else:
            pos = Vector3(pos)
            forward = Vector3(forward)
            up = Vector3(up)
            right = pyrr.vector3.cross(forward, up)

            model_mat = Matrix44([
                forward[0], forward[1], forward[2], 0,
                -right[0], -right[1], -right[2], 0,
                up[0], up[1], up[2], 0,
                pos[0], pos[1], pos[2], 1
            ]) * scale

        self.pr_m_model.write(model_mat.astype('f4'))
        self.pra_m_model.write(model_mat.astype('f4'))

        if global_color is None:
            global_color = Vector4((0, 0, 0, 0))
        self.pr_global_color.write(global_color.astype('f4'))

        if texture is not None:
            texture.use()
        else:
            self.t_none.use()

        model_vao.render(mode)

    def render_ribbon(self, ribbon: RibbonEmitter, camera_pos, lifetime, width, start_taper_time, color):
        if len(ribbon.points) == 0:
            return

        vertices = []

        first_point = ribbon.points[0]
        cam_to_ribbon_dir = -(first_point.pos - camera_pos).normalized
        ribbon_away_dir = first_point.vel.normalized
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
            self.ribbon_vao, self.t_none, 20,
            color,
            moderngl.TRIANGLE_STRIP
        )
        glEnable(GL_CULL_FACE)

    def calc_camera_state(self, state, interp_ratio):
        pos = Vector3((-4000, 0, 1000))
        target_pos = state.ball_state.get_pos(interp_ratio)

        # TODO: Make configurable params
        CAM_DISTANCE = 270
        CAM_HEIGHT = 120
        CAM_FOV = 80
        CAM_BIRD_FOV = 60

        CAM_LEAN_HEIGHT_SCALE = 1.0
        CAM_LEAN_DIST_SCALE = 0.4
        CAM_LEAN_DIST_EXP = 1.0
        CAM_LEAN_MIN_HEIGHT_CLAMP = 300

        if self.spectate_idx > -1:
            if len(state.car_states) > self.spectate_idx:

                height = CAM_HEIGHT
                dist = CAM_DISTANCE

                car_pos = state.car_states[self.spectate_idx].phys.get_pos(interp_ratio)

                cam_dir = (target_pos - car_pos).normalized

                # As we tilt up, move the camera down
                lean_scale = cam_dir.z
                height_clamp = abs(target_pos.z - car_pos.z) / CAM_LEAN_MIN_HEIGHT_CLAMP
                height *= 1 - min(lean_scale * CAM_LEAN_HEIGHT_SCALE, height_clamp)

                # As we tilt up, move the camera closer
                dist *= 1 - pow(lean_scale, CAM_LEAN_DIST_EXP) * CAM_LEAN_DIST_SCALE

                cam_offset = cam_dir * Vector3((-1, -1, 0)) * dist
                cam_offset.z +=height

                pos = car_pos + cam_offset

        return pos, target_pos, (CAM_FOV if (self.spectate_idx >= 0) else CAM_BIRD_FOV)

    def render(self, total_time, delta_time):

        with global_state_mutex:
            if not global_state_manager.state.ball_state.has_rot:
                global_state_manager.state.ball_state.rotate_with_ang_vel(delta_time)

            state = copy.deepcopy(global_state_manager.state)

        self.spectate_count = len(state.car_states)

        while len(self.car_ribbons) != len(state.car_states):
            if len(self.car_ribbons) < len(state.car_states):
                self.car_ribbons.append(RibbonEmitter())
            else:
                self.car_ribbons.pop()

        cur_time = time.time()
        interp_interval = max(state.recv_interval, 1e-6)
        interp_ratio = min(max((cur_time - state.recv_time) / interp_interval, 0), 1)

        #self.pr_enable_arena_coloring.value = False

        self.ctx.clear(0, 0, 0)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)

        self.ctx.cull_face = "back"
        self.ctx.front_face = "ccw"
        self.ctx.enable(moderngl.CULL_FACE)

        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        camera_pos, camera_target_pos, camera_fov = self.calc_camera_state(state, interp_ratio)

        proj = Matrix44.perspective_projection(camera_fov, self.aspect_ratio, 0.1, 50 * 1000.0)
        lookat = Matrix44.look_at(
            camera_pos,
            camera_target_pos,
            (0.0, 0.0, 1.0),
        )

        self.pr_camera_pos.write(camera_pos.astype('f4'))
        self.pr_m_vp.write((proj * lookat).astype('f4'))
        self.pra_m_vp.write((proj * lookat).astype('f4'))

        if not (state.boost_pad_states is None): # Render boost pads
            for i in range(len(state.boost_pad_states)):
                is_big = state.is_boost_big(i)

                is_active = state.boost_pad_states[i]

                pos = state.boost_pad_locations[i].copy()
                pos.z = 0

                self.render_model(
                    pos, Vector3((1, 0, 0)), Vector3((0, 0, 1)),
                    self.vaos_boost_pad[int(is_big)][int(is_active)],
                    self.t_boostpad,
                    3,
                )


        if True: # Render ball
            ball_phys = state.ball_state
            ball_pos = ball_phys.get_pos(interp_ratio)
            self.render_model(
                ball_pos,
                ball_phys.get_forward(interp_ratio), ball_phys.get_up(interp_ratio), self.vao_ball, self.t_ball
            )

            if True: # Update and render ball ribbon
                ball_speed = ball_phys.vel.length
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
                    50,
                    ribbon_lifetime / 10,
                    Vector4((1, 1, 1, ribbon_alpha))
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
                self.render_model(
                    car_pos,
                    car_forward, car_up, self.vao_octane, self.ts_octane[car_state.team_num]
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



        #self.ctx.wireframe = True
        #self.pr_enable_arena_coloring.value = True
        self.pra_ball_pos.write(state.ball_state.get_pos(interp_ratio).astype('f4'))
        self.render_model(None, None, None, self.vao_arena, self.t_none, 1, Vector4((1,1,1,1)))
        #self.pr_enable_arena_coloring.value = False
        #self.ctx.wireframe = False

        # Render black matte behind
        # TODO: Makes lines aliased
        #arena_matte_scale = 1.02 # Shift back slightly to fix z fighting
        #self.render_model(None, None, None, self.vao_arena, self.t_black, arena_matte_scale)

        self.prev_interp_ratio = interp_ratio

    ####################################################

    def mouse_press_event(self, x, y, button):
        if self.spectate_count == 0:
            return

        self.spectate_idx += 1;
        if self.spectate_idx >= self.spectate_count:
            self.spectate_idx = -1

''' TODO: Breaks moderngl?
arg_parser = argparse.ArgumentParser(
                    prog='RocketSimVis',
                    description='Python visualizer for RocketSim games',
                    epilog='')
arg_parser.add_argument("-p", "--port")
'''

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
    RocketSimVisWindow.run()

    print("Shutting down...")
    g_socket_listener.stop_async()
    exit()

if __name__ == "__main__":
    main()