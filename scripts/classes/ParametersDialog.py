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

class ParametersDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Configurar Parâmetros")
        self.setGeometry(100, 100, 400, 400)

        self.setWindowIcon(QIcon(os.path.expanduser("~/ViralFlow/docs/source/img/viralflow_logo.png")))

        layout = QVBoxLayout()

        # Parâmetros com opções booleanas (CheckBox)
        self.run_snp_eff = QCheckBox("Habilitar --runSnpEff")
        self.run_snp_eff.setChecked(True)
        layout.addWidget(self.run_snp_eff)

        self.write_mapped_reads = QCheckBox("Habilitar --writeMappedReads")
        self.write_mapped_reads.setChecked(True)
        layout.addWidget(self.write_mapped_reads)

        # Parâmetros numéricos (SpinBox)
        self.min_len_label = QLabel("Valor para --minLen")
        layout.addWidget(self.min_len_label)
        self.min_len = QSpinBox()
        self.min_len.setMinimum(0)
        self.min_len.setMaximum(1000)
        self.min_len.setValue(75)
        layout.addWidget(self.min_len)

        self.depth_label = QLabel("Valor para --depth")
        layout.addWidget(self.depth_label)
        self.depth = QSpinBox()
        self.depth.setMinimum(0)
        self.depth.setMaximum(1000)
        self.depth.setValue(10)
        layout.addWidget(self.depth)

        self.min_dp_intrahost_label = QLabel("Valor para --minDpIntrahost")
        layout.addWidget(self.min_dp_intrahost_label)
        self.min_dp_intrahost = QSpinBox()
        self.min_dp_intrahost.setMinimum(0)
        self.min_dp_intrahost.setMaximum(1000)
        self.min_dp_intrahost.setValue(100)
        layout.addWidget(self.min_dp_intrahost)

        self.nextflow_sim_calls_label = QLabel("Valor para --nextflowSimCalls")
        layout.addWidget(self.nextflow_sim_calls_label)
        self.nextflow_sim_calls = QSpinBox()
        self.nextflow_sim_calls.setMinimum(0)
        self.nextflow_sim_calls.setMaximum(300)
        self.nextflow_sim_calls.setValue(12)
        layout.addWidget(self.nextflow_sim_calls)

        self.fastp_threads_label = QLabel("Valor para --fastp_threads")
        layout.addWidget(self.fastp_threads_label)
        self.fastp_threads = QSpinBox()
        self.fastp_threads.setMinimum(0)
        self.fastp_threads.setMaximum(300)
        self.fastp_threads.setValue(12)
        layout.addWidget(self.fastp_threads)

        self.bwa_threads_label = QLabel("Valor para --bwa_threads")
        layout.addWidget(self.bwa_threads_label)
        self.bwa_threads = QSpinBox()
        self.bwa_threads.setMinimum(0)
        self.bwa_threads.setMaximum(300)
        self.bwa_threads.setValue(12)
        layout.addWidget(self.bwa_threads)

        self.mafft_threads_label = QLabel("Valor para --mafft_threads")
        layout.addWidget(self.mafft_threads_label)
        self.mafft_threads = QSpinBox()
        self.mafft_threads.setMinimum(0)
        self.mafft_threads.setMaximum(300)
        self.mafft_threads.setValue(12)
        layout.addWidget(self.mafft_threads)

        # Botões
        button_layout = QHBoxLayout()
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_parameters(self):
        return {
            "run_snp_eff": self.run_snp_eff.isChecked(),
            "write_mapped_reads": self.write_mapped_reads.isChecked(),
            "min_len": self.min_len.value(),
            "depth": self.depth.value(),
            "min_dp_intrahost": self.min_dp_intrahost.value(),
            "nextflow_sim_calls": self.nextflow_sim_calls.value(),
            "fastp_threads": self.fastp_threads.value(),
            "bwa_threads": self.bwa_threads.value(),
            "mafft_threads": self.mafft_threads.value(),
        }

