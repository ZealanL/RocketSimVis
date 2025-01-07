# All are modified versions of http://www.geoffprewett.com/blog/software/opengl-outline/index.html

UNLIT_VERT_SHADER = '''
#version 330

uniform mat4 m_vp;
uniform mat4 m_model;

in vec4 in_position;
in vec3 in_color;

void main() {
    gl_Position = m_vp * m_model * in_position;
}
'''

UNLIT_FRAG_SHADER = '''
#version 330

uniform vec4 color;

out vec4 out_color;

void main() {
    out_color = color;
}
'''

BLUR_VERT_SHADER = '''
#version 330

in vec2 in_position;
out vec2 texCoord;
void main() {
    texCoord = in_position;
    // pos ranges from [(0, 0), (1, 1)], so we need to convert to OpenGL’s
    // native coordinates of [(-1, -1], (1, 1)].
    gl_Position = vec4(2.0 * in_position.x - 1.0, 2.0 * in_position.y - 1.0, 0.0, 1.0);
}
'''

BLUR_FRAG_SHADER = '''
#version 330

uniform sampler2D texture;

uniform vec2 pixelSize;
in vec2 texCoord;

out vec4 out_color;

void main()
{
    vec4 color = texture2D(texture, texCoord);
    const int WIDTH = 1;
    bool isInside = false;
    int count = 0;
    float coverage = 0.0;
    float dist = 1e6;
    for (int y = -WIDTH;  y <= WIDTH;  ++y) {
        for (int x = -WIDTH;  x <= WIDTH;  ++x) {
            vec2 dUV = vec2(float(x) * pixelSize.x, float(y) * pixelSize.y);
            vec4 textureColor = texture2D(texture, texCoord + dUV);
            float mask = textureColor.a;
            coverage += mask;
            if (mask >= 0.5) {
                dist = min(dist, sqrt(float(x * x + y * y)));
                
                for (int i = 0; i < 4; i++)
                    color[i] = max(color[i], textureColor[i]);
            }
            if (x == 0 && y == 0) {
                isInside = (mask > 0.5);
                if (isInside)
                    color = textureColor;
            }
            count += 1;
        }
    }
    coverage /= float(count);
    float a;
    if (isInside) {
        a = min(1.0, (1.0 - coverage) / 0.75);
    } else {
        const float solid = 0.7 * float(WIDTH);
        const float fuzzy = float(WIDTH) - solid;
        a = 1.0 - min(1.0, max(0.0, dist - solid) / fuzzy);
    }
    
    color.a *= a;
    out_color = color;
}
'''