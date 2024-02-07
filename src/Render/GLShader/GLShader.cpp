#include "GLShader.h"

// Shoutout to https://www.youtube.com/watch?v=6ztUqU14Tyc (OpenGL shader tutorial by Jayanam)

GLuint LoadShaderFromStr(std::string shaderName, GLenum shaderType, std::string shaderSrc) {
	GLuint id = glCreateShader(shaderType);

	const GLchar* glStrPtr = shaderSrc.c_str();
	const GLint glStrLen = shaderSrc.size();
	glShaderSource(id, 1, &glStrPtr, &glStrLen);

	glCompileShader(id);

	for (int i = 0; i < 3; i++) {
		constexpr int statusIDs[3] = { GL_COMPILE_STATUS, GL_LINK_STATUS, GL_VALIDATE_STATUS };
		GLint result;
		glGetShaderiv(id, statusIDs[i], &result);

		if (!result) {
			int logLen;
			glGetShaderiv(id, GL_INFO_LOG_LENGTH, &logLen);

			std::string errorLogStr = std::string(logLen, NULL);
			glGetShaderInfoLog(id, logLen, &logLen, errorLogStr.data());
			RS_ERR_CLOSE("Failed to load shader \"" << shaderName << "\": " << errorLogStr);
		}
	}

	return id;
}

GLShader::GLShader(std::string vertexShaderPath, std::string fragmentShaderPath, std::string geometryShaderPath) {
	std::string shaderPaths[3] = { vertexShaderPath, fragmentShaderPath, geometryShaderPath };
	int shaderTypes[3] = { GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_GEOMETRY_SHADER };
	GLuint* shaderIDs[3] = { &this->vertShaderID, &this->fragShaderID, &this->geomShaderID };
	for (int i = 0; i < 3; i++) {
		std::ifstream shaderFile = std::ifstream(shaderPaths[i]);
		assert(shaderFile.good());

		std::stringstream shaderStream;
		shaderStream << shaderFile.rdbuf();
		*shaderIDs[i] = LoadShaderFromStr(shaderPaths[i], shaderTypes[i], shaderStream.str());
	}
}

void GLShader::AttachToProgram(GLuint programID) {
	glAttachShader(programID, vertShaderID);
	glAttachShader(programID, fragShaderID);
	glAttachShader(programID, geomShaderID);
}

GLShader::~GLShader() {
	if (vertShaderID != NULL)
		glDeleteShader(vertShaderID);
	if (fragShaderID != NULL)
		glDeleteShader(fragShaderID);
	if (geomShaderID != NULL)
		glDeleteShader(geomShaderID);
}