#pragma once
#include "../../Framework.h"

struct RibbonEmitter {
	struct Point {
		Vec pos;
		Vec vel;
		float timeActive = 0;
		bool disconnected = false;
	};

	std::deque<Point> points;
	float timeSinceEmit = 0;

	void Update(bool canEmit, float emitDelay, Vec emitPos, Vec emitVel, float lifeTime, float deltaTime);
};