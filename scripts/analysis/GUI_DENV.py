#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QDialog, QCheckBox, QSpinBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal

import pandas as pd
import subprocess

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.analysis.report.report_generator_denv import generate_report_denv
from scripts.analysis.DenvProcessor import DenvProcessor

#Import classes instances
from scripts.analysis.assembler.AssemblerRun_custom import Assembler_run



class ReportGenerator:
    def __init__(self, output_folder):
        self.output_folder = output_folder

    def generate_report(self):
        # Exemplo simples
        report_path = os.path.join(self.output_folder, "report.csv")
        try:
            data = {"Step": ["Assembly", "Analysis", "Report"], "Status": ["Completed", "Completed", "Generated"]}
            df = pd.DataFrame(data)
            df.to_csv(report_path, index=False)
            print(f"Relatório gerado em: {report_path}")
        except Exception as e:
            print(f"Erro ao gerar relatório: {e}")

# Adicionar funcionalidade ao workflow existente
class AssemblerRunWithReport(Assembler_run):
    def run(self):
        # Executar as etapas originais
        super().run()

        # Geração de relatório adicional
        report_generator = ReportGenerator(self.output_folder)
        report_generator.generate_report()

# Inicializar GUI com as funcionalidades
if __name__ == "__main__":
    app = QApplication([])
    gui = Assembler_run()
    gui.show()
    app.exec_()