from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget
from PyQt5.QtGui import QOpenGLShader, QOpenGLShaderProgram
from PyQt5.QtCore import QTimer, QPoint
from OpenGL.GL import *
import sys
import time

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
uniform vec2 iMouse;
uniform float iTime;
out vec4 fragColor;

float rand(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233) + iTime)) * 43758.5453);
}

void main() {
    vec2 uv = gl_FragCoord.xy / iResolution.xy;
    vec3 backgroundColor = vec3(0.02, 0.05, 0.02); // Fundo escuro esverdeado
    vec3 lightColor = vec3(0.4, 1.0, 0.4); // Verde vibrante mais claro
    vec3 whiteGlow = vec3(0.7, 1.0, 0.7); // Branco esverdeado suave

    // Posição do mouse normalizada
    vec2 mousePos = iMouse / iResolution.xy;

    // Distância do fragmento ao mouse
    float dist = length(uv - mousePos);

    // Ajuste para reduzir o brilho no epicentro
    float intensity = exp(-4.0 * dist) * (0.5 + 0.2 * sin(iTime * 2.0 + dist * 8.0));

    // Efeito de blur aumentado
    float blurEffect = exp(-10.0 * dist) * (0.4 + 0.2 * sin(iTime * 3.0 + rand(uv) * 3.5));
    
    // Redução do ruído em 30%
    if (rand(uv * 10.0) > 0.7) {
        blurEffect *= 0.3;
    }

    // Efeito de brilho esverdeado
    float glow = exp(-15.0 * dist) * 0.3;

    // Mistura dos efeitos
    vec3 color = mix(backgroundColor, lightColor, intensity);
    color = mix(color, whiteGlow, glow); // Brilho dinâmico esverdeado
    color += blurEffect; // Efeito de vidro Aero randomizado

    fragColor = vec4(color, 1.0);
}
"""

class ShaderWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_time = time.time()
        self.mouse_pos = QPoint(0, 0)
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
        iMouse = self.program.uniformLocation("iMouse")
        iTime = self.program.uniformLocation("iTime")
        
        self.program.setUniformValue(iResolution, self.width(), self.height())
        self.program.setUniformValue(iMouse, float(self.mouse_pos.x()), float(self.height() - self.mouse_pos.y()))
        self.program.setUniformValue(iTime, float(time.time() - self.start_time))
        
        glBegin(GL_TRIANGLES)
        glVertex2f(-1, -1)
        glVertex2f(3, -1)
        glVertex2f(-1, 3)
        glEnd()
        
        self.program.release()

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Efeito Aero Style - Shader")
        self.setGeometry(100, 100, 800, 600)
        self.shader_widget = ShaderWidget(self)
        self.setCentralWidget(self.shader_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())