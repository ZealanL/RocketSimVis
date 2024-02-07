#include "Render.h"

#include "GLShader/GLShader.h"

#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <glm/gtx/euler_angles.hpp>

SDL_Window* g_SDLWindow;
SDL_GLContext g_GLContext;
GLuint g_GLProgram;
int g_WindowSizeX, g_WindowSizeY;

glm::mat4
g_Camera_ProjMatrix,
g_Camera_ViewMatrix;

GLuint
g_GLID_ProjMatrix,
g_GLID_ViewMatrix,
g_GLID_ModelMatrix,

g_GLID_GlobalModelColor,
g_GLID_EnableShaders,
g_GLID_EnableArenaColoring;

void UpdateView(Camera* camera) {
	g_Camera_ProjMatrix = glm::perspective(
		glm::radians(camera->fovDegrees), (float)g_WindowSizeX / (float)g_WindowSizeY,
		0.1f, 100000.0f
	);

	g_Camera_ViewMatrix = glm::mat4(1);
	glm::vec3 camPosGLM = glm::vec3(camera->pos.x, camera->pos.y, camera->pos.z);
	Vec camForward = camera->CalcForwardDir();
	glm::vec3 camForwardGLM = glm::vec3(camForward.x, camForward.y, camForward.z);

	g_Camera_ViewMatrix = glm::lookAt(
		camPosGLM,
		camPosGLM + camForwardGLM,
		glm::vec3(0, 0, 1) // Upright
	);
}

void SetupOpenGL() {
	g_GLContext = SDL_GL_CreateContext(g_SDLWindow);
	assert(g_GLContext);

	// Initialize glew
	glewExperimental = GL_TRUE;
	glewInit();

	{ // Set up OpenGL program with shaders
		g_GLProgram = glCreateProgram();

		GLShader shader = GLShader(
			SHADERS_DIR_PATH "vs.shader", 
			SHADERS_DIR_PATH "fs.shader",
			SHADERS_DIR_PATH "ge.shader"
		);
		shader.AttachToProgram(g_GLProgram);

		glLinkProgram(g_GLProgram);

		GLint validateResult;
		glGetProgramiv(g_GLProgram, GL_LINK_STATUS, &validateResult);
		if (!validateResult) {
			int logLength;
			glGetProgramiv(g_GLProgram, GL_INFO_LOG_LENGTH, &logLength);

			string errorLogStr = string(logLength, NULL);
			glGetProgramInfoLog(g_GLProgram, logLength, &logLength, errorLogStr.data());
			RS_ERR_CLOSE("Failed to load program: " << errorLogStr);
		}

		glValidateProgram(g_GLProgram);

		

		// Set up matrix links between the vertex shader and us
		g_GLID_ProjMatrix = glGetUniformLocation(g_GLProgram, "projection");
		g_GLID_ViewMatrix = glGetUniformLocation(g_GLProgram, "view");
		g_GLID_ModelMatrix = glGetUniformLocation(g_GLProgram, "model");

		// Set up model color link
		g_GLID_GlobalModelColor = glGetUniformLocation(g_GLProgram, "globalModelColor");

		g_GLID_EnableShaders = glGetUniformLocation(g_GLProgram, "enableShaders");
		g_GLID_EnableArenaColoring = glGetUniformLocation(g_GLProgram, "enableArenaColoring");

		glUseProgram(g_GLProgram);
	}

	// Set clear color to black
	glClearColor(0.f, 0.f, 0.f, 1.f);

	// Enable blending
	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

	// Enable depth
	glEnable(GL_DEPTH_TEST);
	glDepthFunc(GL_LESS);

	// Enable culling
	glCullFace(GL_BACK);
	glFrontFace(GL_CCW);
	glEnable(GL_CULL_FACE);

	//glEnable(GL_MULTISAMPLE);
	glEnable(GL_LINE_SMOOTH);
	glHint(GL_LINE_SMOOTH_HINT, GL_NICEST);

	// Viewport scale
	glViewport(0, 0, g_WindowSizeX, g_WindowSizeY);

	// No swap delay
	SDL_GL_SetSwapInterval(0);

	RS_LOG("OpenGL version: " << glGetString(GL_VERSION));
}

void Render::Init(int windowSizeX, int windowSizeY) {
	g_WindowSizeX = windowSizeX;
	g_WindowSizeY = windowSizeY;

	g_SDLWindow = SDL_CreateWindow(
		"RocketSimVis", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, windowSizeX, windowSizeY,
		SDL_WINDOW_OPENGL);

	SetupOpenGL();

	SDL_ShowWindow(g_SDLWindow);

	// Lock cursor in the center of the screen
	//SDL_SetRelativeMouseMode(SDL_TRUE);
}

