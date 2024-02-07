#include "VisInst.h"
#include "../Render/Render.h"
#include "../../RocketSim/libsrc/bullet3-3.24/BulletCollision/CollisionShapes/btTriangleMesh.h"
#include "../../RocketSim/libsrc/bullet3-3.24/BulletCollision/CollisionShapes/btTriangleMeshShape.h"

constexpr Color TEAM_COLORS[2] = {
	Color(0.1, 0.6, 1.0),
	Color(1.0, 0.6, 0.1)
};

void VisInst::SDLEventHandler(SDL_Event* e) {
	if (e->type == SDL_QUIT)
		exit(EXIT_SUCCESS);

	if (e->type == SDL_KEYDOWN) {
		SDL_Scancode keyCode = e->key.keysym.scancode;
		if (keyCode == SDL_SCANCODE_SPACE) {
			// Toggle ball cam?
		}
	}

	if (e->type == SDL_MOUSEBUTTONDOWN) {
		if (e->button.button == SDL_BUTTON_LEFT) {
			// Cycle spectate
			specCarIdx++;
			if (specCarIdx >= arenaInst->_cars.size()) {
				specCarIdx = -1; // Freecam
			}
		}
	}
}

void VisInst::MakePuckModel() {
	puckModel = AddModel();

	Model::MaterialColors matColors;
	matColors.defaultColor = Color(0.2, 0.2, 0.3);

	vector<Vec> points;
	using namespace RLConst;
	float angStep = (M_PI * 2) / Snowday::PUCK_CIRCLE_POINT_AMOUNT;
	float curAng = 0;
	for (int i = 0; i < Snowday::PUCK_CIRCLE_POINT_AMOUNT + 1; i++) {
		Vec point = Vec(
			cosf(curAng) * Snowday::PUCK_RADIUS,
			sinf(curAng) * Snowday::PUCK_RADIUS,
			Snowday::PUCK_HEIGHT / 2
		);

		points.push_back(point);
		point.z *= -1;
		points.push_back(point);

		curAng += angStep;
	}

	for (int i = 0; i < points.size(); i++) {
		Vec p = points[i];
		puckModel->vertices.push_back({ p.x, p.y, p.z });
		Vec norm = p.Normalized();
		puckModel->normals.push_back({ norm.x, norm.y, norm.z });
	}

	for (int i = 0; i < points.size() - 2; i++) {
		Model::Tri tri;
		for (int j = 0; j < 3; j++) {
			tri.vertIdx[j] = i + j;
			tri.normIdx[j] = i + j;
		}

		puckModel->triangles.push_back(tri);
		std::swap(tri.vertIdx[0], tri.vertIdx[2]);
		std::swap(tri.normIdx[0], tri.normIdx[2]);
		puckModel->triangles.push_back(tri);
	}

	int topVertIdx = puckModel->vertices.size();
	puckModel->vertices.push_back({ 0, 0, Snowday::PUCK_HEIGHT / 2 });
	puckModel->normals.push_back({ 0, 0, 1 });

	int bottomVertIdx = puckModel->vertices.size();
	puckModel->vertices.push_back({ 0, 0, -Snowday::PUCK_HEIGHT / 2 });
	puckModel->normals.push_back({ 0, 0, -1 });

	for (int top = 0; top < 2; top++) {
		int centerVertIdx = top ? topVertIdx : bottomVertIdx;
		for (int i = top ? 0 : 1; i < points.size() - 2; i += 2) {
			Model::Tri tri;
			tri.vertIdx[0] = i;
			tri.vertIdx[1] = i + 2;
			tri.vertIdx[2] = centerVertIdx;


			tri.normIdx[0] = centerVertIdx;
			tri.normIdx[1] = centerVertIdx;
			tri.normIdx[2] = centerVertIdx;

			puckModel->triangles.push_back(tri);
			std::swap(tri.vertIdx[0], tri.vertIdx[2]);
			puckModel->triangles.push_back(tri);
		}
	}

	for (Model::Tri& tri : puckModel->triangles)
		tri.col = matColors.defaultColor;

	puckModel->LoadIntoGL();
}

