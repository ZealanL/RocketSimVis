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
		float heightAdjustment = RS_CLAMP((carState.pos.z - ballState.pos.z) / 5, -height, height / 2);
		//height += heightAdjustment;
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