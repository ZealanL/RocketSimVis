# RocketSimVis
My visualizer for [RocketSim](https://github.com/ZealanL/RocketSim)

![rocketsimvis](https://github.com/ZealanL/RocketSimVis/assets/36944229/644f618a-88de-409f-9722-a4ddcd4b490e)

## Is This Official?
No, there are many other cool visualizers available for RocketSim, I just thought I'd make mine open-source for those who want it.

## Communication
RocketSimVis communicates through a UDP socket on a pre-determined port. 
There's no need for any kind of syncing, you just send the current gamestate over the port and it will be rendered.
You don't have to send every tick, and you can even send data faster or slower than real time!
The simulation renders at 120fps, and if the received gamestate is being updated slower than that, physics objects will be interpolated.

## Models
All models are made by me to resemble things in the game, except arena meshes which are loaded from an internal RocketSim instance.
You are welcome to use my models for whatever you like so long as you credit me.

## Dependencies 
 - RocketSim (as a submodule)
 - A modified version of [cpp_sockets](https://github.com/computersarecool/cpp_sockets)
 - SDL2 (as cmake package) for general window creation, input, etc.
 - OpenGL for rendering
 - GLEW (as cmake package) to manage OpenGL
