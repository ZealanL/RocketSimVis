#version 400

layout(location = 0)in vec4 l_vert;
layout(location = 1)in vec4 l_norm;
layout(location = 2)in vec4 l_vertCol;

out VD {
	vec3 normal;
	vec3 cameraNormal;
	vec4 vertColor;
	vec4 worldPos;
} outData;

out vec2 windowPosition;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

uniform bool enableShaders;

void main() {
	if (enableShaders) {
		gl_Position = projection * view * model * l_vert;
		
		mat4 modelRotOnly = model;
		for (int i = 0; i < 4; i++)
			for (int j = 0; j < 4; j++)
				if (i == 3 || j == 3)
					modelRotOnly[i][j] = (i == j) ? 1 : 0;
		
		outData.vertColor = l_vertCol;
		outData.normal = (modelRotOnly * l_norm).xyz;
		outData.cameraNormal = (projection * view * model * l_norm).xyz;
	} else {
		gl_Position = projection * view * l_vert;
	}
	windowPosition = gl_Position.xy;
	outData.worldPos = l_vert;
}