#!/usr/bin/env python3
import json
import os
from PyQt5.QtWidgets import QDialog
from scripts.gui.ParametersDialog import ParametersDialog

class ParametersManager:
    def __init__(self):
        # Arquivo JSON para salvar os parâmetros (mesma pasta do script)
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")

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

        # Tenta carregar parâmetros salvos do JSON
        self.load_parameters()

    def configure_parameters(self, parent=None):
        dialog = ParametersDialog(parent)
        dialog.set_parameters(self.parameters)  # Preenche o diálogo com os valores atuais

        if dialog.exec_() == QDialog.Accepted:
            self.parameters = dialog.get_parameters()  # Pega os valores alterados
            self.save_parameters()  # Salva no JSON

    def save_parameters(self):
        """Salva os parâmetros no arquivo JSON."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.parameters, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar parâmetros: {e}")

    def load_parameters(self):
        """Carrega os parâmetros do JSON, se existir."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self.parameters = loaded
                    else:
                        print("Arquivo de configuração inválido, usando valores padrão")
            except json.JSONDecodeError:
                print("Erro ao ler JSON, usando valores padrão")
        else:
            # Se não existe, cria o arquivo com os valores padrão
            self.save_parameters()
