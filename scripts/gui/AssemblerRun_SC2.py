#!/usr/bin/env python3

import sys
import subprocess
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QComboBox, QGroupBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importações
from scripts.gui.ParametersDialog import ParametersDialog
from scripts.gui.ParametersManager import ParametersManager
from scripts.analysis.assembler.assembler_thread import AssemblerThread


class AssemblerRun_SC2(AssemblerThread):
    def __init__(self, command_viralflow, output_folder, input_path):

        commands = [(command_viralflow, "Executando ViralFlow...")]
        super().__init__(commands)

        self.output_folder = output_folder
        self.input_path = input_path

    def run(self):
        try:
            super().run()
            self.process_finished.emit("ViralFlow executado com sucesso!\n")
        except Exception as e:
            self.process_finished.emit(f"Erro durante a execução: {str(e)}")

 
 
class ViralFlowGUI_SC2(QWidget):
    process_finished = Signal(str)

    def __init__(self, menu_inicial):
        super().__init__()
        self.menu_inicial = menu_inicial

        self.setWindowTitle("ViralFlow GUI - SARS-CoV-2")
        self.setGeometry(100, 100, 600, 380)
        self.setWindowIcon(QIcon(os.path.expanduser("~/ViralFlow/docs/source/img/viralflow_logo.png")))

        self.param_manager = ParametersManager()
        main_layout = QVBoxLayout()

        # Pasta resources
        self.resources_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "resources"
        )

        # -------------------------
        # Grupo: Dados de entrada
        # -------------------------
        input_group = QGroupBox("Dados de entrada")
        input_layout = QVBoxLayout()

        # Campos adicionais
        self.fields = [
            ("Arquivo bed (Primers)", "primersBED", True),
            ("Pasta de entrada", "inDir", False),
            ("Pasta de saída", "outDir", False)
        ]
        
        self.entries = {}

        for label_text, field_name, is_file in self.fields:
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(label_text))
            entry = QLineEdit(self)
            row_layout.addWidget(entry)
            browse_button = QPushButton("Browse", self)
            if is_file:
                browse_button.clicked.connect(lambda checked, e=entry: self.select_file(e))
            else:
                browse_button.clicked.connect(lambda checked, e=entry: self.select_folder(e))
            row_layout.addWidget(browse_button)
            self.entries[field_name] = entry
            input_layout.addLayout(row_layout)

        self.entries["inDir"].textChanged.connect(self.validate_fields)
        self.entries["outDir"].textChanged.connect(self.validate_fields)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # -------------------------
        # Grupo: Execução
        # -------------------------
        exec_group = QGroupBox("Execução")
        exec_layout = QVBoxLayout()

        params_button = QPushButton("Configurar Parâmetros")
        params_button.clicked.connect(lambda: self.param_manager.configure_parameters(self))
        exec_layout.addWidget(params_button)

        self.run_button = QPushButton("Executar ViralFlow", self)
        self.run_button.setEnabled(False)  # começa desabilitado
        self.run_button.clicked.connect(self.run_command)
        exec_layout.addWidget(self.run_button)

        menu_button = QPushButton("Voltar ao Menu Inicial")
        menu_button.clicked.connect(self.voltar_menu_inicial)
        exec_layout.addWidget(menu_button)

        exit_button = QPushButton("Sair")
        exit_button.clicked.connect(self.sair)
        exec_layout.addWidget(exit_button)

        exec_group.setLayout(exec_layout)
        main_layout.addWidget(exec_group)

        self.setLayout(main_layout)
        self.thread = None

    def select_file(self, entry):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecione um arquivo")
        if file_path:
            entry.setText(file_path)

    def select_folder(self, entry):
        folder_path = QFileDialog.getExistingDirectory(self, "Selecione uma pasta")
        if folder_path:
            entry.setText(folder_path)

    def get_nextflow_path(self):
        try:
            result = subprocess.run(["which", "nextflow"], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "nextflow"

    def run_command(self):
        params = {key: entry.text() for key, entry in self.entries.items()}
        nextflow_path = self.get_nextflow_path()

        command_viralflow = (
            f"micromamba run -n viralflow "
            f"{nextflow_path} run {os.path.expanduser('~/ViralFlow/vfnext/main.nf')} "
            f"--primersBED {params['primersBED']} "
            f"--outDir {params['outDir']} "
            f"--inDir {params['inDir']} "
            f"--virus sars-cov2 "
            f"--runSnpEff {'true' if self.param_manager.parameters['run_snp_eff'] else 'false'} "
            f"--writeMappedReads {'true' if self.param_manager.parameters['write_mapped_reads'] else 'false'} "
            f"--minLen {self.param_manager.parameters['min_len']} "
            f"--depth {self.param_manager.parameters['depth']} "
            f"--minDpIntrahost {self.param_manager.parameters['min_dp_intrahost']} "
            f"--nextflowSimCalls {self.param_manager.parameters['nextflow_sim_calls']} "
            f"--fastp_threads {self.param_manager.parameters['fastp_threads']} "
            f"--bwa_threads {self.param_manager.parameters['bwa_threads']} "
            f"--mafft_threads {self.param_manager.parameters['mafft_threads']} "
            f"--trimLen 0 --refGenomeCode null "
            f"--referenceGFF null --referenceGenome null -resume"
        )

        self.thread = AssemblerRun_SC2(
            command_viralflow,
            os.path.join(params['outDir'], "COMPILED_OUTPUT"),
            input_path=params['inDir']
        )

        self.thread.process_started.connect(self.update_status)
        self.thread.process_finished.connect(self.update_status)
        self.thread.start()

    def update_status(self, message):
        print(message)

    def voltar_menu_inicial(self):
        self.close()
        if self.menu_inicial:
            self.menu_inicial.show()

    def sair(self):
        confirm = QMessageBox.question(
            self, "Confirmação", "Tem certeza de que deseja sair?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            QApplication.quit()

    def validate_fields(self):
        """Habilita Executar ViralFlow apenas se inDir e outDir forem preenchidos."""
        inDir = self.entries["inDir"].text().strip()
        outDir = self.entries["outDir"].text().strip()

        if inDir and outDir:
            self.run_button.setEnabled(True)
            self.entries["inDir"].setStyleSheet("")
            self.entries["outDir"].setStyleSheet("")
        else:
            self.run_button.setEnabled(False)
            # Destaca os campos vazios em vermelho
            if not inDir:
                self.entries["inDir"].setStyleSheet("background-color: #ffcccc;")
            else:
                self.entries["inDir"].setStyleSheet("")
            if not outDir:
                self.entries["outDir"].setStyleSheet("background-color: #ffcccc;")
            else:
                self.entries["outDir"].setStyleSheet("")


def main():
    app = QApplication(sys.argv)
    window = ViralFlowGUI_SC2(None)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