VisInst::VisInst(int windowSizeX, int windowSizeY, int framerate, GameMode gameMode) 
	: windowSizeX(windowSizeX), windowSizeY(windowSizeY), framerate(framerate) {
	if (RocketSim::GetStage() != RocketSimStage::INITIALIZED)
		RocketSim::Init("./collision_meshes");

	arenaInst = Arena::Create(gameMode);
	arenaInst->AddCar(Team::BLUE);
	arenaInst->AddCar(Team::ORANGE);

	Render::Init(windowSizeX, windowSizeY);

	// Load car model
	for (int i = 0; i < 2; i++) {
		Model::MaterialColors matColors;
		matColors.defaultColor = TEAM_COLORS[i];

		// Set up colors of other car materials
		matColors.otherColors["Metal_Bar"] = Color(0.3, 0.3, 0.3);
		matColors.otherColors["Wheel"] = Color(0.2, 0.2, 0.2);
		matColors.otherColors["Underbelly"] = Color(0.3, 0.3, 0.3);
		matColors.otherColors["Window"] = Color(0.1, 0.1, 0.1);
		matColors.otherColors["Headlight"] = Color(0.9, 0.8, 0.5);

		carModels[i] = AddModel();
		carModels[i]->ReadFromOBJ(MODELS_DIR_PATH "Octane.obj", matColors);
		carModels[i]->LoadIntoGL();
	}

	// Load ball or puck model
	if (arenaInst->gameMode != GameMode::SNOWDAY) {
		Model::MaterialColors matColors;
		matColors.defaultColor = Color(0.7, 0.7, 0.7);
		matColors.otherColors["Caps_Base"] = Color(0.4, 0.4, 0.4);
		matColors.otherColors["Caps_Inner"] = Color(0.5, 0.5, 0.5);

		ballModel = AddModel();
		ballModel->ReadFromOBJ(MODELS_DIR_PATH "Ball.obj", matColors);
		ballModel->LoadIntoGL();
	} else {
		MakePuckModel();
	}

	// Make models from arena collision shapes
	for (size_t i = 0; i < arenaInst->_worldCollisionRBAmount; i++) {
		auto rb = &arenaInst->_worldCollisionRBs[i];
		auto shape = rb->getCollisionShape();
		if (shape->getShapeType() == TRIANGLE_MESH_SHAPE_PROXYTYPE) {
			auto triangleMesh = (btTriangleMeshShape*)shape;
			btTriangleMesh* triMesh = (btTriangleMesh*)triangleMesh->getMeshInterface();

			Model* model = AddModel();

			for (int i = 0; i < triMesh->m_4componentVertices.size(); i++) {
				Model::Vertex vert;
				for (int j = 0; j < 3; j++)
					vert[j] = triMesh->m_4componentVertices[i][j] * BT_TO_UU;
				model->vertices.push_back(vert);
				model->normals.push_back({ 1.f, 0.f, 0.f });
			}

			for (int i = 0; i < triMesh->m_32bitIndices.size() / 3; i++) {
				Model::Tri tri;
				for (int j = 0; j < 3; j++) {
					tri.vertIdx[j] = triMesh->m_32bitIndices[i * 3 + j];
					tri.normIdx[j] = tri.vertIdx[j];
				}

				model->triangles.push_back(tri);
			}

			model->LoadIntoGL();
			arenaCollisionModels.push_back(model);
		}
	}

	// Add floor model
	{
		floorModel = AddModel();
		floorModel->ReadFromOBJ(MODELS_DIR_PATH "Floor.obj", Model::MaterialColors());
		floorModel->LoadIntoGL();
		arenaCollisionModels.push_back(floorModel);
	}

	// Add boost pad models
	{
		for (int i = 0; i < 2; i++) {
			for (int j = 0; j < 2; j++) {
				Model*& boostPadModel = (i ? boostPadModelsBig : boostPadModelsSmall)[j];
				boostPadModel = AddModel();

				Model::MaterialColors matColors;
				matColors.otherColors["Base_Metal"] = Color(0.25, 0.25, 0.25);
				matColors.otherColors["Boost_Glow"] = j ? Color(1, 0.9, 0.2, 0.9f) : Color(0, 0, 0, 0);

				boostPadModel->ReadFromOBJ(i ? (MODELS_DIR_PATH "BoostPadLarge.obj") : (MODELS_DIR_PATH "BoostPadSmall.obj"), matColors);
				boostPadModel->LoadIntoGL();
			}
		}
	}
}

void VisInst::UpdateCarInfos() {
	// Add new car infos
	for (Car* car : arenaInst->_cars) {
		if (carInfos.find(car->id) == carInfos.end()) {
			carInfos[car->id] = CarInfo();
		}
	}

	// Remove old car infos
	while (carInfos.size() > arenaInst->_cars.size()) {

	}
}

void VisInst::UpdateNewStates() {
	constexpr float TELEPORT_MIN_DIST = 400;

	auto ballState = arenaInst->ball->GetState();
	if (ballState.pos.DistSq(ballRenderEnt.next.pos) > (TELEPORT_MIN_DIST * TELEPORT_MIN_DIST)) {
		ballRenderEnt = RenderEnt(RenderEnt::State(ballState.pos, ballState.rotMat));
	} else {
		ballRenderEnt.Update(RenderEnt::State(ballState.pos, ballState.rotMat));
	}
	
	for (Car* car : arenaInst->_cars) {
		CarState carState = car->GetState();
		auto& carInfo = carInfos[car->id];
		bool isTeleporting = carState.pos.DistSq(carInfo.renderEnt.next.pos) > (TELEPORT_MIN_DIST * TELEPORT_MIN_DIST);
		if (isTeleporting) {
			carInfo.renderEnt = RenderEnt(RenderEnt::State(carState.pos, carState.rotMat));
			carInfo.boostRibbon = RibbonEmitter();
		} else {
			carInfo.renderEnt.Update(RenderEnt::State(carState.pos, carState.rotMat));
		}
	}
}

