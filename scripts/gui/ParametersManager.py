#!/usr/bin/env python3

from PyQt5.QtWidgets import (QDialog)

from scripts.gui.ParametersDialog import ParametersDialog

class ParametersManager:
    def __init__(self):
        # Valores padrão
        self.parameters = {
            "run_snp_eff": True,
            "write_mapped_reads": True,
            "min_len": 75,
            "depth": 20,
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