void Render::StartFrame(Camera* camera, Render::SDLEventHandlerFn handler) {
	{ // Process events
		SDL_Event event;
		while (SDL_PollEvent(&event))
			handler(&event);
	}

	// Clear buffer
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

	UpdateView(camera);

	// Set global model color to white
	Color white = Color(1, 1, 1);
	glUniform4fv(g_GLID_GlobalModelColor, 1, &white.r);

	// Disable arena coloring
	glUniform1i(g_GLID_EnableArenaColoring, false);

	// Enable shaders
	glUniform1i(g_GLID_EnableShaders, true);

	// Update camera matrixes
	glUniformMatrix4fv(g_GLID_ProjMatrix, 1, GL_FALSE, &g_Camera_ProjMatrix[0][0]);
	glUniformMatrix4fv(g_GLID_ViewMatrix, 1, GL_FALSE, &g_Camera_ViewMatrix[0][0]);

	// Make default model matrix just 4x4 identity
	auto defaultModelMatrix = glm::mat4(1);
	glUniformMatrix4fv(g_GLID_ModelMatrix, 1, GL_FALSE, &defaultModelMatrix[0][0]);
}

void Render::FinishFrame() {
	glFinish();
	SDL_GL_SwapWindow(g_SDLWindow);
}

void Render::SetArenaColoringEnabled(bool enabled) {
	glUniform1i(g_GLID_EnableArenaColoring, enabled);
}

void Render::RenderModel(Model* model, Vec pos, btMatrix3x3 matrix, Vec scale, Color globalColor, bool wireframe, bool enableShaders) {
	glm::mat4 modelMatrix = glm::mat4(1);

	matrix = matrix.transpose();

	// Copy rotation to inner 3x3
	for (int i = 0; i < 3; i++)
		for (int j = 0; j < 3; j++)
			modelMatrix[i][j] = matrix[i][j];
	
	// Copy position to 4th column
	for (int i = 0; i < 3; i++)
		modelMatrix[3][i] = pos[i];

	// Apply scale
	modelMatrix = glm::scale(modelMatrix, *(glm::vec3*)(&scale));

	// Load model color
	glUniform4fv(g_GLID_GlobalModelColor, 1, &globalColor.r);

	glPolygonMode(GL_FRONT_AND_BACK, wireframe ? GL_LINE : GL_FILL);

	if (!enableShaders) {
		glUniform1i(g_GLID_EnableShaders, false);
		glEnable(GL_POLYGON_OFFSET_FILL);
		glPolygonOffset(10, 1);
	}

	model->Render(modelMatrix, g_GLID_ModelMatrix);

	if (!enableShaders) {
		glUniform1i(g_GLID_EnableShaders, true);
		glDisable(GL_POLYGON_OFFSET_FILL);
	}
}

void Render::RenderRibbon(Camera* camera, RibbonEmitter* ribbon, float lifetime, float width, float startTaperTime, Color color) {
	if (ribbon->points.empty())
		return;

	glUniform1i(g_GLID_EnableShaders, false);

	// Set color
	glUniform4fv(g_GLID_GlobalModelColor, 1, &color.r);

	RibbonEmitter::Point& firstPoint = ribbon->points.front();
	Vec camToRibbonDir = -(firstPoint.pos - camera->pos).Normalized();
	Vec ribbonAwayDir = firstPoint.vel.Normalized();
	Vec ribbonSidewaysDir = ribbonAwayDir.Cross(camToRibbonDir).Normalized();

	{
		glDisable(GL_CULL_FACE);
		glBegin(GL_TRIANGLE_STRIP);
		for (RibbonEmitter::Point& point : ribbon->points) {

			if (point.disconnected) {
				glEnd();
				glBegin(GL_TRIANGLE_STRIP);
				continue;
			}

			float widthScale;
			if (point.timeActive < startTaperTime) {
				widthScale = point.timeActive / startTaperTime;
			} else {
				widthScale = 1 - (point.timeActive / lifetime);
			}

			Vec offset = ribbonSidewaysDir * width * widthScale;
			for (int j = 0; j < 2; j++) {
				float offsetScale = (j ? 1 : -1);
				Vec vertexPos = point.pos + (offset * offsetScale);
				glVertex3f(vertexPos.x, vertexPos.y, vertexPos.z);
			}
		}
		glEnd();
		glEnable(GL_CULL_FACE);
	}

	// Reset color
	Color white = Color(1, 1, 1);
	glUniform4fv(g_GLID_GlobalModelColor, 1, &white.r);

	glUniform1i(g_GLID_EnableShaders, true);
}

Vec Render::W2S(Camera* camera, Vec pos) {
	glm::vec4 glmPoint = { pos.x, pos.y, pos.z, 1 };
	glm::vec4 toScreen = g_Camera_ProjMatrix * g_Camera_ViewMatrix * glmPoint;

	if (toScreen.w > 0.001f) {
		toScreen /= toScreen.w;
		toScreen /= camera->scale;
		return Vec(toScreen.x, toScreen.y, 1);
	} else {
		return Vec(0, 0, 0);
	}
}