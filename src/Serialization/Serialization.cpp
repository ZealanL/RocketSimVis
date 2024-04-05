#include "Serialization.h"

Vec Serialization::DeserializeVec(DataStreamIn& in) {
	float x = in.Read<float>();
	float y = in.Read<float>();
	float z = in.Read<float>();
	return Vec(x, y, z);
}

RotMat Serialization::DeserializeRot(DataStreamIn& in) {
	Vec forward = DeserializeVec(in);
	Vec right = DeserializeVec(in);
	Vec up = DeserializeVec(in);
	return RotMat(forward, right, up);
}

bool Serialization::DeserializeUpdateCar(Car* car, DataStreamIn& in) {
	// Read car info
	uint8_t teamNum = in.Read<uint8_t>();
	if (teamNum > (uint8_t)Team::ORANGE) {
		throw std::exception("DeserializeUpdateCar(): Team number out of range");
		return false;
	}

	car->team = (Team)teamNum;

	// Read car state
	CarState carState = CarState();
	carState.pos = DeserializeVec(in);
	carState.rotMat = DeserializeRot(in);
	carState.vel = DeserializeVec(in);
	carState.angVel = DeserializeVec(in);
	float newBoost = in.Read<float>();
	bool boosting = newBoost < car->_internalState.boost;
	carState.boost = newBoost;
	carState.isDemoed = in.Read<uint8_t>();
	car->SetState(carState);

	// Read car controls
	car->controls.throttle = in.Read<float>();
	car->controls.boost = in.Read<uint8_t>();
	car->controls.boost = boosting;
	car->controls.jump = in.Read<uint8_t>();
	car->controls.handbrake = in.Read<uint8_t>();

	return true;
}

bool Serialization::DeserializeUpdateArena(Arena* arena, DataStreamIn& in) {
	constexpr const char* ERR_PREFIX = "DeserializeUpdateArena(): ";

	uint32_t prefixSig = in.Read<uint32_t>();
	if (prefixSig != PREFIX_SIGNATURE) {
#ifdef _DEBUG
		RS_LOG(ERR_PREFIX << "Recieved bad signature, ignoring");
#endif
		return false;
	}

	arena->tickCount = in.Read<uint32_t>();
	
	{ // Derialize cars
		uint32_t numCars = in.Read<uint32_t>();

		while (arena->_cars.size() > numCars) {
			arena->RemoveCar(*arena->_cars.begin());
		}

		while (arena->_cars.size() < numCars) {
			arena->AddCar(Team::BLUE);
		}

		auto carItr = arena->_cars.begin();
		for (int i = 0; i < numCars; i++) {
			if (!DeserializeUpdateCar(*carItr, in)) {
				return false;
			}
			carItr++;
		}
	}

	{ // Deserialize boost pads
		uint32_t boostPadAmount = in.Read<uint32_t>();

		if (boostPadAmount > 0) {
			if (boostPadAmount != arena->_boostPads.size())
				RS_ERR_CLOSE(ERR_PREFIX << "Invalid boost pad amount");

			for (int i = 0; i < boostPadAmount; i++) {
				Vec pos = DeserializeVec(in);

				BoostPadState state = {};
				state.isActive = in.Read<uint8_t>();
				state.cooldown = in.Read<float>();

				{ // Find and update our pad using boost pad grid
					int indexX = pos.x / BoostPadGrid::CELL_SIZE_X + (BoostPadGrid::CELLS_X / 2);
					int indexY = pos.y / BoostPadGrid::CELL_SIZE_Y + (BoostPadGrid::CELLS_Y / 2);

					if (RS_MIN(indexX, indexY) < 0
						|| indexX >= BoostPadGrid::CELLS_X || indexX >= BoostPadGrid::CELLS_Y)
						RS_ERR_CLOSE(ERR_PREFIX << "Invalid boost pad pos: " << pos);

					BoostPad* pad = arena->_boostPadGrid.pads[indexX][indexY];
					assert(pad);
					pad->SetState(state);
				}
			}
		} else {
			// No pads sent
			// Disable all pads in-game
			for (auto pad : arena->_boostPads)
				pad->_internalState.isActive = false;
		}
	}

	{ // Deserialize ball
		BallState ballState = BallState();
		ballState.pos = DeserializeVec(in);
		ballState.rotMat = DeserializeRot(in);
		ballState.vel = DeserializeVec(in);
		ballState.angVel = DeserializeVec(in);

		arena->ball->SetState(ballState);
	}

	if (in.IsOverflown()) {
		throw std::exception("DeserializeUpdateArena(): Input buffer overflowed");
		return false;
	} else if (in.GetNumBytesLeft() > 0) {
		throw std::exception("DeserializeUpdateArena(): Input buffer has bytes left");
		return false;
	} else {
		return true;
	}
}
