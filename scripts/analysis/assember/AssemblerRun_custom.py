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
from scripts.classes.Assembler_run import Assembler_run

# Subclasse para executar o processo ProcessThread
class AssemblerRun_custom(Assembler_run):
    def __init__(self, snpeff_custom, command_viralflow, output_folder, metadata_path, config_path, run_pipeline=None):
        commands = [
            (snpeff_custom, "Iniciando snpeff_custom..."),
            (command_viralflow, "Executando ViralFlow...")
        ]
        super().__init__(commands)
        self.output_folder = output_folder
        self.metadata_path = metadata_path
        self.config_path = config_path
        self.run_pipeline = run_pipeline

    def run(self):
        super().run()
        if self.run_pipeline:
            self.process_started.emit("Executando pipeline customizado...")
            self.run_pipeline()
            self.process_started.emit("Pipeline customizado concluído com sucesso!")