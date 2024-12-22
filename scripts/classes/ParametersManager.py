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


class ParametersManager:
    def __init__(self):
        # Valores padrão
        self.parameters = {
            "run_snp_eff": True,
            "write_mapped_reads": True,
            "min_len": 75,
            "depth": 10,
            "min_dp_intrahost": 100,
            "nextflow_sim_calls": 12,
            "fastp_threads": 12,
            "bwa_threads": 12,
            "mafft_threads": 12,
        }

    def configure_parameters(self, parent=None):
        dialog = ParametersDialog(parent)
        if dialog.exec_() == QDialog.Accepted:
            self.parameters = dialog.get_parameters()


