#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox)

import subprocess

class ViralFlowGUI(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize the window
        self.setWindowTitle("ViralFlow GUI")
        self.setGeometry(100, 100, 500, 250)

        # Create the layout
        layout = QVBoxLayout()

        # Define labels and input fields
        self.fields = [
            ("Arquivo bed (Primers)", "primersBED", True),  # True indicates a file should be chosen
            ("Pasta de entrada", "inDir", False),      # False indicates a folder should be chosen
            ("Pasta de saida", "outDir", False),
            ("Arquivo metadados (.csv)", "metadata", True),
            ("Arquivo configuração (.yaml)", "config_file", True),
        ]

        # Create a dictionary to store the QLineEdit widgets for each field
        self.entries = {}

        # Create input fields and browse buttons for each field
        for label_text, field_name, is_file in self.fields:
            row_layout = QHBoxLayout()

            # Create and add label
            label = QLabel(label_text)
            row_layout.addWidget(label)

            # Create and add the input field (QLineEdit)
            entry = QLineEdit(self)
            row_layout.addWidget(entry)

            # Create the "Browse" button to open the file/folder dialog
            browse_button = QPushButton("Browse", self)
            if is_file:
                browse_button.clicked.connect(lambda checked, e=entry: self.select_file(e))
            else:
                browse_button.clicked.connect(lambda checked, e=entry: self.select_folder(e))

            row_layout.addWidget(browse_button)

            # Add the row layout to the main layout
            layout.addLayout(row_layout)
            self.entries[field_name] = entry

        # Create and add the "Run Command" button
        run_button = QPushButton("Executar ViralFlow", self)
        run_button.clicked.connect(self.run_command)
        layout.addWidget(run_button)

        # Set the layout of the window
        self.setLayout(layout)

        # Botão para sair
        exit_button = QPushButton("Sair")
        exit_button.clicked.connect(self.sair)
        layout.addWidget(exit_button)

        self.setLayout(layout)

    def select_file(self, entry):
        # Open file dialog to select a file
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecione um arquivo")
        if file_path:
            entry.setText(file_path)

    def select_folder(self, entry):
        # Open folder dialog to select a directory
        folder_path = QFileDialog.getExistingDirectory(self, "Selecione uma pasta")
        if folder_path:
            entry.setText(folder_path)

    def run_command(self):
        """Construct and run the command with the parameters from the GUI."""
        # Collect parameters from the GUI
        params = {key: entry.text() for key, entry in self.entries.items()}

    # Construct the command string with parameters
        command_viralflow = f"NXF_VER=22.04.0 nextflow run ~/ViralFlow//vfnext/main.nf --primersBED {params['primersBED']} " \
                f"--outDir {params['outDir']} --inDir {params['inDir']} " \
                f"--virus sars-cov2 --runSnpEff true --writeMappedReads true --minLen 75 " \
                f"--depth 10 --minDpIntrahost 100 --trimLen 0 --refGenomeCode null " \
                f"--referenceGFF null --referenceGenome null --nextflowSimCalls 12 " \
                f"--fastp_threads 12 --bwa_threads 12 --mafft_threads 12 -resume"

        #command_conda_report = f"./report_generator_env.sh"
        command_report_generator = f"python scripts/report_generator_sc2.py {params['outDir']}/COMPILED_OUTPUT/ {params['metadata']} {params['config_file']}  "

        # Run the command using subprocess
        try:
            subprocess.run(command_viralflow, shell=True, check=True)
            print("ViralFlow executado com sucesso!")
            print(" ")
            print(" ")
            subprocess.run(command_report_generator, shell=True, check=True)
            print("Relatorio e arquivos gerados com sucesso!")
            print(" ")
            print(" ")
            print("O terminal pode ser fechado ;)")
            print(" ")
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")

    def sair(self):
        # Confirmação antes de sair
        confirm = QMessageBox.question(
            self,
            "Confirmação",
            "Tem certeza de que deseja sair?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            subprocess.run("exit", shell=True, check=True)
            QApplication.quit()


# Main function to run the application
def main():
    app = QApplication(sys.argv)
    window = ViralFlowGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
