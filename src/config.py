class ConfigVal:
    def __init__(self, default, min, max):
        self.val = float(default)
        self.min = float(min)
        self.max = float(max)

    def __float__(self):
        return self.val

class Config:
    def __init__(self):
        self.camera_distance = ConfigVal(300, 100, 500)
        self.camera_height = ConfigVal(120, 0, 300)
        self.camera_fov = ConfigVal(75, 20, 120)
        self.camera_bird_fov = ConfigVal(60, 20, 120)

        self.camera_lean_height_scale = ConfigVal(1.0, 0, 1)
        self.camera_lean_dist_scale = ConfigVal(0.1, 0, 1)
        self.camera_lean_min_height_clamp = ConfigVal(300, 0, 500)