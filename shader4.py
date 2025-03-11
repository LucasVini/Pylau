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

mat2 rotate2D(float r) {
    return mat2(cos(r), sin(r), -sin(r), cos(r));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (fragCoord - 0.5 * iResolution.xy) / iResolution.y;
    vec3 col = vec3(0);
    float t = iTime;

    vec2 n = vec2(0), q;
    vec2 N = vec2(0);
    vec2 p = uv + sin(t * 0.1) / 10.;
    float S = 10.;
    mat2 m = rotate2D(1. - iMouse.x * 0.0001);

    for (float j = 0.; j < 30.; j++) {
        p *= m;
        n *= m;
        q = p * S + j + n + t;
        n += sin(q);
        N += cos(q) / S;
        S *= 1.2;
    }

    col = vec3(0.0, 1.0, 0.2) * pow((N.x + N.y + 0.2) + 0.005 / length(N), 2.1);
    fragColor = vec4(col, 1.0);
}

void main() {
    mainImage(fragColor, gl_FragCoord.xy);
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
        self.setWindowTitle("Shader Effect")
        self.setGeometry(100, 100, 800, 600)
        self.shader_widget = ShaderWidget(self)
        self.setCentralWidget(self.shader_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
