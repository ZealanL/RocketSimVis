#include "RibbonEmitter.h"

void RibbonEmitter::Update(bool canEmit, float emitDelay, Vec emitPos, Vec emitVel, float lifeTime, float deltaTime) {
	if (timeSinceEmit < emitDelay || !canEmit) {
		timeSinceEmit += deltaTime;
		if (!points.empty()) {
			points.front().disconnected = true;
		}
	} else {
		timeSinceEmit = 0;

		Point newPoint;
		newPoint.pos = emitPos;
		newPoint.vel = emitVel;
		points.push_front(newPoint);
	}

	for (Point& point : points) {
		point.pos += point.vel * deltaTime;
		point.timeActive += deltaTime;
	}

	// Remove dead points from the back
	while (!points.empty() && points.back().timeActive > lifeTime)
		points.pop_back();

}