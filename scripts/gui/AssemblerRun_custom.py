#!/usr/bin/env python3

import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QComboBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.gui.ParametersDialog import ParametersDialog
from scripts.gui.ParametersManager import ParametersManager
from scripts.analysis.assembler.assembler_thread import AssemblerThread
from scripts.analysis.rename_fastq import rename_fastq_files
from scripts.analysis.report.modules_general import data_processing, mod_pasta, Quality_monitor


# -----------------------------
# Classe que executa os comandos
# -----------------------------
class AssemblerRun_custom(AssemblerThread):
    def __init__(self, command_viralflow, output_folder, input_path, metadata_path, config_path):
        if metadata_path and input_path:
            try:
                rename_fastq_files(metadata_path, input_path)
                print("\nRenomeação de arquivos FASTQ concluída!\n")
            except Exception as e:
                print(f"Erro ao renomear arquivos FASTQ: {str(e)}\n")

        commands = [
            (command_viralflow, "Executando ViralFlow...")
        ]
        super().__init__(commands)
        self.output_folder = output_folder
        self.metadata_path = metadata_path
        self.config_path = config_path
        self.input_path = input_path

    def run(self):
        try:
            super().run()
            self.process_finished.emit("ViralFlow executado com sucesso!")
        except Exception as e:
            self.process_finished.emit(f"Erro durante a execução: {str(e)}")


