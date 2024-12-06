#!/usr/bin/env python3

import subprocess
from PyQt5.QtWidgets import QMessageBox


def atualizar_viralflow():
    try:
        # Comando para atualizar banco de dados
        subprocess.run(
            "./Installer/viralflow_setup.sh",
            shell=True,
            check=True
        )
        QMessageBox.information(None, "Sucesso", "ViralFlow atualizado com sucesso!")
    except subprocess.CalledProcessError as e:
        QMessageBox.critical(None, "Erro", f"Falha ao atualizar o banco de dados:\n{e}")
