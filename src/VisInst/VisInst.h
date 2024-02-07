#pragma once
#include "../Framework.h"
#include "../Color.h"
#include "../Render/Model/Model.h"
#include "../Render/RibbonEmitter/RibbonEmitter.h"
#include "../Render/Camera/Camera.h"
#include "../Render/RenderEnt/RenderEnt.h"

struct VisInst {
	Arena* arenaInst;
	int windowSizeX, windowSizeY;
	int framerate;

	Camera camera;
	int specCarIdx = 0;

	Model* carModels[2] = {};
	Model* ballModel;
	Model* puckModel;

	Model* boostPadModelsSmall[2]; // First is inactive, second is active
	Model* boostPadModelsBig[2];

	std::vector<Model*> arenaCollisionModels;
	Model* floorModel;

	struct CarInfo {
		RenderEnt renderEnt;
		RibbonEmitter boostRibbon;
	};

	std::unordered_map<uint32_t, CarInfo> carInfos;
	
	std::vector<Model*> allModels;

	RenderEnt ballRenderEnt = RenderEnt();
	std::vector<RenderEnt> carRenderEnts = {};

	std::mutex updateMutex;

	VisInst(int windowSizeX = 1440, int windowSizeY = 960, int framerate = 120, GameMode gameMode = GameMode::SOCCAR);
	~VisInst();

	Model* AddModel();

	void SDLEventHandler(SDL_Event* e);
	void MakePuckModel();
	void Run();
	void UpdateNewStates();
	void UpdateCarInfos();
};