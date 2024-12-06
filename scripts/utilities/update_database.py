#!/usr/bin/env python3

import subprocess
from PyQt5.QtWidgets import QMessageBox


def atualizar_banco_dados():
    try:
        # Comando para atualizar banco de dados
        subprocess.run(
            "viralflow -update_pangolin && viralflow -update_pangolin_data",
            shell=True,
            check=True
        )
        QMessageBox.information(None, "Sucesso", "Banco de dados atualizado com sucesso!")
    except subprocess.CalledProcessError as e:
        QMessageBox.critical(None, "Erro", f"Falha ao atualizar o banco de dados:\n{e}")
