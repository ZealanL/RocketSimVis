cmake_minimum_required (VERSION 3.8)

project("RocketSimVis")

# Add all headers and code files
file(GLOB_RECURSE FILES_SRC "src/*.cpp" "src/*.h")
file(GLOB_RECURSE FILES_LIBSRC "libsrc/*.cpp" "libsrc/*.h")

add_executable(RocketSimVis ${FILES_SRC} ${FILES_LIBSRC})

# Set C++ version to 20
set_target_properties(RocketSimVis PROPERTIES LINKER_LANGUAGE CXX)
set_target_properties(RocketSimVis PROPERTIES CXX_STANDARD 20)

# Copy models and shaders to build directory
file(COPY "${CMAKE_CURRENT_SOURCE_DIR}/models" DESTINATION "${CMAKE_CURRENT_BINARY_DIR}")
file(COPY "${CMAKE_CURRENT_SOURCE_DIR}/shaders" DESTINATION "${CMAKE_CURRENT_BINARY_DIR}")

# Include RocketSim
add_subdirectory("${PROJECT_SOURCE_DIR}/RocketSim")
target_link_libraries(RocketSimVis RocketSim)

# Include OpenGL
target_link_libraries(RocketSimVis opengl32)

# Include GLEW
find_package(GLEW REQUIRED)
target_link_libraries(RocketSimVis GLEW::GLEW)

# Include SDL
find_package(SDL REQUIRED)
include_directories(${SDL_INCLUDE_DIRS})
target_link_libraries(RocketSimVis ${SDL_LIBRARIES})

# Include GLM
target_include_directories(RocketSimVis PRIVATE ${GLM_INCLUDE_DIRS})