VisInst::~VisInst() {
	delete arenaInst;

	for (Model* m : allModels)
		delete m;
	allModels.clear();
}

void VisInst::Run() {
	auto lastFrameTime = RS_CUR_MS();
	float targetFrameTime = 1.f / framerate;
	while (true) {
		updateMutex.lock();

		auto deltaMs = RS_CUR_MS() - lastFrameTime;
		float deltaTime = targetFrameTime;
		auto frameStartMs = RS_CUR_MS();

		// Step render ents
		ballRenderEnt.Step(deltaTime);
		for (Car* car : arenaInst->_cars)
			carInfos[car->id].renderEnt.Step(deltaTime);

		auto ballState = arenaInst->ball->GetState();
		ballRenderEnt.ApplyToState(ballState);
		// Update camera
		{
			if (specCarIdx >= 0 && specCarIdx < arenaInst->_cars.size()) {
				// Car list isn't ordered so we will just use the order in memory
				auto targetItr = arenaInst->_cars.begin();
				for (int i = 0; i < specCarIdx; i++)
					targetItr++;
				Car* targetCar = *targetItr;
				CarState carState = targetCar->GetState();
				carInfos[targetCar->id].renderEnt.ApplyToState(carState);
				camera.UpdateCarCam(carState, ballState, true, deltaTime);
				camera.fovDegrees = 80;
			} else {
				camera.pos = Vec(-4000, 0, 2000);
				camera.LookAt(ballRenderEnt.cur.pos);
				camera.fovDegrees = 70;
			}
		}

		Render::StartFrame(&camera, std::bind(&VisInst::SDLEventHandler, this, std::placeholders::_1));

		// Update boost ribbon(s)
		float boostRibbonLifetime = 0.8f;
		for (Car* c : arenaInst->_cars) {

			CarState carState = c->GetState();
			carInfos[c->id].renderEnt.ApplyToState(carState);

			RibbonEmitter& ribbon = carInfos[c->id].boostRibbon;

			Vec forwardDir = carState.rotMat.forward;
			Vec upDir = carState.rotMat.up;
			Vec boostRibbonStartPos = carState.pos - (forwardDir * 45) + (upDir * 10);
			ribbon.Update(
				c->controls.boost && c->_internalState.boost > 0,
				0.f,
				boostRibbonStartPos,
				forwardDir * -100,
				boostRibbonLifetime,
				deltaTime
			);
		}

		// Render arena collision meshes
		Render::SetArenaColoringEnabled(true);
		for (Model* arenaModel : arenaCollisionModels) {
			Render::RenderModel(arenaModel, Vec(0, 0, 0), btMatrix3x3::getIdentity(), Vec(1, 1, 1), Color(1, 1, 1), true);
			Render::RenderModel(arenaModel, Vec(0, 0, 0), btMatrix3x3::getIdentity(), Vec(1, 1, 1), Color(0, 0, 0), false, false);
		}
		Render::SetArenaColoringEnabled(false);

		// Render boost pads
		for (BoostPad* pad : arenaInst->_boostPads) {
			Render::RenderModel(
				(pad->isBig ? boostPadModelsBig : boostPadModelsSmall)[pad->_internalState.isActive],
				pad->pos * Vec(1, 1, 0),
				btMatrix3x3::getIdentity()
			);
		}

		// Render cars and boost ribbons
		for (Car* c : arenaInst->_cars) {
			if (c->_internalState.isDemoed)
				continue;

			int teamIndex = (int)c->team;

			RenderEnt& renderEnt = carInfos[c->id].renderEnt;
			Render::RenderModel(carModels[teamIndex], renderEnt.cur.pos, renderEnt.cur.rot);

			RibbonEmitter& boostRibbon = carInfos[c->id].boostRibbon;
			Render::RenderRibbon(&camera, &boostRibbon, boostRibbonLifetime, 20, boostRibbonLifetime / 10, Color(1.f, 0.9f, 0.4f));
		}

		// Render ball
		Model* model = arenaInst->ball->IsSphere() ? ballModel : puckModel;
		Render::RenderModel(model, ballRenderEnt.cur.pos, ballRenderEnt.cur.rot);

		Render::FinishFrame();

		updateMutex.unlock();

		auto frameTimeMs = RS_CUR_MS() - frameStartMs;
		auto baseDelay = RS_MAX(1000 / framerate, 1);
		SDL_Delay(RS_MAX(baseDelay - frameTimeMs, 1));

		lastFrameTime = RS_CUR_MS();
	}
}

Model* VisInst::AddModel() {
	Model* model = new Model();
	allModels.push_back(model);
	return model;
}