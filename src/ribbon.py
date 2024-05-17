from collections import deque

from pyrr import Vector3

class RibbonPoint:
    def __init__(self, pos, vel):
        self.pos = pos
        self.vel = vel
        self.time_active = 0
        self.connected = True

class RibbonEmitter:
    def __init__(self):
        self.points = deque()
        self.time_since_emit = 0

    def update(self, can_emit, emit_delay, emit_pos, emit_vel, lifetime, delta_time):
        if self.time_since_emit < emit_delay:
            self.time_since_emit += delta_time
            if len(self.points) > 0:
                self.points[0].connected = False
        elif can_emit:
            self.time_since_emit = 0

            new_point = RibbonPoint(emit_pos, emit_vel)
            self.points.insert(0, new_point)

        for point in self.points:
            point.pos += point.vel * delta_time
            point.time_active += delta_time

        # Remove dead points
        while len(self.points) > 0 and self.points[-1].time_active > lifetime:
            self.points.pop()