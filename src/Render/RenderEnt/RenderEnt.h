#pragma once
#include "../../Framework.h"

struct RenderEnt {
	struct State {
		Vec pos = {};
		RotMat rot = {};
	};

	State prev, cur, next;
	float lastInterval;
	float timeSinceUpdate;

	static constexpr float MAX_INTERP_TIME = 0.2f;

	RenderEnt(State initialState);
	RenderEnt() : RenderEnt(State()) {}

	void Step(float deltaTime);
	void Update(State newState);

	void Update(const CarState& state) {
		Update(State(state.pos, state.rotMat));
	}

	void Update(const BallState& state) {
		Update(State(state.pos, state.rotMat));
	}

	void ApplyToState(CarState& state) {
		state.pos = cur.pos;
		state.rotMat = cur.rot;
	}

	void ApplyToState(BallState& state) {
		state.pos = cur.pos;
		state.rotMat = cur.rot;
	}
};