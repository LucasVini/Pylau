from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget
from PyQt5.QtGui import QOpenGLShader, QOpenGLShaderProgram
from PyQt5.QtCore import QTimer
from OpenGL.GL import *
import sys
import time
import math

vertex_shader_source = """
#version 330 core
layout (location = 0) in vec2 position;
out vec2 fragCoord;
void main()
{
    fragCoord = position;
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

fragment_shader_source = """
#version 330 core
uniform vec2 iResolution;
uniform float iTime;
out vec4 fragColor;

float random(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

// Função de ruído com movimento dinâmico
float movingNoise(vec2 uv) {
    float noise = 0.0;
    float scale = 0.02;
    float timeOffset = sin(iTime * 0.5) * 0.02;
    
    for (int i = -1; i <= 1; i++) {
        for (int j = -1; j <= 1; j++) {
            noise += random(uv + vec2(i, j) * scale + timeOffset);
        }
    }
    return noise / 9.0;
}

// Efeito de feixe de luz com variação no tempo
float lightBeam(vec2 coord, vec2 source, float intensity, float spread) {
    float dist = length(coord - source);
    float attenuation = exp(-dist * spread) * intensity;
    float flicker = 0.5 + 0.5 * sin(iTime * 2.0); // Oscilação suave da luz
    return attenuation * flicker;
}

void main()
{
    vec2 uv = gl_FragCoord.xy / iResolution.xy;
    vec3 backgroundColor = vec3(0.02, 0.04, 0.02); // Verde escuro
    
    // Fonte de luz centralizada no topo
    vec2 lightSource = vec2(iResolution.x * 0.5, iResolution.y * 1.1);
    
    // Parâmetros da luz
    float intensity = 1.0;
    float spread = 0.004;
    
    // Feixe de luz dinâmico
    float beam = lightBeam(gl_FragCoord.xy, lightSource, intensity, spread);
    vec3 lightEffect = vec3(0.1, 0.8, 0.3) * beam; // Verde brilhante
    
    // Ruído dinâmico aplicado suavemente
    float noise = movingNoise(uv);
    lightEffect *= mix(0.9, 1.1, noise);
    
    fragColor = vec4(backgroundColor + lightEffect, 1.0);
}
"""

class ShaderWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_time = time.time()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # Aproximadamente 60 FPS

    def initializeGL(self):
        self.program = QOpenGLShaderProgram()
        vertex_shader = QOpenGLShader(QOpenGLShader.Vertex)
        vertex_shader.compileSourceCode(vertex_shader_source)
        self.program.addShader(vertex_shader)
        fragment_shader = QOpenGLShader(QOpenGLShader.Fragment)
        fragment_shader.compileSourceCode(fragment_shader_source)
        self.program.addShader(fragment_shader)
        self.program.link()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        self.program.bind()
        
        iResolution = self.program.uniformLocation("iResolution")
        iTime = self.program.uniformLocation("iTime")
        
        self.program.setUniformValue(iResolution, self.width(), self.height())
        self.program.setUniformValue(iTime, float(time.time() - self.start_time))
        
        glBegin(GL_TRIANGLES)
        glVertex2f(-1, -1)
        glVertex2f(3, -1)
        glVertex2f(-1, 3)
        glEnd()
        
        self.program.release()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Efeito de Luz Aero Windows 7")
        self.setGeometry(100, 100, 800, 600)
        self.shader_widget = ShaderWidget(self)
        self.setCentralWidget(self.shader_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
