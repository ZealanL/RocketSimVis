# TODO: Having them hardcoded in strings kinda sucks for editing complex shaders

FRAG_SHADER_ARENA = '''
#version 400

uniform sampler2D Texture;
uniform vec3 ballPos;

in FD {
	vec3 vert;
	vec3 norm;
	vec2 text;
} inData;

in vec3 distanceToEdges;

out vec4 f_color;

void main() { 
    bool isFloor = inData.norm.z > 0.95;
    bool isCeil = inData.norm.z < -0.95;
    
    float ratio = clamp((inData.vert.y + 0.01) / 6000, -1, 1);

    float brightness = 0;
    float colRatio = 0.2 + sqrt(abs(ratio)) * 0.8;
    colRatio *= 0.75;
    
    vec3 arenaCol = vec3(0, 0, 0);
    if (ratio > 0) {
        arenaCol.r = colRatio;
        arenaCol.g = colRatio * 0.60;
    } else if (ratio < 0) {
        arenaCol.b = colRatio;
        arenaCol.g = colRatio * 0.55;
    }

    float min_col_val = 0.3;
    arenaCol.r = max(arenaCol.r, min_col_val);
    arenaCol.g = max(arenaCol.g, min_col_val);
    arenaCol.b = max(arenaCol.b, min_col_val);

    // Prevent color from becoming too dark when gray
    arenaCol = normalize(arenaCol) * max(length(arenaCol), 0.6);

    f_color = vec4(arenaCol.x, arenaCol.y, arenaCol.z, 1);

    float min_edge_dist = min(distanceToEdges.x, min(distanceToEdges.y, distanceToEdges.z));
    //f_color *= 1 / (1 + min_edge_dist * 0.2);

    float edge_ratio = 0.95 * float(min_edge_dist < 10);
    if (isFloor || isCeil)
        edge_ratio *= 0.7;
    
    float backlight = abs(inData.norm.y * 0.7 + inData.norm.x * 0.3) * 0.6 + 0.4;
    float light_ratio = min(backlight * 0.4 + (max(0, inData.norm.z)) * 0.2, 1);

    f_color.xyz *= light_ratio + edge_ratio * (1 - light_ratio);
    f_color.a = 1;
    f_color *= (1 + brightness);

    float ball_radius = 100;
    float circle_width = 10;
    float min_ball_circle_norm_z = 0.5;
    float min_fade_height = 300;
    float max_fade_height = 900;
    float max_height = 2000;
    if (inData.norm.z > min_ball_circle_norm_z) {
        if (inData.vert.z < ballPos.z - ball_radius) {

            float height_ratio = clamp((ballPos.z - min_fade_height) / (max_fade_height - min_fade_height), 0, 1);

            vec3 deltaToBall2D = (inData.vert - ballPos) * vec3(1, 1, 0);
            float distToBall2D = length(deltaToBall2D);
            float secondCircleSize = ball_radius + 100;//ball_radius * (ballPos.z / max_height);

            bool inFirstCircle = distToBall2D < ball_radius && distToBall2D > (ball_radius - circle_width);
            bool inSecondCircle = distToBall2D < secondCircleSize && distToBall2D > (secondCircleSize - circle_width);

            if (inFirstCircle)
                f_color += vec4(1, 1, 1, 1) * 0.5 * height_ratio;
            if (inSecondCircle)
                f_color += vec4(1, 1, 1, 1) * 0.25 * height_ratio;
        }
    }
}
 '''

FRAG_SHADER = '''
#version 400

// https://stackoverflow.com/questions/15095909/from-rgb-to-hsv-in-opengl-glsl
// All components are in the range [0...1], including hue.
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
uniform vec3 cameraPos;
uniform vec3 ballPos;
uniform vec4 globalColor;

in FD {
	vec3 vert;
	vec3 norm;
	vec2 text;
} inData;

out vec4 f_color;

void main() { 
    float distFromCam = length(cameraPos - inData.vert);
    vec3 normFromCam = normalize(cameraPos - inData.vert);
    float fresnelRatio = clamp(1 - dot(normFromCam, inData.norm), 0, 1);
    
    /* New experimental lighting that sucks
    vec3 hsv = rgb2hsv(baseColor.xyz);
    vec4 baseColor = texture(Texture, inData.text).rgba;
    //hsv[0] = mod(hsv[0] - 0.05, 1);
    vec4 baseColorShifted = vec4(hsv2rgb(hsv), baseColor[3]);
    
    fresnelRatio *= fresnelRatio;
    vec3 color = baseColor.xyz * (1-fresnelRatio) + baseColorShifted.xyz * fresnelRatio;

    float upFrac = (inData.norm.z + 1) / 2;
    float litFrac = pow(upFrac, 2);
    
    vec3 litColor = color * litFrac;
    vec3 unlitColor = color * (1 - litFrac) * vec3(0.9, 0.95, 1.0) * 0.5;

    f_color = vec4(litColor + unlitColor, baseColor.a);
    */
    
    vec4 vertColor = texture(Texture, inData.text).rgba;
    vec3 hsv = rgb2hsv(vertColor.xyz);
    vec3 sunLightDir = normalize(vec3(-0.3, 0.2, -1)) + normFromCam * 0.0001;
    vec3 sunLightColor = vec3(1, 1, 0.8);
            
    vec3 ambientLightDir = normalize(vec3(1, 1, 1));
    vec3 ambientLightColor = vec3(0.1, 0.15, 0.2) * 2;
            
    float sunLightScale = pow(dot(sunLightDir, -inData.norm) / 2 + 0.5, 2) + fresnelRatio * 0.01;
    float ambientLightScale = dot(ambientLightDir, -inData.norm) / 2 + 0.5;
            
    vec3 baseColor = vertColor.xyz * ((sunLightColor * sunLightScale) + (ambientLightColor * ambientLightScale));
    float finalExp = 0.9;
    f_color = vec4(pow(baseColor, vec3(finalExp, finalExp, finalExp)), vertColor[3]);

    bool isVibrantColor = hsv[1] > 0.8f;
    if (isVibrantColor) {
        // Make vibrant colors less affected by lighting and "pop" more
        float distScale = 1 - (1 / ( 1 + (distFromCam / 900))); 
        distScale = 0;
        float vibrantScale = 0.2 + (0.7 * distScale);
        
        f_color = f_color*(1-vibrantScale) + vertColor*vibrantScale;
    }

    if (vertColor.a != 1) {
        f_color = vertColor;
    }
    
    if (globalColor != vec4(0,0,0,0)) {
        f_color = globalColor;
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

out vec3 distanceToEdges;

float og_distanceToLine(vec3 f, vec3 p0, vec3 p1) {
    vec3 l = f - p0;
    vec3 d = p1 - p0;

    vec3 p = p0 + (d * (dot(l, d) / dot(d, d)));
    return distance(f, p);
}

void main() {
	//vec3 p0 = inData[0].vert;
    //vec3 p1 = inData[1].vert;
    //vec3 p2 = inData[2].vert;

    vec3 p0 = gl_in[0].gl_Position.xyz;
    vec3 p1 = gl_in[1].gl_Position.xyz;
    vec3 p2 = gl_in[2].gl_Position.xyz;

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

noperspective out vec2 windowPosition;

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
    windowPosition = in_position.xy;
}
'''