# RocketSimVis Python
My Python visualizer for [RocketSim](https://github.com/ZealanL/RocketSim)

![image](https://github.com/ZealanL/RocketSimVis/assets/36944229/3112e332-da79-4c09-90b6-e2bb0fcbd559)

The goal of this visualizer is to be as easy to set up and use as possible, while also looking nice and simple.

This project has no RocketSim dependencies and uses custom-made low-poly meshes for cars, the ball, boost pads, and the arena.

Features:
- Clean low-poly style with entirely custom models
- Smooth interpolation for any update rate
- Boost and ball trails
- Clear vibrant team colors to make seeing cars easier
- Ball circle on the ground below the ball
- Player camera switching with additional static stadium camera
- No dependencies apart from `requirements.txt`

Roadmap (Planned Features):
- Simple player nameplates
- Jump and flip particles
- Freecam camera option
- Small UI section with debug info

## Installation with rlgym_sim/RLGym-PPO
1. Clone this repo and install the dependencies in `requirements.txt`
2. Copy the `rocketsimvis_rlgym_sim_client.py` file into the same directory you run rlgym-sim/RLGym-PPO in
3. Connect it to the rlgym_sim env(s):
```py
# Add these lines right after "env = rlgym_sim.make( ..."
import rocketsimvis_rlgym_sim_client as rsv
type(env).render = lambda self: rsv.send_state_to_rocketsimvis(self._prev_state)

# That's it!
```

## Running the visualizer
Just run `MAIN.bat` (if on Windows), or `main.py`.

## Is This Official?
No, there are many other cool visualizers available for RocketSim, I just thought I'd make mine open-source for those who want it.

## Communication
RocketSimVis communicates through a UDP socket on a pre-determined port. The gamestate should be sent as JSON text. 
There's no need for any kind of syncing, you just send the current gamestate over the port and it will be rendered.
You don't have to send every tick, and you can even send data faster or slower than real time!
The simulation renders at your monitor's refresh rate, and if the received gamestate is being updated slower than that, physics objects will be interpolated.

To learn how to communicate with the renderer, see [networking-format.md](networking-format.md)

## Models
All models are made by me to resemble things in the game.
You are welcome to use my models for whatever you like so long as you credit me.

## Dependencies 
All dependencies are listed in `requirements.txt`
