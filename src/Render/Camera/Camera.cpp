#include "Camera.h"

void Camera::LookAt(Vec pos) {
	RotMat mat = RotMat::LookAt(pos - this->pos, Vec(0, 0, 1));
	angle = Angle::FromRotMat(mat);
}

Vec Camera::CalcForwardDir() {
	// TODO: Inefficient
	return angle.ToRotMat().forward;
}

void Camera::UpdateCarCam(
	const CarState& carState, const BallState& ballState,
	bool inBallCam,
	float deltaTime,
	float distance,
	float height,
	float aboveCarHeight
) {
	
	Vec camDir;
	if (inBallCam) {
		camDir = ((ballState.pos - this->pos) * Vec(1, 1, 0)).Normalized();
	} else {
		Vec oldDir = ((carState.pos - this->pos) * Vec(1, 1, 0)).Normalized();

		if (carState.vel.Length() > 10) {
			Vec targetDir = carState.vel * Vec(1, 1, 0.5f);
			targetDir = targetDir.Normalized();

			// TODO: Make parameter
			constexpr float LERP_SCALE = 1000.f;
			float lerpRatio = 1 - RS_CLAMP(LERP_SCALE * (deltaTime * deltaTime), 0, 1);
			camDir = (oldDir * lerpRatio) + (targetDir * (1 - lerpRatio));
		} else {
			camDir = oldDir;
		}
	}

	camDir *= Vec(1, 1, 0);
	camDir = camDir.Normalized();

	if (inBallCam) {
		// If the ball is above us, the camera starts to shift lower and get closer to the car
		// I refer to this as "leaning"
		// TODO: This is a lame approximation, in RL it seems to be just sphereical movement clamped to the ground

		Vec dirToBall = (ballState.pos - this->pos).Normalized();
		float leanScale = RS_MAX(dirToBall.z, 0);

		// Move camera down
		constexpr float LEAN_HEIGHT_SCALE = 1.0f;
		height *= 1 - leanScale * LEAN_HEIGHT_SCALE;

		// Move camera closer
		constexpr float
			LEAN_DIST_SCALE = 0.4f,
			LEAN_DIST_EXPONENT = 1.0f;
		distance *= 1 - powf(leanScale, LEAN_DIST_EXPONENT) * LEAN_DIST_SCALE;
	}

	Vec offset = -camDir * distance;
	offset.z += height;

	this->pos = (carState.pos + offset);
	
	if (inBallCam) {
		this->LookAt(ballState.pos);
	} else {
		this->LookAt(carState.pos + Vec(0, 0, aboveCarHeight));
	}
}