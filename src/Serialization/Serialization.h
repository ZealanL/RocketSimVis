#pragma once
#include "../Framework.h"

namespace Serialization {
	constexpr uint32_t PREFIX_SIGNATURE = 0xA490E7B3;

	Vec DeserializeVec(DataStreamIn& in);
	RotMat DeserializeRot(DataStreamIn& in);
	bool DeserializeUpdateCar(Car* car, DataStreamIn& in);
	bool DeserializeUpdateArena(Arena* arena, DataStreamIn& in);
}