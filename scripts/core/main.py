#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel, QPushButton, QWidget, QMessageBox
import subprocess
import os
import sys

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.analysis.assembly_sc2 import ViralFlowGUI  # Importa o script para configuração do pipeline
from scripts.analysis.assembly_custom import ViralFlowGUI  # Importa o script para configuração do pipeline
from scripts.utilities.update_database import atualizar_banco_dados  # Função para atualizar banco de dados
from scripts.utilities.update_viralflow import atualizar_viralflow  # Função para atualizar viralflow


class MenuInicial(QWidget):
    def __init__(self):
        super().__init__()

        # Configurações da janela
        self.setWindowTitle("Menu Inicial - ViralFlow GUI")
        self.setGeometry(200, 200, 600, 200)

        # Layout principal
        layout = QVBoxLayout()

        # Mensagem inicial
        label = QLabel("Escolha uma opção:")
        layout.addWidget(label)

        # Botão para atualizar banco de dados
        update_button = QPushButton("Atualizar ViralFlow")
        update_button.clicked.connect(self.atualizar_viralflow)
        layout.addWidget(update_button)

        # Botão para atualizar banco de dados
        update_button = QPushButton("Atualizar Banco de dados")
        update_button.clicked.connect(self.atualizar_banco_dados)
        layout.addWidget(update_button)


        # Botão para abrir a tela de Montagem Sars-CoV2
        assembly_button = QPushButton("Montagem SARS-CoV-2")
        assembly_button.clicked.connect(self.abrir_tela_assembly_sc2)
        layout.addWidget(assembly_button)

        # Botão para sair
        exit_button = QPushButton("Sair")
        exit_button.clicked.connect(self.sair)
        layout.addWidget(exit_button)

        self.setLayout(layout)



    def atualizar_viralflow(self):
        # Pergunta de confirmação antes de rodar o script
        confirm = QMessageBox.question(
            self,
            "Confirmação",
            "Você deseja atualizar o ViralFlow?\nIsso pode levar algum tempo.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            atualizar_viralflow()


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

    def abrir_tela_assembly_sc2(self):
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
            subprocess.run("exit", shell=True, check=True)
            QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    menu = MenuInicial()
    menu.show()
    sys.exit(app.exec_())
