import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer
import ollama

class ChatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Chat com IA")
        self.setGeometry(200, 200, 500, 600)

        # Layout principal
        layout = QVBoxLayout()

        # Área de exibição do chat
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background-color: #f0f0f0;
            font-family: Arial;
            font-size: 14px;
        """)
        layout.addWidget(self.chat_display)

        # Layout para entrada do usuário
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Digite sua mensagem aqui...")
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Enviar", self)
        self.send_button.clicked.connect(self.handle_send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        # Status
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Variáveis para exibição ao vivo
        self.full_response = ""
        self.current_index = 0
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.show_typing_effect)

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

            self.status_label.setText("Pronto.")

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
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec_())
