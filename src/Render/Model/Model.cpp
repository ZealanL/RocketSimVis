#include "Model.h"

void Model::ReadFromOBJ(string filePath, MaterialColors colors, float scale) {
	constexpr char ERROR_MSG_BASE[] = "Model::ReadFromOBJ(): ";

	assert(vertices.empty());
	assert(triangles.empty());

	std::ifstream fileStream = std::ifstream(filePath);
	assert(fileStream.good());

	Color curColor = colors.defaultColor;

	string line;
	while (std::getline(fileStream, line)) {
		if (line.length() < 7)
			continue; // Cannot possibly be a vertex/face

		std::stringstream lineStream = std::stringstream(line);
		string lineType;
		lineStream >> lineType;

		if (lineType == "v") { // Vertex
			Vertex vert;
			string curPart;
			for (int i = 0; lineStream >> curPart; i++) {
				vert[i] = std::stof(curPart) * scale;
			}

			this->vertices.push_back(vert);

		} else if (lineType == "f") { // Face
			Tri tri;
			string curPart;
			
			for (int i = 0; lineStream >> curPart; i++) {
				if (i > 2) {
					RS_ERR_CLOSE(
						ERROR_MSG_BASE << "Model has a face with more than 3 points! " <<
						"Not allowed, please only use triangulated meshes."
					);
				}

				// Forward slashes seperate vertex index, texture coordinate index, and normal index
				std::stringstream coordStream = std::stringstream(curPart);
				string curSubPart;
				int j;
				for (j = 0; j < 3 && std::getline(coordStream, curSubPart, '/'); j++) {
					uint32_t idxVal = std::stoul(curSubPart) - 1; // NOTE: OBJ indexes start at 1

					switch (j) {
					case 0: // Vertex index
						tri.vertIdx[i] = idxVal;
						break;
					case 1: // Texture coordinate index
						tri.texIdx[i] = idxVal;
						break;
					case 2: // Normal index
						tri.normIdx[i] = idxVal;
						break;
					}
				}

				if (j < 3) {
					RS_ERR_CLOSE(
						ERROR_MSG_BASE << "Model doesn't have normals and texture coordinates included! " <<
						"These are required parameters for RocketSimVis, please include them in the OBJ."
					);
				}
			}

			tri.col = curColor;
			this->triangles.push_back(tri);

		} else if (lineType == "vn") { // Vertex normal
			Vertex vertNorm;
			string curPart;
			for (int i = 0; lineStream >> curPart; i++) {
				vertNorm[i] = std::stof(curPart);
			}

			this->normals.push_back(vertNorm);
		} else if (lineType == "vt") { // Vertex texture coordinate
			TexCoord vertTexCoord;
			string curPart;
			for (int i = 0; lineStream >> curPart; i++) {
				vertTexCoord[i] = std::stof(curPart);
			}

			this->texCoords.push_back(vertTexCoord);
		} else if (lineType == "usemtl") { // Change material
			string matName;
			lineStream >> matName;
			
			if (colors.otherColors.find(matName) == colors.otherColors.end()) {
				curColor = colors.defaultColor;
			} else {
				curColor = colors.otherColors[matName];
			}
		}
	}

#ifdef _DEBUG
	// Validate model
	for (Tri& tri : triangles) {
		for (int i = 0; i < 3; i++) {
			if (tri.vertIdx[i] >= vertices.size()) {
				RS_ERR_CLOSE(ERROR_MSG_BASE <<
					"Model has out-of-bounds vertex index (" <<
					tri.vertIdx[i] << "/" << (vertices.size() - 1) << ")"
				);
			}

			if (tri.texIdx[i] >= texCoords.size()) {
				RS_ERR_CLOSE(ERROR_MSG_BASE <<
					"Model has out-of-bounds texture coordinate index (" <<
					tri.texIdx[i] << "/" << (texCoords.size() - 1) << ")"
				);
			}

			if (tri.normIdx[i] >= normals.size()) {
				RS_ERR_CLOSE(ERROR_MSG_BASE <<
					"Model has out-of-bounds normal index (" <<
					tri.normIdx[i] << "/" << (normals.size() - 1) << ")"
				);
			}
		}
	}
#endif
}

