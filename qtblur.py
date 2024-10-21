import sys
import ctypes
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

# Estrutura necessária para aplicar o efeito de blur/acrílico
class ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int)
    ]

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(ACCENTPOLICY)),  # Ponteiro para ACCENTPOLICY
        ("SizeOfData", ctypes.c_size_t)
    ]

# Função para ativar o efeito de blur/acrílico no Windows 11
def enable_blur_effect(hwnd):
    accent = ACCENTPOLICY()
    accent.AccentState = 3  # 3 = Enable acrylic blur (ACCENT_ENABLE_ACRYLICBLURBEHIND)
    accent.GradientColor = 0xD0000000  # Cor de fundo transparente (D = alpha)

    # Criar um ponteiro para a estrutura ACCENTPOLICY
    accent_data = ctypes.pointer(accent)

    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attribute = 19  # 19 = Windows 10/11 specific blur effect (WCA_ACCENT_POLICY)
    data.Data = accent_data  # Passando o ponteiro para a estrutura
    data.SizeOfData = ctypes.sizeof(accent)

    hwnd_set_window_composition_attribute = ctypes.windll.user32.SetWindowCompositionAttribute
    hwnd_set_window_composition_attribute(hwnd, ctypes.byref(data))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuração da janela com fundo transparente
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Configuração do layout e conteúdo
        self.setMinimumSize(400, 300)
        layout = QVBoxLayout()

        # Adicionando um label com o texto
        label = QLabel("PyLAU 1.0\nAutor: Lucas Vinicius\nDescrição: Ferramenta de testes After Release para gravadores de vídeo.", self)
        label.setStyleSheet("color: white; font-size: 24px;")
        label.setAlignment(Qt.AlignCenter)

        # Widget central com layout
        central_widget = QWidget(self)
        layout.addWidget(label)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def showEvent(self, event):
        # Ativar o efeito de blur/acrílico no Windows 10/11
        hwnd = ctypes.windll.user32.FindWindowW(None, self.windowTitle())
        enable_blur_effect(hwnd)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.setWindowTitle("Janela com fundo blur")
    window.show()

    sys.exit(app.exec_())
