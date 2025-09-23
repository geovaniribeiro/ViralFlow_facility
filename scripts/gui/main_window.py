#!/usr/bin/env python3

from PySide6.QtWidgets import (
    QApplication, QVBoxLayout, QLabel, QPushButton, QWidget, QMessageBox, QRadioButton
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QThread, Signal
import subprocess
import os
import sys
import matplotlib
matplotlib.use('Agg')  

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.gui.AssemblerRun_SC2 import ViralFlowGUI_SC2  # Interface para SARS-CoV-2
from scripts.gui.AssemblerRun_custom import ViralFlowGUI as ViralFlowGUI_custom  # Interface para vírus customizados
from scripts.utilities.update_database import atualizar_banco_dados  # Função para atualizar banco de dados
from scripts.utilities.update_viralflow import atualizar_viralflow  # Função para atualizar viralflow
from scripts.utilities.update_GUI import atualizar_GUI  # Função para atualizar viralflow
from scripts.analysis.report.report_generator_denv import generate_report_denv  # Classe para geração de relatórios
from scripts.analysis.report.report_generator_chikv import generate_report_chikv  # Classe para geração de relatórios
from scripts.analysis.DenvNextclade import DenvNextclade # Classe para rodar DenvNext (genotyping e linhagem)


class WorkerThread(QThread):
    finished = Signal()
    error = Signal(str)

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
        self.setWindowTitle("Menu Inicial - ViralFlow GUI")
        self.setGeometry(200, 200, 600, 300)
        self.setWindowIcon(QIcon(os.path.expanduser("~/ViralFlow/docs/source/img/viralflow_logo.png")))

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Escolha uma opção:"))

        # Botões de atualização
        update_button = QPushButton("Atualizar Interface")
        update_button.clicked.connect(self.atualizar_GUI)
        layout.addWidget(update_button)

        update_viralflow_btn = QPushButton("Atualizar ViralFlow")
        update_viralflow_btn.clicked.connect(self.atualizar_viralflow)
        layout.addWidget(update_viralflow_btn)

        db_update_button = QPushButton("Atualizar Banco de dados")
        db_update_button.clicked.connect(self.atualizar_banco_dados)
        layout.addWidget(db_update_button)

        # Botões de seleção de vírus
        self.radio_sc2 = QRadioButton("SARS-CoV-2")
        self.radio_denv = QRadioButton("DENV")
        self.radio_chikv = QRadioButton("CHIKV")

        layout.addWidget(self.radio_sc2)
        layout.addWidget(self.radio_denv)
        layout.addWidget(self.radio_chikv)

        confirm_button = QPushButton("Iniciar Análise")
        confirm_button.clicked.connect(self.executar_analise)
        layout.addWidget(confirm_button)

        exit_button = QPushButton("Sair")
        exit_button.clicked.connect(self.sair)
        layout.addWidget(exit_button)

        self.setLayout(layout)

    def atualizar_GUI(self):
        if QMessageBox.question(self, "Confirmação", "Você deseja atualizar a interface?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.thread = WorkerThread(atualizar_GUI)
            self.thread.error.connect(lambda msg: QMessageBox.critical(self, "Erro", msg))
            self.thread.start()

    def atualizar_viralflow(self):
        if QMessageBox.question(self, "Confirmação", "Você deseja atualizar o ViralFlow?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.thread = WorkerThread(atualizar_viralflow)
            self.thread.error.connect(lambda msg: QMessageBox.critical(self, "Erro", msg))
            self.thread.start()

    def atualizar_banco_dados(self):
        if QMessageBox.question(self, "Confirmação", "Atualizar banco de dados? Isso pode levar algum tempo.", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.thread_banco = WorkerThread(atualizar_banco_dados)
            self.thread_banco.finished.connect(lambda: QMessageBox.information(self, "Sucesso", "Banco de dados atualizado!"))
            self.thread_banco.error.connect(lambda msg: QMessageBox.critical(self, "Erro", msg))
            self.thread_banco.start()

    def executar_analise(self):
        if self.radio_sc2.isChecked():
            self.close()
            self.tela_assembly = ViralFlowGUI_SC2(self)
            self.tela_assembly.show()
        elif self.radio_denv.isChecked():
            self.close()
            self.tela_assembly = ViralFlowDENV(self)
            self.tela_assembly.show()
        elif self.radio_chikv.isChecked():
            self.close()
            self.tela_assembly = ViralFlowCHIKV(self)
            self.tela_assembly.show()

    def sair(self):
        if QMessageBox.question(self, "Confirmação", "Deseja sair?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            QApplication.quit()


class ViralFlowDENV(ViralFlowGUI_custom):
    def __init__(self, menu_inicial=None):
        super().__init__(menu_inicial, virus="DENV")
        self.menu_principal = menu_inicial

    def report_generator(self, message):
        try:
            metadata_path = self.entries['metadata'].text()
            config_path = self.entries['config_file'].text()
            output_folder = os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT")

            print("\nGerando relatório DENV...")
            processor = DenvNextclade(output_folder)
            processor.execute_pipeline()
            generate_report_denv(metadata_path, config_path, output_folder)
            print("\nRelatório gerado com sucesso")
            QMessageBox.information(self, "Relatório", "Relatório DENV gerado com sucesso.")
        except KeyError as e:
            QMessageBox.critical(self, "Erro", f"Campo não encontrado: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar relatório DENV: {str(e)}")


class ViralFlowCHIKV(ViralFlowGUI_custom):
    def __init__(self, menu_inicial=None):
        super().__init__(menu_inicial, virus="CHIKV")
        self.menu_principal = menu_inicial

    def report_generator(self, message):
        try:
            metadata_path = self.entries['metadata'].text()
            config_path = self.entries['config_file'].text()
            output_folder = os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT")

            print("\nGerando relatório CHIKV...")
            generate_report_chikv(metadata_path, config_path, output_folder)
            print("\nRelatório gerado com sucesso")
            QMessageBox.information(self, "Relatório", "Relatório CHIKV gerado com sucesso.")
        except KeyError as e:
            QMessageBox.critical(self, "Erro", f"Campo não encontrado: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar relatório CHIKV: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    menu = MenuInicial()
    menu.show()
    sys.exit(app.exec())
