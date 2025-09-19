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

class AssemblerRun_custom(AssemblerThread):
    def __init__(self, snpeff_custom, command_viralflow, output_folder, input_path, metadata_path, config_path):
        if metadata_path and input_path:
            try:
                rename_fastq_files(metadata_path, input_path)
                print("\nRenomeação de arquivos FASTQ concluída!\n")
            except Exception as e:
                print(f"Erro: {e}\n")
        commands = [
            (snpeff_custom, "Iniciando snpeff_custom..."),
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
            self.process_finished.emit(f"Erro: {str(e)}")


class ViralFlowGUI(QWidget):
    process_finished = pyqtSignal(str)

    def __init__(self, menu_inicial, virus="CUSTOM"):
        super().__init__()
        self.menu_inicial = menu_inicial
        self.virus = virus  # Novo parâmetro para filtrar BED

        self.setWindowTitle("ViralFlow GUI")
        self.setGeometry(100, 100, 500, 250)
        self.setWindowIcon(QIcon(os.path.expanduser("~/ViralFlow/docs/source/img/viralflow_logo.png")))

        self.param_manager = ParametersManager()
        layout = QVBoxLayout()

        # Criar campos
        self.entries = {}
        self.fields = [
            ("Arquivo bed (Primers)", "primersBED", True),
            ("Pasta de entrada", "inDir", False),
            ("Pasta de saída", "outDir", False),
            ("Código refseq", "refGenomeCode", False),
            ("Metadados (.csv) [Opcional]", "metadata", True),
            ("Submission_info (.yaml) [Opcional]", "config_file", True),
        ]

        for label_text, field_name, is_file in self.fields:
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            row_layout.addWidget(label)

            if field_name == "primersBED":
                combo = QComboBox()
                self.populate_bed_files(combo)
                row_layout.addWidget(combo)
                self.entries[field_name] = combo
            else:
                entry = QLineEdit(self)
                row_layout.addWidget(entry)
                if field_name != "refGenomeCode":
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
        params_button.clicked.connect(self.configure_parameters)
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
        self.parameters = {
            "run_snp_eff": True,
            "write_mapped_reads": True,
            "min_len": 75,
            "depth": 10,
            "min_dp_intrahost": 100,
        }
        self.thread = None

    def populate_bed_files(self, combo):
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "resources")
        for f in os.listdir(resources_dir):
            if f.endswith(".bed"):
                if self.virus.upper() == "DENV" and f.startswith("denv"):
                    combo.addItem(f, os.path.join(resources_dir, f))
                elif self.virus.upper() == "CHIKV" and f.startswith("chikv"):
                    combo.addItem(f, os.path.join(resources_dir, f))
                elif self.virus.upper() == "CUSTOM":
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
        self.param_manager.configure_parameters(self)

    def post_processing(self):
        try:
            reads, coverage = data_processing(os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT"))
            mod_pasta(os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT"))
            Quality_monitor(coverage, reads, os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT"))
            print("Quality check realizado!")
        except Exception as e:
            print(f"Erro: {e}")

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
                params[key] = entry.currentData()  # Caminho do .bed

        nextflow_path = self.get_nextflow_path()
        snpeff_custom = f"micromamba run -n viralflow bash ~/ViralFlow/vfnext/containers/add_entries_SnpeffDB.sh custom {params['refGenomeCode']}"
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
            f"--trimLen 0 --refGenomeCode {params['refGenomeCode']} --referenceGFF null "
            f"--referenceGenome null -resume"
        )

        self.thread = AssemblerRun_custom(snpeff_custom, command_viralflow,
                                          os.path.join(params['outDir'], "COMPILED_OUTPUT"),
                                          metadata_path=params.get('metadata'),
                                          config_path=params.get('config_file'),
                                          input_path=params.get('inDir'))
        self.thread.process_started.connect(self.update_status)
        self.thread.process_finished.connect(self.update_status)
        self.thread.process_finished.connect(self.post_processing)
        self.thread.start()

    def update_status(self, message):
        print(message)

    def voltar_menu_inicial(self):
        self.close()
        self.menu_inicial.show()

    def sair(self):
        if QMessageBox.question(self, "Confirmação", "Deseja sair?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            QApplication.quit()

def main():
    app = QApplication(sys.argv)
    window = ViralFlowGUI(menu_inicial=None)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
