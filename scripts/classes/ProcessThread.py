#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QDialog, QCheckBox, QSpinBox
)

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal


import subprocess

# Classe para executar o processo em um thread separado
class ProcessThread(QThread):
    process_started = pyqtSignal(str)
    process_finished = pyqtSignal(str)

    def __init__(self, command_viralflow, output_folder, metadata_path, config_path):
        super().__init__()
        self.command_viralflow = command_viralflow
        self.output_folder = output_folder
        self.metadata_path = metadata_path
        self.config_path = config_path

    def run(self):
        try:
            self.process_started.emit("Executando ViralFlow...")
            self.process_started.emit(" ")
            subprocess.run(self.command_viralflow, shell=True, check=True)
            self.process_started.emit("ViralFlow executado com sucesso!")
            self.process_started.emit(" ")
            self.process_started.emit(" ")

            # Gerar o relatório após a execução dos comandos
            self.process_started.emit("Gerando o relatório...")
            self.process_started.emit(" ")
            self.process_started.emit(" ")

            generate_report(output_folder=self.output_folder, 
                            metadata_path=self.metadata_path, 
                            config_path=self.config_path)
            self.process_started.emit("Relatório gerado com sucesso!")
            self.process_started.emit(" ")
            self.process_started.emit(" ")

            self.process_finished.emit("Processo concluído com sucesso!")
            self.process_started.emit(" ")
            self.process_started.emit(" ")

        except subprocess.CalledProcessError as e:
            self.process_finished.emit(f"Erro ao executar o comando: {e}")
        except Exception as e:
            self.process_finished.emit(f"Erro ao gerar o relatório: {e}")

