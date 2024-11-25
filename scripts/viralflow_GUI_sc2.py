#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QPlainTextEdit)

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
            ("Primers BED File", "primersBED"),
            ("Input Directory", "inDir"),
            ("Output Directory", "outDir")
            
        ]

        # Create a dictionary to store the QLineEdit widgets for each field
        self.entries = {}

        # Create input fields and browse buttons for each field
        for label_text, field_name in self.fields:
            row_layout = QHBoxLayout()

            # Create and add label
            label = QLabel(label_text)
            row_layout.addWidget(label)

            # Create and add the input field (QLineEdit)
            entry = QLineEdit(self)
            row_layout.addWidget(entry)

            # Create the "Browse" button to open the file/folder dialog
            if field_name == "primersBED":
                browse_button = QPushButton("Browse", self)
                browse_button.clicked.connect(lambda checked, e=entry: self.select_file(e))
            else:
                browse_button = QPushButton("Browse", self)
                browse_button.clicked.connect(lambda checked, e=entry: self.select_folder(e))

            row_layout.addWidget(browse_button)

            # Add the row layout to the main layout
            layout.addLayout(row_layout)
            self.entries[field_name] = entry

        # Create and add the "Run Command" button
        run_button = QPushButton("Run Command", self)
        run_button.clicked.connect(self.run_command)
        layout.addWidget(run_button)

        # Set the layout of the window
        self.setLayout(layout)

    def select_folder(self, entry_field):
        """Open a dialog to select a folder and set the path in the entry field."""
        folder_selected = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_selected:
            entry_field.setText(folder_selected)

    def select_file(self, entry_field):
        """Open a dialog to select a file and set the path in the entry field."""
        file_selected, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_selected:
            entry_field.setText(file_selected)

    def run_command(self):
        """Construct and run the command with the parameters from the GUI."""
        # Collect parameters from the GUI
        params = {key: entry.text() for key, entry in self.entries.items()}

    # Construct the command string with parameters
        command = f"NXF_VER=22.04.0 nextflow run ~/ViralFlow//vfnext/main.nf --primersBED {params['primersBED']} " \
                f"--outDir {params['outDir']} --inDir {params['inDir']} " \
                f"--virus sars-cov2 --runSnpEff true --writeMappedReads true --minLen 75 " \
                f"--depth 10 --minDpIntrahost 100 --trimLen 0 --refGenomeCode null " \
                f"--referenceGFF null --referenceGenome null --nextflowSimCalls 12 " \
                f"--fastp_threads 12 --bwa_threads 12 --mafft_threads 12 -resume"


        # Run the command using subprocess
        try:
            subprocess.run(command, shell=True, check=True)
            print("Command executed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")

# Main function to run the application
def main():
    app = QApplication(sys.argv)
    window = ViralFlowGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
