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

# Classe para executar o processo em um thread separado
class AssemblerThread(QThread):
    process_started = pyqtSignal(str)
    process_finished = pyqtSignal(str)

    def __init__(self, commands=None):
        super().__init__()
        self.commands = commands or []  # Lista de comandos a serem executados

    def execute_command(self, command, description=""):
        try:
            if description:
                self.process_started.emit(description)
            self.process_started.emit(" ")
            subprocess.run(command, shell=True, check=True)
            self.process_started.emit(" ")
        except subprocess.CalledProcessError as e:
            self.process_started.emit(f"Erro ao executar {description}: {str(e)}")
            raise

    def run(self):
        for command, description in self.commands:
            self.execute_command(command, description)