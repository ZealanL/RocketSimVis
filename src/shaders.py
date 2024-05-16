# TODO: Having them hardcoded in strings kinda sucks for editing complex shaders

FRAG_SHADER = '''
#version 400

// https://stackoverflow.com/questions/15095909/from-rgb-to-hsv-in-opengl-glsl
// All components are in the range [0…1], including hue.
vec3 rgb2hsv(vec3 c)
{
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

// https://stackoverflow.com/questions/15095909/from-rgb-to-hsv-in-opengl-glsl
// All components are in the range [0...1], including hue.
vec3 hsv2rgb(vec3 c)
{
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

uniform sampler2D Texture;
uniform bool enableArenaColoring;
uniform vec3 cameraPos;
uniform vec4 globalColor;

in FD {
	vec3 vert;
	vec3 norm;
	vec2 text;
} inData;

out vec4 f_color;

void main() { 
    if (enableArenaColoring) {
        vec4 orange = vec4(1, 0.5, 0, 1);
        vec4 blue = vec4(0, 0.3, 1, 1);
        float ratio = clamp((inData.vert.y + 0.01) / 5000, -1, 1);
        vec3 arenaCol = vec3(0, 0.5, 0);
        
        if (ratio > 0) {
            ratio = sqrt(ratio);
            arenaCol.r = ratio;
            arenaCol.g = ratio/1.9;
        } else if (ratio < 0) {
            ratio = sqrt(-ratio);
            arenaCol.b = ratio;
            arenaCol.g = ratio/3;
        }
        arenaCol.r = max(arenaCol.r, 0.2);
        arenaCol.g = max(arenaCol.g, 0.2);
        arenaCol.b = max(arenaCol.b, 0.2);
        
        arenaCol.xyz *= 0.85;
        
        f_color = vec4(arenaCol.x, arenaCol.y, arenaCol.z, 1);
    } else {
        vec3 normFromCam = normalize(cameraPos - inData.vert);
    
        /* New experimental lighting that sucks
        vec4 baseColor = texture(Texture, inData.text).rgba;
        
        vec3 hsv = rgb2hsv(baseColor.xyz);
        //hsv[0] = mod(hsv[0] - 0.05, 1);
        vec4 baseColorShifted = vec4(hsv2rgb(hsv), baseColor[3]);
        
        float fresnelRatio = clamp(1 - dot(normFromCam, inData.norm), 0, 1);
        fresnelRatio *= fresnelRatio;
        vec3 color = baseColor.xyz * (1-fresnelRatio) + baseColorShifted.xyz * fresnelRatio;
    
        float upFrac = (inData.norm.z + 1) / 2;
        float litFrac = pow(upFrac, 2);
        
        vec3 litColor = color * litFrac;
        vec3 unlitColor = color * (1 - litFrac) * vec3(0.9, 0.95, 1.0) * 0.5;
    
        f_color = vec4(litColor + unlitColor, baseColor.a);
        */
        
        vec4 vertColor = texture(Texture, inData.text).rgba;
        vec3 sunLightDir = normalize(vec3(-0.3, 0.2, -1)) + normFromCam * 0.0001;
		vec3 sunLightColor = vec3(1, 1, 0.8);
				
		vec3 ambientLightDir = normalize(vec3(1, 1, 1));
		vec3 ambientLightColor = vec3(0.1, 0.2, 0.3);
				
		float sunLightScale = dot(sunLightDir, -inData.norm) / 2 + 0.5;
		float ambientLightScale = dot(ambientLightDir, -inData.norm) / 2 + 0.5;
				
		vec3 baseColor = vertColor.xyz * ((sunLightColor * sunLightScale) + (ambientLightColor * ambientLightScale));
		float finalExp = 0.9;
		f_color = vec4(pow(baseColor, vec3(finalExp, finalExp, finalExp)), vertColor[3]);
		
		if (globalColor != vec4(0,0,0,0)) {
		    f_color = globalColor;
		}
    }
}
 '''

GEOM_SHADER = '''
#version 400

layout (triangles) in;
layout (triangle_strip) out;
layout (max_vertices = 3) out;

in VD {
	vec3 vert;
	vec3 norm;
	vec2 text;
} inData[];

out FD {
	vec3 vert;
	vec3 norm;
	vec2 text;
} outData;

in vec2 windowPosition[];
noperspective out vec3 distanceToEdges;

float og_distanceToLine(vec2 f, vec2 p0, vec2 p1) {
    vec2 l = f - p0;
    vec2 d = p1 - p0;

    vec2 p = p0 + (d * (dot(l, d) / dot(d, d)));
    return distance(f, p);
}

void main() {
	vec2 p0 = windowPosition[0];
    vec2 p1 = windowPosition[1];
    vec2 p2 = windowPosition[2];

    for (int i = 0; i < 3; i++) {
        
        outData.vert = inData[i].vert;
        outData.norm = inData[i].norm;
        outData.text = inData[i].text;
    
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
'''

VERT_SHADER = '''
#version 400

uniform mat4 m_vp;
uniform mat4 m_model;

in vec3 in_position;
in vec4 in_normal;
in vec2 in_texcoord_0;

out VD {
	vec3 vert;
	vec3 norm;
	vec2 text;
} outData;

out vec2 windowPosition;

void main() {
    outData.vert = in_position;
    
    mat4 modelRot = m_model;
	for (int i = 0; i < 4; i++)
		for (int j = 0; j < 4; j++)
			if (i == 3 || j == 3)
				modelRot[i][j] = (i == j) ? 1 : 0;
    
    outData.norm = (modelRot * in_normal).xyz;
    outData.text = in_texcoord_0;
    gl_Position = m_vp * m_model * vec4(in_position, 1.0);
    windowPosition = gl_Position.xy;
}
'''