# -----------------------------
# Interface gráfica principal
# -----------------------------
class ViralFlowGUI(QWidget):
    process_finished = pyqtSignal(str)

    def __init__(self, menu_inicial, virus="DENV"):
        super().__init__()
        self.menu_inicial = menu_inicial
        self.virus = virus  # define o vírus em execução (DENV ou CHIKV)

        self.setWindowTitle("ViralFlow GUI")
        self.setGeometry(100, 100, 500, 300)
        self.setWindowIcon(QIcon(os.path.expanduser("~/ViralFlow/docs/source/img/viralflow_logo.png")))

        self.param_manager = ParametersManager()
        layout = QVBoxLayout()
        self.entries = {}

        # Campos da interface
        self.fields = [
            ("Código refseq", "refGenomeCode", False),
            ("Arquivo bed (Primers)", "primersBED", True),
            ("Pasta de entrada", "inDir", False),
            ("Pasta de saída", "outDir", False),
            ("Metadados (.csv) [Opcional]", "metadata", True),
            ("Submission_info (.yaml) [Opcional]", "config_file", True),
        ]

        for label_text, field_name, is_file in self.fields:
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            row_layout.addWidget(label)

            # Lista de arquivos BED
            if field_name == "primersBED":
                combo = QComboBox()
                self.populate_bed_files(combo)
                row_layout.addWidget(combo)
                self.entries[field_name] = combo

            # Código refseq — adaptado
            elif field_name == "refGenomeCode":
                if self.virus.upper() == "DENV":
                    combo = QComboBox()
                    combo.addItem("DENV1 (NC_001477.1)", "NC_001477.1")
                    combo.addItem("DENV2 (NC_001474.2)", "NC_001474.2")
                    combo.addItem("DENV3 (NC_001475.2)", "NC_001475.2")
                    combo.addItem("DENV4 (NC_002640.1)", "NC_002640.1")
                    row_layout.addWidget(combo)
                    self.entries[field_name] = combo
                elif self.virus.upper() == "CHIKV":
                    hidden_entry = QLineEdit()
                    hidden_entry.setText("NC_004162.2")
                    hidden_entry.setVisible(False)
                    self.entries[field_name] = hidden_entry

            # Demais campos
            else:
                entry = QLineEdit(self)
                row_layout.addWidget(entry)
                if field_name not in ["refGenomeCode"]:
                    btn = QPushButton("Browse", self)
                    if is_file:
                        btn.clicked.connect(lambda checked, e=entry: self.select_file(e))
                    else:
                        btn.clicked.connect(lambda checked, e=entry: self.select_folder(e))
                    row_layout.addWidget(btn)
                self.entries[field_name] = entry

            layout.addLayout(row_layout)

        # Botões
        params_button = QPushButton("Configurar Parâmetros")
        params_button.clicked.connect(lambda: self.param_manager.configure_parameters(self))
        layout.addWidget(params_button)

        run_button = QPushButton("Executar ViralFlow")
        run_button.clicked.connect(self.run_command)
        layout.addWidget(run_button)

        menu_button = QPushButton("Voltar ao Menu Inicial")
        menu_button.clicked.connect(self.voltar_menu_inicial)
        layout.addWidget(menu_button)

        exit_button = QPushButton("Sair")
        exit_button.clicked.connect(self.sair)
        layout.addWidget(exit_button)

        self.setLayout(layout)
        self.thread = None

    # -----------------------------
    # Métodos auxiliares
    # -----------------------------
    def populate_bed_files(self, combo):
        resources_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "resources"
        )
        for f in os.listdir(resources_dir):
            if f.endswith(".bed"):
                if self.virus.upper() == "DENV" and f.startswith("denv"):
                    combo.addItem(f, os.path.join(resources_dir, f))
                elif self.virus.upper() == "CHIKV" and f.startswith("chikv"):
                    combo.addItem(f, os.path.join(resources_dir, f))

    def select_file(self, entry):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecione um arquivo")
        if file_path:
            entry.setText(file_path)

    def select_folder(self, entry):
        folder_path = QFileDialog.getExistingDirectory(self, "Selecione uma pasta")
        if folder_path:
            entry.setText(folder_path)

    def configure_parameters(self):
        dialog = ParametersDialog(self.param_manager.parameters, self)
        if dialog.exec_():
            self.param_manager.parameters = dialog.get_parameters()

    def post_processing(self):
        """Executa o processamento de dados após a finalização do assembler."""
        try:
            reads, coverage = data_processing(os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT"))
            mod_pasta(os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT"))
            Quality_monitor(coverage, reads, os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT"))
            print("")
            print("Quality check realizado!")
        except Exception as e:
            print(f"Erro ao executar data_processing, mod_pasta ou Quality_monitor: {e}")

    def get_nextflow_path(self):
        try:
            result = subprocess.run(["which", "nextflow"], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "nextflow"

    def run_command(self):
        params = {}
        for key, entry in self.entries.items():
            if isinstance(entry, QLineEdit):
                params[key] = entry.text()
            elif isinstance(entry, QComboBox):
                params[key] = entry.currentData()

        nextflow_path = self.get_nextflow_path()

        command_viralflow = (
            f"micromamba run -n viralflow {nextflow_path} run ~/ViralFlow/vfnext/main.nf "
            f"--primersBED {params['primersBED']} "
            f"--outDir {params['outDir']} "
            f"--inDir {params['inDir']} "
            f"--virus custom "
            f"--runSnpEff {'true' if self.param_manager.parameters['run_snp_eff'] else 'false'} "
            f"--writeMappedReads {'true' if self.param_manager.parameters['write_mapped_reads'] else 'false'} "
            f"--minLen {self.param_manager.parameters['min_len']} "
            f"--depth {self.param_manager.parameters['depth']} "
            f"--minDpIntrahost {self.param_manager.parameters['min_dp_intrahost']} "
            f"--nextflowSimCalls {self.param_manager.parameters['nextflow_sim_calls']} "
            f"--fastp_threads {self.param_manager.parameters['fastp_threads']} "
            f"--bwa_threads {self.param_manager.parameters['bwa_threads']} "
            f"--mafft_threads {self.param_manager.parameters['mafft_threads']} "
            f"--trimLen 0 --refGenomeCode {params['refGenomeCode']} "
            f"--referenceGFF null --referenceGenome null -resume"
        )

        self.thread = AssemblerRun_custom(
            command_viralflow,
            os.path.join(params['outDir'], "COMPILED_OUTPUT"),
            metadata_path=params.get('metadata'),
            config_path=params.get('config_file'),
            input_path=params.get('inDir')
        )
        
        # Conectar os sinais do thread com as funções da GUI
        self.thread.process_started.connect(self.update_status)
        self.thread.process_finished.connect(self.update_status)

        #Se metadata_path e config_path forem válidos, gerar relatório ao finalizar o processo
        if params.get('metadata') and params.get('config_file'):
            if hasattr(self, "report_generator") and callable(getattr(self, "report_generator")):
                self.thread.process_finished.connect(self.report_generator)
        else:
            print("AVISO: Metadados e/ou Submission info não foram informados!")
            print("")  

        self.thread.start()

    def update_status(self, message):
        print(message)

    def voltar_menu_inicial(self):
        self.close()
        if self.menu_inicial:
            self.menu_inicial.show()

    def sair(self):
        if QMessageBox.question(self, "Confirmação", "Deseja sair?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            QApplication.quit()


def main():
    app = QApplication(sys.argv)
    window = ViralFlowGUI(menu_inicial=None, virus="DENV")  # padrão: DENV
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
