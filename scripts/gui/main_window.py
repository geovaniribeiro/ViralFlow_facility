#!/usr/bin/env python3

from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QLabel, QPushButton, QWidget, QMessageBox, QRadioButton
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import os
import sys
import matplotlib
matplotlib.use('Agg')  # Configura o backend sem GUI antes de qualquer uso do Matplotlib

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.gui.AssemblerRun_SC2 import ViralFlowGUI as ViralFlowGUI_SC2  # Interface para SARS-CoV-2
from scripts.gui.AssemblerRun_custom import ViralFlowGUI as ViralFlowGUI_custom  # Interface para vírus customizados
from scripts.utilities.update_database import atualizar_banco_dados  # Função para atualizar banco de dados
from scripts.utilities.update_viralflow import atualizar_viralflow  # Função para atualizar viralflow
from scripts.analysis.report.report_generator_denv import generate_report_denv  # Classe para geração de relatórios
from scripts.analysis.DenvNextclade import DenvNextclade # Classe para rodar DenvNext (genotyping e linhagem)

class WorkerThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.function(*self.args, **self.kwargs)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class MenuInicial(QWidget):
    def __init__(self):
        super().__init__()

        # Configurações da janela
        self.setWindowTitle("Menu Inicial - ViralFlow GUI")
        self.setGeometry(200, 200, 600, 300)

        # Define o ícone da janela
        self.setWindowIcon(QIcon(os.path.expanduser("~/ViralFlow/docs/source/img/viralflow_logo.png")))  # Substitua pelo caminho do ícone

        # Layout principal
        layout = QVBoxLayout()

        # Mensagem inicial
        label = QLabel("Escolha uma opção:")
        layout.addWidget(label)

        # Botão para atualizar ViralFlow
        update_button = QPushButton("Atualizar ViralFlow")
        update_button.clicked.connect(self.atualizar_viralflow)
        layout.addWidget(update_button)

        # Botão para atualizar banco de dados
        db_update_button = QPushButton("Atualizar Banco de dados")
        db_update_button.clicked.connect(self.atualizar_banco_dados)
        layout.addWidget(db_update_button)

        # Grupo de botões de seleção para vírus
        self.radio_sc2 = QRadioButton("SARS-CoV-2")
        self.radio_denv = QRadioButton("DENV")
        self.radio_outro_virus = QRadioButton("OUTRO VÍRUS")
        layout.addWidget(self.radio_sc2)
        layout.addWidget(self.radio_denv)
        layout.addWidget(self.radio_outro_virus)

        # Botão para confirmar
        confirm_button = QPushButton("Iniciar Análise")
        confirm_button.clicked.connect(self.executar_analise)
        layout.addWidget(confirm_button)

        # Botão para sair
        exit_button = QPushButton("Sair")
        exit_button.clicked.connect(self.sair)
        layout.addWidget(exit_button)

        self.setLayout(layout)

    def atualizar_viralflow(self):
        confirm = QMessageBox.question(self, "Confirmação", "Você deseja atualizar o ViralFlow?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.thread = WorkerThread(atualizar_viralflow)
            self.thread.error.connect(lambda msg: QMessageBox.critical(self, "Erro", msg))
            self.thread.start()

    def atualizar_banco_dados(self):
        confirm = QMessageBox.question(
            self,
            "Confirmação",
            "Você deseja atualizar o banco de dados?\nIsso pode levar algum tempo.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            atualizar_banco_dados()

    def executar_analise(self):
        if self.radio_sc2.isChecked():
            self.tela_assembly = ViralFlowGUI_SC2(self)
        elif self.radio_denv.isChecked():
            self.tela_assembly = ViralFlowDENV(self)
        elif self.radio_outro_virus.isChecked():
            self.tela_assembly = ViralFlowGUI_custom(self)
        else:
            QMessageBox.warning(self, "Atenção", "Selecione uma opção antes de continuar.")
            return

        self.thread = WorkerThread(self.tela_assembly.show)
        self.thread.error.connect(lambda msg: QMessageBox.critical(self, "Erro", msg))
        self.thread.start()

        self.close()

    def sair(self):
        confirm = QMessageBox.question(
            self,
            "Confirmação",
            "Tem certeza de que deseja sair?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            subprocess.run("exit", shell=True, check=True)
            QApplication.quit()



class ViralFlowDENV(ViralFlowGUI_custom):
    def __init__(self, menu_inicial=None):
        super().__init__(menu_inicial)
        self.menu_principal = menu_inicial  # Armazena referência do menu principal, se fornecida

    def report_generator(self, message):
        """Sobrescreve a finalização com lógica específica para DENV."""
        
        try:
            # Extrair os valores diretamente dos campos da GUI
            metadata_path = self.entries['metadata'].text()
            config_path = self.entries['config_file'].text()
            output_folder = os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT")

            print("")
            print("Gerando relatório DENV...")
            # Criar uma instância para executar o NextClade
            processor = DenvNextclade(output_folder)
            processor.execute_pipeline()

            #Executa o script de relatório
            generate_report_denv(metadata_path, config_path, output_folder)
            print("")
            print("")
            print("Relatório gerado com sucesso")
        except KeyError as e:
            QMessageBox.critical(self, "Erro", f"Campo não encontrado: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar relatório DENV: {str(e)}")



if __name__ == "__main__":
    app = QApplication(sys.argv)

    menu = MenuInicial()
    menu.show()
    sys.exit(app.exec_())
