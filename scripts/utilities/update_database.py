#!/usr/bin/env python3

import subprocess
from PySide6.QtWidgets import QMessageBox

def atualizar_banco_dados():
    try:

        # Executar o comando dentro do ambiente Micromamba sem precisar ativá-lo no shell
        comando = [
            "micromamba", "run", "-n", "viralflow", "bash", "-c",
            "viralflow -update_pangolin && viralflow -update_pangolin_data"
        ]

        subprocess.run(comando, check=True)

        #QMessageBox.information(None, "Sucesso", "Banco de dados atualizado com sucesso!")

    except subprocess.CalledProcessError as e:
        QMessageBox.critical(None, "Erro", f"Falha ao atualizar o banco de dados:\n{e}")
