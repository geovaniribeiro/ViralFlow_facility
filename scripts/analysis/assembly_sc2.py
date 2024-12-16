#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QDialog, QCheckBox, QSpinBox
)

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal


import subprocess

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.analysis.report_generator_sc2 import generate_report


class ParametersDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Configurar Parâmetros")
        self.setGeometry(100, 100, 400, 400)

        self.setWindowIcon(QIcon(os.path.expanduser("~/ViralFlow/docs/source/img/viralflow_logo.png")))

        layout = QVBoxLayout()

        # Parâmetros com opções booleanas (CheckBox)
        self.run_snp_eff = QCheckBox("Habilitar --runSnpEff")
        self.run_snp_eff.setChecked(True)
        layout.addWidget(self.run_snp_eff)

        self.write_mapped_reads = QCheckBox("Habilitar --writeMappedReads")
        self.write_mapped_reads.setChecked(True)
        layout.addWidget(self.write_mapped_reads)

        # Parâmetros numéricos (SpinBox)
        self.min_len_label = QLabel("Valor para --minLen")
        layout.addWidget(self.min_len_label)
        self.min_len = QSpinBox()
        self.min_len.setMinimum(0)
        self.min_len.setMaximum(1000)
        self.min_len.setValue(75)
        layout.addWidget(self.min_len)

        self.depth_label = QLabel("Valor para --depth")
        layout.addWidget(self.depth_label)
        self.depth = QSpinBox()
        self.depth.setMinimum(0)
        self.depth.setMaximum(1000)
        self.depth.setValue(10)
        layout.addWidget(self.depth)

        self.min_dp_intrahost_label = QLabel("Valor para --minDpIntrahost")
        layout.addWidget(self.min_dp_intrahost_label)
        self.min_dp_intrahost = QSpinBox()
        self.min_dp_intrahost.setMinimum(0)
        self.min_dp_intrahost.setMaximum(1000)
        self.min_dp_intrahost.setValue(100)
        layout.addWidget(self.min_dp_intrahost)

        self.nextflow_sim_calls_label = QLabel("Valor para --nextflowSimCalls")
        layout.addWidget(self.nextflow_sim_calls_label)
        self.nextflow_sim_calls = QSpinBox()
        self.nextflow_sim_calls.setMinimum(0)
        self.nextflow_sim_calls.setMaximum(300)
        self.nextflow_sim_calls.setValue(12)
        layout.addWidget(self.nextflow_sim_calls)

        self.fastp_threads_label = QLabel("Valor para --fastp_threads")
        layout.addWidget(self.fastp_threads_label)
        self.fastp_threads = QSpinBox()
        self.fastp_threads.setMinimum(0)
        self.fastp_threads.setMaximum(300)
        self.fastp_threads.setValue(12)
        layout.addWidget(self.fastp_threads)

        self.bwa_threads_label = QLabel("Valor para --bwa_threads")
        layout.addWidget(self.bwa_threads_label)
        self.bwa_threads = QSpinBox()
        self.bwa_threads.setMinimum(0)
        self.bwa_threads.setMaximum(300)
        self.bwa_threads.setValue(12)
        layout.addWidget(self.bwa_threads)

        self.mafft_threads_label = QLabel("Valor para --mafft_threads")
        layout.addWidget(self.mafft_threads_label)
        self.mafft_threads = QSpinBox()
        self.mafft_threads.setMinimum(0)
        self.mafft_threads.setMaximum(300)
        self.mafft_threads.setValue(12)
        layout.addWidget(self.mafft_threads)

        # Botões
        button_layout = QHBoxLayout()
        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_parameters(self):
        return {
            "run_snp_eff": self.run_snp_eff.isChecked(),
            "write_mapped_reads": self.write_mapped_reads.isChecked(),
            "min_len": self.min_len.value(),
            "depth": self.depth.value(),
            "min_dp_intrahost": self.min_dp_intrahost.value(),
            "nextflow_sim_calls": self.nextflow_sim_calls.value(),
            "fastp_threads": self.fastp_threads.value(),
            "bwa_threads": self.bwa_threads.value(),
            "mafft_threads": self.mafft_threads.value(),
        }

