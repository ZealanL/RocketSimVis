#pragma once
#include "../../Framework.h"
#include "../../Color.h"

#include <gl/glew.h>

struct Model {

	struct MaterialColors {
		Color defaultColor;
		std::map<std::string, Color> otherColors;

		MaterialColors(Color defaultColor = Color(1, 1, 1)) : defaultColor(defaultColor) {}
	};

	struct Vertex {
		float x, y, z;

		float& operator[](uint32_t index) {
			assert(index >= 0 && index < 3);
			return ((float*)(this))[index];
		}

		float operator[](uint32_t index) const {
			assert(index >= 0 && index < 3);
			return ((float*)(this))[index];
		}

		float Distance(const Vertex& other) const {
			float sqDist = 0;
			for (int i = 0; i < 3; i++) {
				float d = (*this)[i] - other[i];
				sqDist += d * d;
			}

			return sqrtf(sqDist);
		}
	};

	struct Tri {
		int
			vertIdx[3] = { -1, -1, -1 },
			normIdx[3] = { -1, -1, -1 },
			texIdx[3] = { -1, -1, -1 };

		Color col = Color(1, 1, 1);
	};

	struct TexCoord {
		float x, y;

		float& operator[](uint32_t index) {
			assert(index >= 0 && index < 2);
			return ((float*)(this))[index];
		}
	};

	std::vector<Vertex> vertices;
	std::vector<Vertex> normals;
	std::vector<TexCoord> texCoords;

	std::vector<Tri> triangles;
	
	struct {
		GLuint
			triCount = 0;

		GLuint
			vertsID = -1,
			normsID = -1,
			colsID = -1;
	} vbos;
	

	bool IsLoadedIntoGL() {
		return vbos.triCount > 0;
	}

	Model() = default;

	// No copy constructor
	Model(const Model& other) = delete;

	void ReadFromOBJ(std::string filePath, MaterialColors colors, float scale = 1);
	void SetAllColors(Color color);
	void LoadIntoGL();
	void Render(glm::mat4 modelMat, GLuint modelMatID);

	~Model();
};