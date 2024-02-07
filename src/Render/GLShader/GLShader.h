#pragma once
#include "../../Framework.h"

struct GLShader {
	GLuint
		vertShaderID = NULL,
		fragShaderID = NULL,
		geomShaderID = NULL;
		
	GLShader(std::string vertexShaderPath, std::string fragmentShaderPath, std::string geometryShaderPath);
	GLShader(const GLShader& other) = delete;
	~GLShader();

	void AttachToProgram(GLuint programID);
};