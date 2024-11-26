from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel, QPushButton, QWidget, QMessageBox
import subprocess
import sys
from assembly_sc2 import ViralFlowGUI  # Importa o script para configuração do pipeline
from update_database import atualizar_banco_dados  # Função para atualizar banco de dados


class MenuInicial(QWidget):
    def __init__(self):
        super().__init__()

        # Configurações da janela
        self.setWindowTitle("Menu Inicial - ViralFlow GUI")
        self.setGeometry(100, 100, 400, 200)

        # Layout principal
        layout = QVBoxLayout()

        # Mensagem inicial
        label = QLabel("Escolha uma opção:")
        layout.addWidget(label)

        # Botão para atualizar banco de dados
        update_button = QPushButton("Atualizar banco de dados")
        update_button.clicked.connect(self.atualizar_banco_dados)
        layout.addWidget(update_button)

        # Botão para abrir a tela de Montagem Sars-CoV2
        assembly_button = QPushButton("Montagem Sars-CoV2")
        assembly_button.clicked.connect(self.abrir_tela_assembly)
        layout.addWidget(assembly_button)

        # Botão para sair
        exit_button = QPushButton("Sair")
        exit_button.clicked.connect(self.sair)
        layout.addWidget(exit_button)

        self.setLayout(layout)

    def atualizar_banco_dados(self):
        # Pergunta de confirmação antes de rodar o script
        confirm = QMessageBox.question(
            self,
            "Confirmação",
            "Você deseja atualizar o banco de dados?\nIsso pode levar algum tempo.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            atualizar_banco_dados()

    def abrir_tela_assembly(self):
        # Fecha o menu inicial e abre a interface de configuração
        self.close()
        self.tela_assembly = ViralFlowGUI()
        self.tela_assembly.show()

    def sair(self):
        # Confirmação antes de sair
        confirm = QMessageBox.question(
            self,
            "Confirmação",
            "Tem certeza de que deseja sair?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    menu = MenuInicial()
    menu.show()
    sys.exit(app.exec_())
