import sys
import ctypes
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint
import ollama

# Estruturas para o efeito de blur
class ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("Flags", ctypes.c_int),
        ("GradientColor", ctypes.c_int),
        ("AnimationId", ctypes.c_int),
    ]

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(ACCENTPOLICY)),
        ("SizeOfData", ctypes.c_size_t),
    ]

def enable_blur_effect(hwnd):
    """Aplica o efeito de blur acrílico em uma janela."""
    accent = ACCENTPOLICY()
    accent.AccentState = 3  # Blur acrílico
    accent.GradientColor = 0xD0000000  # Fundo transparente

    accent_data = ctypes.pointer(accent)
    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attribute = 19
    data.Data = accent_data
    data.SizeOfData = ctypes.sizeof(accent)

    ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))


class ChatApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Configurações da janela
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 600)
        self.setWindowTitle("Chat com IA")

        # Layout principal
        layout = QVBoxLayout()

        # Área de exibição do chat
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.2);
            font-family: Impact;
            font-size: 14px;
            color: white;
            border: none;
        """)
        layout.addWidget(self.chat_display)

        # Layout para entrada do usuário
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Digite sua mensagem aqui...")
        self.input_field.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.3);
            font-family: Impact;
            font-size: 14px;
            color: white;
            border: 1px solid white;
            border-radius: 5px;
        """)
        # Conectar Enter para enviar mensagem
        self.input_field.returnPressed.connect(self.handle_send_message)
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Enviar", self)
        self.send_button.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.3);
            font-family: Arial;
            font-size: 14px;
            color: white;
            border: 1px solid white;
            border-radius: 5px;
        """)
        self.send_button.clicked.connect(self.handle_send_message)
        input_layout.addWidget(self.send_button)

        self.exit_button = QPushButton("Sair", self)
        self.exit_button.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.3);
            font-family: Arial;
            font-size: 14px;
            color: white;
            border: 1px solid white;
            border-radius: 5px;
        """)
        self.exit_button.clicked.connect(self.close)
        input_layout.addWidget(self.exit_button)

        layout.addLayout(input_layout)

        # Status
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: lightgray; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Variáveis para exibição ao vivo
        self.full_response = ""
        self.current_index = 0
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.show_typing_effect)

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = self.winId().__int__()  # Obtém o identificador da janela
        enable_blur_effect(hwnd)

        # Centraliza a janela no pai (se houver)
        if self.parent():
            parent_geom = self.parent().geometry()
            x = parent_geom.x() + (parent_geom.width() - self.width()) // 2
            y = parent_geom.y() + (parent_geom.height() - self.height()) // 2
            self.move(x, y)

    def handle_send_message(self):
        user_message = self.input_field.text().strip()
        if user_message:
            # Exibe a mensagem do usuário no chat
            self.chat_display.append(f"<b>Você:</b> {user_message}")
            self.input_field.clear()
            self.status_label.setText("Processando resposta...")

            # Faz a chamada ao modelo da IA
            try:
                response = ollama.chat(
                    model='qwen2.5:0.5b',
                    messages=[{'role': 'user', 'content': user_message}]
                )
                self.full_response = response['message']['content']
                self.current_index = 0
                self.chat_display.append("<b>IA:</b> ")  # Inicia a resposta
                self.typing_timer.start(50)  # Controla a velocidade de digitação
            except Exception as e:
                self.chat_display.append(f"<b>Erro:</b> Não foi possível obter a resposta.")
                self.status_label.setText("Erro na comunicação com a IA.")
                print(f"Erro: {e}")

    def show_typing_effect(self):
        # Mostra o texto da resposta letra por letra
        if self.current_index < len(self.full_response):
            self.chat_display.insertPlainText(self.full_response[self.current_index])
            self.chat_display.ensureCursorVisible()
            self.current_index += 1
        else:
            # Para o timer ao concluir a exibição
            self.typing_timer.stop()
            self.status_label.setText("Pronto.")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Simulando uma janela principal do PyLau
    main_window = QWidget()

    # Criando a janela de chat
    chat_app = ChatApp(parent=main_window)
    chat_app.show()

    sys.exit(app.exec_())
