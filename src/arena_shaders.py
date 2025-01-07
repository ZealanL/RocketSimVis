# TODO: Having them hardcoded in strings kinda sucks for editing complex shaders

ARENA_FRAG_SHADER = '''
#version 330

uniform sampler2D Texture;
uniform vec3 ballPos;

in FD {
	vec3 vert;
	vec3 norm;
	vec2 text;
	float edgeFrac;
} inData;

out vec4 f_color;

void main() { 
    bool isFloor = inData.norm.z > 0.95;
    bool isCeil = inData.norm.z < -0.95;

    float minRatio = 0.1f;
    float ratio = clamp((inData.vert.y + 1e-1) / 6000, -1, 1);
    if (abs(ratio) < minRatio)
        ratio = minRatio * sign(ratio);

    float colRatio = 0.2 + sqrt(abs(ratio)) * 0.8;
    colRatio *= 0.75;

    vec3 arenaCol = vec3(0, 0, 0);
    if (ratio > 0) {
        arenaCol.r = colRatio;
        arenaCol.g = colRatio * 0.65;
    } else if (ratio < 0) {
        arenaCol.b = colRatio;
        arenaCol.g = colRatio * 0.675;
    }

    float min_col_val = 0.35;
    arenaCol.r = max(arenaCol.r, min_col_val);
    arenaCol.g = max(arenaCol.g, min_col_val);
    arenaCol.b = max(arenaCol.b, min_col_val);

    // Prevent color from becoming too dark when gray
    arenaCol = normalize(arenaCol) * max(length(arenaCol), 0.6);

    f_color = vec4(arenaCol.x, arenaCol.y, arenaCol.z, 1);

    float edge_ratio = float(inData.edgeFrac);
    if (isFloor || isCeil)
        edge_ratio *= 0.7;

    float backlight = abs(abs(inData.norm.y) * 0.7 + abs(inData.norm.x) * 0.3) * 0.6 + 0.4;
    float light_ratio = min(backlight * 0.4 + (max(0, inData.norm.z)) * 0.2, 1);

    f_color.xyz *= light_ratio + edge_ratio * (1 - light_ratio);
    f_color.a = 1;

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

ARENA_GEOM_SHADER = '''
#version 330

layout (triangles) in;
layout (triangle_strip) out;
layout (max_vertices = 21) out;

uniform mat4 m_vp;
uniform mat4 m_model;

in VD {
	vec3 vert;
	vec3 norm;
	vec2 text;
} inData[];

out FD {
	vec3 vert;
	vec3 norm;
	vec2 text;
	float edgeFrac;
} outData;

out vec3 distanceToEdges;

float og_distanceToLine(vec3 f, vec3 p0, vec3 p1) {
    vec3 l = f - p0;
    vec3 d = p1 - p0;

    vec3 p = p0 + (d * (dot(l, d) / dot(d, d)));
    return distance(f, p);
}

void main() {
    vec3 p[3];
    for (int i = 0; i < 3; i++)
        p[i] = inData[i].vert;
    
    float wireframeWidth = 15; 
    bool doWireframe = true;
    
    // Minimum size of the 3 edges
    float minEdgeSize = 10;
    float edgeSize = min(length(p[0]-p[1]), min(length(p[1]-p[2]), length(p[2]-p[0])));
    if (edgeSize < minEdgeSize)
        doWireframe = false;
        
    wireframeWidth = min(wireframeWidth, edgeSize * 2);
        
    // Aveage position of the triangle
    vec3 center = (p[0] + p[1] + p[2]) / 3;
    
    // Inner points
    vec3 ip[3];
    for (int i = 0; i < 3; i++) {
        vec3 vert = inData[i].vert;
    
        vec3 deltaToCenter = center - vert;
        float distToCenter = length(deltaToCenter);
        vec3 dirToCenter = deltaToCenter / distToCenter;
        if (distToCenter < 1e-5)
            dirToCenter = vec3(0, 0, 0);
                
        vert += dirToCenter * wireframeWidth;
        ip[i] = vert;
    }
    
    if (doWireframe) {
        vec3 norm = (inData[0].norm + inData[1].norm + inData[2].norm) / 3;
        vec2 text = (inData[0].text + inData[1].text + inData[2].text) / 3;
        outData.norm = norm;
        outData.text = text;
        
        outData.edgeFrac = 0;
        {
            for (int i = 0; i < 3; i++) {
                
                outData.vert = ip[i];
                
                gl_Position = m_vp * m_model * vec4(outData.vert, 1);
                
                EmitVertex();
            }
            EndPrimitive();
        }
    
        outData.edgeFrac = 1;
        {
            vec3 ovs[4*3];
            for (int i = 0; i < 3; i++) {
                ovs[i*4 + 0] = p[(0 + i) % 3];
                ovs[i*4 + 1] = ip[(0 + i) % 3];
                ovs[i*4 + 2] = p[(2 + i) % 3];
                ovs[i*4 + 3] = ip[(2 + i) % 3];
            }
            
            for (int i = 0; i < 3; i++) {
                for (int j = 0; j < 4; j++) {
                    outData.vert = ovs[i * 4 + j];
                    
                    gl_Position = m_vp * m_model * vec4(outData.vert, 1);
                    
                    EmitVertex();
                }
                EndPrimitive();
            }
        }
    } else {
        for (int i = 0; i < 3; i++) {
            
            outData.vert = inData[i].vert;
            outData.norm = inData[i].norm;
            outData.text = inData[i].text;
            outData.edgeFrac = 0;
            
            gl_Position = m_vp * m_model * vec4(p[i], 1);
            
            EmitVertex();
        }
        EndPrimitive();
    }
    
    /*
    for (int itr = 0; itr < 2; itr++) {
        if (!doWireframe && itr == 0)
            continue;
    
        for (int i = 0; i < 3; i++) {
    
            vec3 vert = inData[i].vert;
    
            vec3 deltaToCenter = center - vert;
            float distToCenter = length(deltaToCenter);
            vec3 dirToCenter = deltaToCenter / distToCenter;
            if (distToCenter < 1e-5)
                dirToCenter = vec3(0, 0, 0);
            
            if (doWireframe && itr == 0) {
                vert += dirToCenter * wireframeWidth;
            }
            
            outData.vert = vert;
            outData.norm = inData[i].norm;
            outData.text = inData[i].text;
            outData.edgeFrac = float(itr == 1);
    
            gl_Position = m_vp * m_model * vec4(vert, 1);
            if (itr == 1) {
                gl_Position.z += 1e-2;
            }
            
            if (i == 0) {
                distanceToEdges = vec3(og_distanceToLine(p[0], p[1], p[2]), 0.0, 0.0);
            } else if (i == 1) {
                distanceToEdges = vec3(0.0, og_distanceToLine(p[1], p[2], p[0]), 0.0);
            } else {
                distanceToEdges = vec3(0.0, 0.0, og_distanceToLine(p[2], p[0], p[1]));
            }
            EmitVertex();
        }
        EndPrimitive();
    }
    */
}
'''

ARENA_VERT_SHADER = '''
#version 330

uniform mat4 m_vp;
uniform mat4 m_model;

in vec3 in_position;
in vec4 in_normal;
in vec2 in_texcoord_0;
in vec3 in_color;

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