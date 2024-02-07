#pragma once
#include "../RocketSim/src/RocketSim.h"
using namespace RocketSim;

using std::string;
using std::vector;

#define SDL_MAIN_HANDLED
#include <SDL.h>

#define GL_GLEXT_PROTOTYPES
#include <GL/glew.h>
#include <glm/glm.hpp>

#define BASE_OUT_PATH "./"
#define MODELS_DIR_PATH BASE_OUT_PATH "models/"
#define SHADERS_DIR_PATH BASE_OUT_PATH "shaders/"