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
uniform float iTime;
out vec4 fragColor;

void mainImage( out vec4 o, vec2 u )
{
    vec2 v = iResolution.xy;
         u = .2*(u+u-v)/v.y;    
         
    vec4 z = o = vec4(1,2,3,0);
     
    for (float a = .5, t = iTime, i; 
         ++i < 19.; 
         o += (1. + cos(z+t)) 
            / length((1.+i*dot(v,v)) 
                   * sin(1.5*u/(.5-dot(u,u)) - 9.*u.yx + t))
         )  
        v = cos(++t - 7.*u*pow(a += .03, i)) - 5.*u,                 
        u += tanh(40. * dot(u *= mat2(cos(i + .02*t - vec4(0,11,33,0)))
                           ,u)
                      * cos(1e2*u.yx + t)) / 2e2
           + .2 * a * u
           + cos(4./exp(dot(o,o)/1e2) + t) / 3e2;
              
     o = 25.6 / (min(o, 13.) + 164. / o) 
       - dot(u, u) / 250.;
}

void main() {
    mainImage(fragColor, gl_FragCoord.xy);
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
        self.setWindowTitle("Shader Effect")
        self.setGeometry(100, 100, 800, 600)
        self.shader_widget = ShaderWidget(self)
        self.setCentralWidget(self.shader_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())