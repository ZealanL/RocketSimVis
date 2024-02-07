#version 400

in FD {
	vec3 normal;
	vec3 cameraNormal;
	vec4 vertColor;
	vec4 worldPos;
} inData;

out vec4 color;

uniform vec4 globalModelColor;
uniform bool enableShaders;
uniform bool enableArenaColoring;

noperspective in vec3 distanceToEdges;

void main() {

	if (enableShaders) {
		if (enableArenaColoring) {
			vec4 orange = vec4(1, 0.5, 0, 1);
			vec4 blue = vec4(0, 0.3, 1, 1);
			float ratio = inData.worldPos.y / 5000;
			vec3 arenaCol = vec3(0, 0.5, 0);
			
			if (ratio > 0) {
				ratio = ratio*ratio;
				arenaCol.r = ratio;
				arenaCol.g = ratio/2;
			} else if (ratio < 0) {
				ratio = ratio*ratio;
				arenaCol.b = ratio;
				arenaCol.g = ratio/3;
			}
			arenaCol.r = max(arenaCol.r, 0.2);
			arenaCol.g = max(arenaCol.g, 0.2);
			arenaCol.b = max(arenaCol.b, 0.2);
			
			color = vec4(arenaCol.x, arenaCol.y, arenaCol.z, 1) * inData.vertColor;
		} else {

			if (inData.vertColor.w > 0.99) { // Only do lighting when full alpha
				// Hardcoded lighting lol
				vec3 sunLightDir = normalize(vec3(-0.3, 0.2, -1));
				vec3 sunLightColor = vec3(1, 1, 0.8);
				
				vec3 ambientLightDir = normalize(vec3(1, 1, 1));
				vec3 ambientLightColor = vec3(0.1, 0.2, 0.3);
				
				float sunLightScale = dot(sunLightDir, -inData.normal) / 2 + 0.5;
				float ambientLightScale = dot(ambientLightDir, -inData.normal) / 2 + 0.5;
				
				vec3 baseColor = inData.vertColor.xyz * ((sunLightColor * sunLightScale) + (ambientLightColor * ambientLightScale));
				color = vec4(baseColor.x, baseColor.y, baseColor.z + 0.1, inData.vertColor.w) * globalModelColor;
			} else {
				color = inData.vertColor;
			}
		}
	} else {
		color = globalModelColor;
	}
}