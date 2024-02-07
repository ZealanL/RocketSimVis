#version 400

layout (triangles) in;
layout (triangle_strip) out;
layout (max_vertices = 3) out;

in VD {
	vec3 normal;
	vec3 cameraNormal;
	vec4 vertColor;
	vec4 worldPos;
} inData[];

out FD {
	vec3 normal;
	vec3 cameraNormal;
	vec4 vertColor;
	vec4 worldPos;
} outData;

in vec2 windowPosition[];
noperspective out vec3 distanceToEdges;

float og_distanceToLine(vec2 f, vec2 p0, vec2 p1) {
    vec2 l = f - p0;
    vec2 d = p1 - p0;

    vec2 p = p0 + (d * (dot(l, d) / dot(d, d)));
    return distance(f, p);
}

void main(void) {

	vec2 p0 = windowPosition[0];
    vec2 p1 = windowPosition[1];
    vec2 p2 = windowPosition[2];

    for (int i = 0; i < 3; i++) {
	
		outData.normal = inData[i].normal;
		outData.cameraNormal = inData[i].cameraNormal;
		outData.vertColor = inData[i].vertColor;
		outData.worldPos = inData[i].worldPos;

        gl_Position = gl_in[i].gl_Position;
		if (i == 0) {
			distanceToEdges = vec3(og_distanceToLine(p0, p1, p2), 0.0, 0.0);
		} else if (i == 1) {
			distanceToEdges = vec3(0.0, og_distanceToLine(p1, p2, p0), 0.0);
		} else {
			distanceToEdges = vec3(0.0, 0.0, og_distanceToLine(p2, p0, p1));
		}
        EmitVertex();
    }
    //EndPrimitive();
}