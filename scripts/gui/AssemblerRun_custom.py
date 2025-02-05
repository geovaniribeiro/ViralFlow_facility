#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QDialog, QCheckBox, QSpinBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal

import pandas as pd
import subprocess

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

#Import classes instances
from scripts.gui.ParametersDialog import ParametersDialog #Classe dos parametros ViralFlow
from scripts.gui.ParametersManager import ParametersManager #Classe parametros Deafult do ViralFlow
from scripts.analysis.assembler.assembler_thread import AssemblerThread #Classe para iniciar uma nova thread no processo


# Classe para executar o processo em um thread separado
class AssemblerRun_custom(AssemblerThread):
    def __init__(self, snpeff_custom, command_viralflow, output_folder, metadata_path, config_path, run_pipeline=None):
        commands = [
            (snpeff_custom, "Iniciando snpeff_custom..."),
            (command_viralflow, "Executando ViralFlow...")
        ]
        super().__init__(commands)
        self.output_folder = output_folder
        self.metadata_path = metadata_path
        self.config_path = config_path
        self.run_pipeline = run_pipeline

    def run(self):
        try:
            super().run()  # Executa os comandos principais
            # Emitir o sinal de finalização com mensagem de sucesso
            self.process_finished.emit("ViralFlow executado com sucesso!")
            print("")
        except Exception as e:
            # Emitir o sinal de finalização com mensagem de erro
            self.process_finished.emit(f"Erro durante a execução: {str(e)}")

class ViralFlowGUI(QWidget):
    
    process_finished = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # Inicializar a janela
        self.setWindowTitle("ViralFlow GUI")
        self.setGeometry(100, 100, 500, 250)

        # Gerenciar os parâmetros
        self.param_manager = ParametersManager()


        self.setWindowIcon(QIcon(os.path.expanduser("~/ViralFlow/docs/source/img/viralflow_logo.png")))
        
        # Criar o layout principal
        layout = QVBoxLayout()

        # Definir os campos de entrada
        self.fields = [
            ("Arquivo bed (Primers)", "primersBED", True),
            ("Pasta de entrada", "inDir", False),
            ("Pasta de saída", "outDir", False),
            ("Código refseq", "refGenomeCode", False),
            ("Arquivo metadados (.csv)", "metadata", True),
            ("Arquivo configuração (.yaml)", "config_file", True),
        ]

        # Criar dicionário para armazenar os campos de entrada
        self.entries = {}

        # Criar os campos de entrada e botões "Browse"
        for label_text, field_name, is_file in self.fields:
            row_layout = QHBoxLayout()

            # Adicionar o rótulo
            label = QLabel(label_text)
            row_layout.addWidget(label)

            # Adicionar o campo de texto
            entry = QLineEdit(self)
            row_layout.addWidget(entry)

            # Adicionar o botão "Browse" (exceto para refGenomeCode)
            if field_name != "refGenomeCode":
                browse_button = QPushButton("Browse", self)
                if is_file:
                    browse_button.clicked.connect(lambda checked, e=entry: self.select_file(e))
                else:
                    browse_button.clicked.connect(lambda checked, e=entry: self.select_folder(e))
                row_layout.addWidget(browse_button)

            # Adicionar a linha ao layout principal
            layout.addLayout(row_layout)
            self.entries[field_name] = entry

        # Botão para configurar os parâmetros adicionais
        params_button = QPushButton("Configurar Parâmetros", self)
        params_button.clicked.connect(self.configure_parameters)
        layout.addWidget(params_button)

        # Botão para executar o comando
        run_button = QPushButton("Executar ViralFlow", self)
        run_button.clicked.connect(self.run_command)
        layout.addWidget(run_button)

        # Botão para sair
        exit_button = QPushButton("Sair")
        exit_button.clicked.connect(self.sair)
        layout.addWidget(exit_button)

        self.setLayout(layout)

        # Inicializar parâmetros padrão
        self.parameters = {
            "run_snp_eff": True,
            "write_mapped_reads": True,
            "min_len": 75,
            "depth": 10,
            "min_dp_intrahost": 100,
        }

        self.thread = None

    def select_file(self, entry):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecione um arquivo")
        if file_path:
            entry.setText(file_path)

    def select_folder(self, entry):
        folder_path = QFileDialog.getExistingDirectory(self, "Selecione uma pasta")
        if folder_path:
            entry.setText(folder_path)

    def configure_parameters(self):
        dialog = ParametersDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.parameters = dialog.get_parameters()

    def run_command(self):
        """Constrói e executa o comando com os parâmetros da GUI."""
        params = {key: entry.text() for key, entry in self.entries.items()}

        # Customizing the snpEff database
        snpeff_custom = f"bash ~/ViralFlow//vfnext/containers/add_entries_SnpeffDB.sh custom {params['refGenomeCode']}"

        # Construir o comando
        command_viralflow = (
            f"nextflow run ~/ViralFlow//vfnext/main.nf --primersBED {params['primersBED']} "
            f"--outDir {params['outDir']} --inDir {params['inDir']} --virus custom "
            f"--runSnpEff {'true' if self.param_manager.parameters['run_snp_eff'] else 'false'} "
            f"--writeMappedReads {'true' if self.param_manager.parameters['write_mapped_reads'] else 'false'} "
            f"--minLen {self.param_manager.parameters['min_len']} --depth {self.param_manager.parameters['depth']} "
            f"--minDpIntrahost {self.param_manager.parameters['min_dp_intrahost']} "
            f"--nextflowSimCalls {self.param_manager.parameters['nextflow_sim_calls']} "
            f"--fastp_threads {self.param_manager.parameters['fastp_threads']} "
            f"--bwa_threads {self.param_manager.parameters['bwa_threads']} "
            f"--mafft_threads {self.param_manager.parameters['mafft_threads']} "
            f"--trimLen 0 --refGenomeCode {params['refGenomeCode']} --referenceGFF null "
            f"--referenceGenome null -resume"
        )
        
        # Iniciar o thread para executar o processo
        self.thread = AssemblerRun_custom(snpeff_custom, command_viralflow,
                                    os.path.join(params['outDir'], "COMPILED_OUTPUT"),
                                    metadata_path=params['metadata'],
                                    config_path=params['config_file'])

        # Conectar os sinais do thread com as funções da GUI
        self.thread.process_started.connect(self.update_status)
        self.thread.process_finished.connect(self.update_status)

        # Conectar o sinal de finalização ao método apropriado
        self.thread.process_finished.connect(self.report_generator)

        # Iniciar o thread
        self.thread.start()

    def update_status(self, message):
        """Atualiza a interface com as mensagens do processo."""
        print(message)

    def sair(self):
        confirm = QMessageBox.question(
            self,
            "Confirmação",
            "Tem certeza de que deseja sair?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            QApplication.quit()

def main():
    app = QApplication(sys.argv)
    window = ViralFlowGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()