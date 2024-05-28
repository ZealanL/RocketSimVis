# TODO: Having them hardcoded in strings kinda sucks for editing complex shaders

FRAG_SHADER = '''
#version 330

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

    if (vertColor.a != 1)
        f_color = vertColor;
    
    if (globalColor != vec4(0,0,0,0))
        f_color = globalColor;
    
}
 '''

VERT_SHADER = '''
#version 330

uniform mat4 m_vp;
uniform mat4 m_model;

in vec3 in_position;
in vec4 in_normal;
in vec2 in_texcoord_0;

out FD {
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