void Model::SetAllColors(Color color) {
	assert(!IsLoadedIntoGL());
	for (Tri& triangle : triangles)
		triangle.col = color;
}

void Model::LoadIntoGL() {
	// Generate VBOs
	glGenBuffers(1, &vbos.vertsID);
	glGenBuffers(1, &vbos.normsID);
	glGenBuffers(1, &vbos.colsID);

	// Set triangle count
	vbos.triCount = triangles.size();

	// Use verticies and faces to make an array of ordered triplet of verticies
	vector<Vertex> triVertData;
	vector<Vertex> triNormData;
	vector<Color> vertColData;
	triVertData.reserve(vbos.triCount * 3);
	triNormData.reserve(vbos.triCount * 3);
	vertColData.reserve(vbos.triCount * 3);
	for (Tri& tri : triangles) {
		for (int i = 0; i < 3; i++) {
			triVertData.push_back(
				vertices[tri.vertIdx[i]]
			);
			triNormData.push_back(
				normals[tri.normIdx[i]]
			);
			vertColData.push_back(
				tri.col
			);
		}
	}

	// Copy data to VBO
	assert(!triVertData.empty());
	assert(!triNormData.empty());
	assert(!vertColData.empty());
	glBindBuffer(GL_ARRAY_BUFFER, vbos.vertsID);
	glBufferData(GL_ARRAY_BUFFER, triVertData.size() * sizeof(Vertex), triVertData.data(), GL_STATIC_DRAW);
	glBindBuffer(GL_ARRAY_BUFFER, vbos.normsID);
	glBufferData(GL_ARRAY_BUFFER, triNormData.size() * sizeof(Vertex), triNormData.data(), GL_STATIC_DRAW);
	glBindBuffer(GL_ARRAY_BUFFER, vbos.colsID);
	glBufferData(GL_ARRAY_BUFFER, vertColData.size() * sizeof(Color), vertColData.data(), GL_STATIC_DRAW);

	// Reset bound buffer
	glBindBuffer(GL_ARRAY_BUFFER, NULL);
}

void Model::Render(glm::mat4 modelMat, GLuint modelMatID) {

	assert(IsLoadedIntoGL());

	static bool first = true;
	if (first) {
		first = false;

		// Enable attribute array for vertices at index 0
		glEnableVertexAttribArray(0);

		// Enable attribute array for normals at index 1
		glEnableVertexAttribArray(1);

		// Enable attribute array for normals at index 2
		glEnableVertexAttribArray(2);
	}

	// Load vertices attribute buffer, index 0
	glBindBuffer(GL_ARRAY_BUFFER, vbos.vertsID);
	glVertexAttribPointer(
		0,                  // Attribute index
		3,                  // Size
		GL_FLOAT,           // Type
		GL_FALSE,           // Normalized?
		0,                  // Stride (if not tightly packed)
		0					// Offset in array
	);

	// Load normals attribute buffer, index 1
	glBindBuffer(GL_ARRAY_BUFFER, vbos.normsID);
	glVertexAttribPointer(
		1,                  // Attribute index
		3,                  // Size
		GL_FLOAT,           // Type
		GL_FALSE,           // Normalized?
		0,                  // Stride (if not tightly packed)
		0					// Offset in array
	);

	// Load face colors attribute buffer, index 2
	glBindBuffer(GL_ARRAY_BUFFER, vbos.colsID);
	glVertexAttribPointer(
		2,                  // Attribute index
		4,                  // Size
		GL_FLOAT,           // Type
		GL_FALSE,           // Normalized?
		0,                  // Stride (if not tightly packed)
		0					// Offset in array
	);

	// Load model matrix
	glUniformMatrix4fv(modelMatID, 1, GL_FALSE, &modelMat[0][0]);

	// Draw triangles
	glDrawArrays(GL_TRIANGLES, 0, vbos.triCount * 3 * 3);

	// Reset bound buffer
	glBindBuffer(GL_ARRAY_BUFFER, NULL);
}

Model::~Model() {
	if (vbos.vertsID != NULL)
		glDeleteBuffers(1, &vbos.vertsID);
	if (vbos.normsID != NULL)
		glDeleteBuffers(1, &vbos.normsID);
	if (vbos.colsID != NULL)
		glDeleteBuffers(1, &vbos.colsID);
}