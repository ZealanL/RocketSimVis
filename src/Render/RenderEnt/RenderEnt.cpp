#include "RenderEnt.h"

RenderEnt::RenderEnt(State initialState) {
	prev = cur = next = initialState;
	lastInterval = timeSinceUpdate = 0;
}

RotMat InterpRotMat(RotMat a, RotMat b, float ratio) {
	btQuaternion qA, qB;
	((btMatrix3x3)a).getRotation(qA);
	((btMatrix3x3)b).getRotation(qB);

	btQuaternion qInterp = qA.slerp(qB, ratio);
	btMatrix3x3 interp;
	interp.setRotation(qInterp);
	return interp;
}

void RenderEnt::Step(float deltaTime) {

	float lerpRatio = RS_CLAMP(RS_MIN(timeSinceUpdate, MAX_INTERP_TIME) / (lastInterval + deltaTime), 0, 1);

	cur.pos = ((btVector3)prev.pos).lerp(next.pos, lerpRatio);
	cur.rot = InterpRotMat(prev.rot, next.rot, lerpRatio);
	timeSinceUpdate += deltaTime;
}

void RenderEnt::Update(State newState) {
	lastInterval = timeSinceUpdate;
	timeSinceUpdate = 0;
	prev = cur = next;
	next = newState;
}