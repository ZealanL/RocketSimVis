#pragma once
#include "../../Framework.h"

struct Camera {
	Vec pos = { 0, 0, 0 };
	Angle angle = { 0, 0, 0 };
	float fovDegrees = 100;
	float scale = 1;
	float mouseSensitivity = 1;

	void LookAt(Vec pos);
	Vec CalcForwardDir();

	void UpdateCarCam(
		const CarState& carState, const BallState& ballState, 
		bool inBallCam, 
		float deltaTime, 
		float distance = 290,
		float height = 120.f,
		float aboveCarHeight = 100.f
	);
};