class ParametersManager:
    def __init__(self):
        # Valores padrão
        self.parameters = {
            "run_snp_eff": True,
            "write_mapped_reads": True,
            "min_len": 75,
            "depth": 10,
            "min_dp_intrahost": 100,
            "nextflow_sim_calls": 12,
            "fastp_threads": 12,
            "bwa_threads": 12,
            "mafft_threads": 12,
        }

    def configure_parameters(self, parent=None):
        dialog = ParametersDialog(parent)
        if dialog.exec_() == QDialog.Accepted:
            self.parameters = dialog.get_parameters()


# Classe para executar o processo em um thread separado
class ProcessThread(QThread):
    process_started = pyqtSignal(str)
    process_finished = pyqtSignal(str)

    def __init__(self, command_viralflow, output_folder, metadata_path, config_path):
        super().__init__()
        self.command_viralflow = command_viralflow
        self.output_folder = output_folder
        self.metadata_path = metadata_path
        self.config_path = config_path

    def run(self):
        try:
            self.process_started.emit("Executando ViralFlow...")
            self.process_started.emit(" ")
            subprocess.run(self.command_viralflow, shell=True, check=True)
            self.process_started.emit("ViralFlow executado com sucesso!")
            self.process_started.emit(" ")
            self.process_started.emit(" ")

            # Gerar o relatório após a execução dos comandos
            self.process_started.emit("Gerando o relatório...")
            self.process_started.emit(" ")
            self.process_started.emit(" ")

            generate_report(output_folder=self.output_folder, 
                            metadata_path=self.metadata_path, 
                            config_path=self.config_path)
            self.process_started.emit("Relatório gerado com sucesso!")
            self.process_started.emit(" ")
            self.process_started.emit(" ")

            self.process_finished.emit("Processo concluído com sucesso!")
            self.process_started.emit(" ")
            self.process_started.emit(" ")

        except subprocess.CalledProcessError as e:
            self.process_finished.emit(f"Erro ao executar o comando: {e}")
        except Exception as e:
            self.process_finished.emit(f"Erro ao gerar o relatório: {e}")

class ViralFlowGUI(QWidget):
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

            # Adicionar o botão "Browse"
            browse_button = QPushButton("Browse", self)
            if is_file:
                browse_button.clicked.connect(lambda checked, e=entry: self.select_file(e))
            else:
                browse_button.clicked.connect(lambda checked, e=entry: self.select_folder(e))
            row_layout.addWidget(browse_button)

            # Adicionar a linha ao layout principal
            layout.addLayout(row_layout)
            self.entries[field_name] = entry

        # Botão de parâmetros
        params_button = QPushButton("Configurar Parâmetros")
        params_button.clicked.connect(lambda: self.param_manager.configure_parameters(self))
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
        """Constrói e executa o comando com os parâmetros configurados na GUI."""
        params = {key: entry.text() for key, entry in self.entries.items()}

        # Acessar parâmetros do ParametersManager
        command_viralflow = (
            f"nextflow run ~/ViralFlow/vfnext/main.nf "
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
            f"--trimLen 0 --refGenomeCode null --referenceGFF null "
            f"--referenceGenome null -resume"
        )

        # Iniciar o thread para executar o processo
        self.thread = ProcessThread(command_viralflow,
                                    os.path.join(params['outDir'], "COMPILED_OUTPUT"),
                                    metadata_path=params['metadata'],
                                    config_path=params['config_file'])
        
        # Conectar os sinais do thread com as funções da GUI
        self.thread.process_started.connect(self.update_status)
        self.thread.process_finished.connect(self.update_status)

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
