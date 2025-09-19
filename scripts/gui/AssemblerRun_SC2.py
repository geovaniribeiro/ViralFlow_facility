#!/usr/bin/env python3

import sys
import subprocess
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QDialog, QComboBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

#Import classes instances
from scripts.gui.ParametersDialog import ParametersDialog #Classe dos parametros ViralFlow
from scripts.gui.ParametersManager import ParametersManager #Classe parametros Deafult do ViralFlow
from scripts.analysis.assembler.assembler_thread import AssemblerThread #Instancia para iniciar uma nova thread no processo
from scripts.analysis.report.report_generator_sc2 import generate_report #Função para gerar relatorio e arquivos de SC2
from scripts.analysis.rename_fastq import rename_fastq_files #Função para renomear arquivos para codigo de amostras, se necessario
from scripts.analysis.report.modules_general import data_processing, mod_pasta, Quality_monitor #Importa funções para gerar relatorio de qualidade


class AssemblerRun_SC2(AssemblerThread):
    def __init__(self, command_viralflow, output_folder, metadata_path, config_path, input_path):
        # Renomear FASTQs se possível
        if metadata_path and input_path:
            try:
                rename_fastq_files(metadata_path, input_path)
                print("\nRenomeação de arquivos FASTQ concluída com sucesso!\n")
            except Exception as e:
                print(f"Erro ao renomear arquivos FASTQ: {str(e)}\n")
        else:
            print("Aviso: metadata_path ou input_path não fornecidos, pulando renomeação.\n")

        commands = [(command_viralflow, "Executando ViralFlow...")]
        super().__init__(commands)

        self.output_folder = output_folder
        self.metadata_path = metadata_path
        self.config_path = config_path
        self.input_path = input_path

    def run(self):
        try:
            super().run()
            self.process_finished.emit("ViralFlow executado com sucesso!\n")
        except Exception as e:
            self.process_finished.emit(f"Erro durante a execução: {str(e)}")

        # Gerar relatório se metadata e config existirem
        if self.metadata_path and self.config_path:
            self.generate_report()
        else:
            print("Metadados ou configuração ausentes, executando apenas Quality_monitor.")
            try:
                reads, coverage = data_processing(self.output_folder)
                mod_pasta(self.output_folder)
                Quality_monitor(coverage, reads, self.output_folder)
            except Exception as e:
                print(f"Erro no Quality_monitor: {e}")

    def generate_report(self):
        self.process_started.emit("Gerando o relatório...")
        generate_report(
            output_folder=self.output_folder,
            metadata_path=self.metadata_path,
            config_path=self.config_path
        )
        self.process_started.emit("Relatório gerado com sucesso!\n")


class ViralFlowGUI_SC2(QWidget):
    process_finished = pyqtSignal(str)

    def __init__(self, menu_inicial):
        super().__init__()
        self.menu_inicial = menu_inicial

        self.setWindowTitle("ViralFlow GUI - SARS-CoV-2")
        self.setGeometry(100, 100, 500, 250)
        self.setWindowIcon(QIcon(os.path.expanduser("~/ViralFlow/docs/source/img/viralflow_logo.png")))

        self.param_manager = ParametersManager()
        layout = QVBoxLayout()

        # Pasta resources
        self.resources_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
    "resources"
)
        
        # Campo BED como menu flutuante
        bed_label = QLabel("Arquivo bed (Primers)")
        self.bed_combo = QComboBox()
        bed_files = [f for f in os.listdir(self.resources_path)
                     if f.startswith("SARS-CoV-2") and f.endswith(".bed")]
        self.bed_combo.addItems(bed_files)
        layout.addWidget(bed_label)
        layout.addWidget(self.bed_combo)

        # Campos adicionais
        self.fields = [
            ("Pasta de entrada", "inDir", False),
            ("Pasta de saída", "outDir", False),
            ("Metadados (.csv) [Opcional]", "metadata", True),
            ("Submission_info (.yaml) [Opcional]", "config_file", True),
        ]
        self.entries = {}
        for label_text, field_name, is_file in self.fields:
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            row_layout.addWidget(label)
            entry = QLineEdit(self)
            row_layout.addWidget(entry)
            if is_file:
                browse_button = QPushButton("Browse", self)
                browse_button.clicked.connect(lambda checked, e=entry: self.select_file(e))
                row_layout.addWidget(browse_button)
            else:
                browse_button = QPushButton("Browse", self)
                browse_button.clicked.connect(lambda checked, e=entry: self.select_folder(e))
                row_layout.addWidget(browse_button)
            layout.addLayout(row_layout)
            self.entries[field_name] = entry

        # Botões de parâmetros, execução e menu
        params_button = QPushButton("Configurar Parâmetros")
        params_button.clicked.connect(lambda: self.param_manager.configure_parameters(self))
        layout.addWidget(params_button)

        run_button = QPushButton("Executar ViralFlow", self)
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
        bed_file = os.path.join(self.resources_path, self.bed_combo.currentText())
        nextflow_path = self.get_nextflow_path()

        command_viralflow = (
            f"micromamba run -n viralflow "
            f"{nextflow_path} run ~/ViralFlow//vfnext/main.nf "
            f"--primersBED {bed_file} "
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
            f"--trimLen 0 --refGenomeCode null --referenceGFF null "
            f"--referenceGenome null -resume"
        )

        self.thread = AssemblerRun_SC2(
            command_viralflow,
            os.path.join(params['outDir'], "COMPILED_OUTPUT"),
            metadata_path=params['metadata'],
            config_path=params['config_file'],
            input_path=params['inDir']
        )

        self.thread.process_started.connect(self.update_status)
        self.thread.process_finished.connect(self.update_status)
        self.thread.start()

    def update_status(self, message):
        print(message)

    def voltar_menu_inicial(self):
        self.close()
        self.menu_inicial.show()

    def sair(self):
        confirm = QMessageBox.question(
            self, "Confirmação", "Tem certeza de que deseja sair?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            QApplication.quit()


def main():
    app = QApplication(sys.argv)
    window = ViralFlowGUI_SC2(None)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
