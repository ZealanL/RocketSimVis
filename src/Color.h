#pragma once
#include "Framework.h"

struct Color {
	float
		r = 0,
		g = 0,
		b = 0,
		a = 1.f;

	constexpr Color(float r = 0, float g = 0, float b = 0, float a = 1) : r(r), g(g), b(b), a(a) {}
};