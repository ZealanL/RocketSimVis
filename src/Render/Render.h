#pragma once
#include "../Framework.h"
#include "../Color.h"

#include "Model/Model.h"
#include "Camera/Camera.h"
#include "RibbonEmitter/RibbonEmitter.h"

namespace Render {
	void Init(int windowSizeX, int windowSizeY);

	typedef std::function<void(SDL_Event*)> SDLEventHandlerFn;
	void StartFrame(Camera* camera, SDLEventHandlerFn handler);
	void RenderModel(Model* model, Vec pos, btMatrix3x3 matrix, Vec scale = Vec(1, 1, 1), Color globalColor = Color(1, 1, 1, 1), bool wireframe = false, bool enableShaders = true);
	void RenderRibbon(Camera* camera, RibbonEmitter* ribbon, float lifetime, float width, float startTaperTime, Color color);
	void FinishFrame();

	void SetArenaColoringEnabled(bool enabled);
	
	// World-to-screen projection
	// Point is valid of the Z component is non-zero, otherwise behind camera
	Vec W2S(Camera* camera, Vec pos);
}