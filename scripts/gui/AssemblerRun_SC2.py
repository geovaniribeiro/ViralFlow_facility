#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QDialog)

from PyQt5.QtGui import QIcon


# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

#Import classes instances
from scripts.gui.ParametersDialog import ParametersDialog #Classe dos parametros ViralFlow
from scripts.gui.ParametersManager import ParametersManager #Classe parametros Deafult do ViralFlow
from scripts.analysis.assembler.assembler_thread import AssemblerThread #Instancia para iniciar uma nova thread no processo
from scripts.analysis.rename_fastq import rename_fastq_files #Função para renomear arquivos para codigo de amostras, se necessario
from scripts.analysis.report.report_generator_sc2 import generate_report #Função para gerar relatorio e arquivos de SC2
from scripts.analysis.rename_fastq import rename_fastq_files #Função para renomear arquivos para codigo de amostras, se necessario
from scripts.analysis.report.modules_general import data_processing, mod_pasta, Quality_monitor #Importa funções para gerar relatorio de qualidade

class AssemblerRun_sc2(AssemblerThread):

    def __init__(self, command_viralflow, output_folder, metadata_path, config_path, input_path):

       # Primeiro, renomeia os arquivos FASTQ antes de qualquer outra ação
        try:
            rename_fastq_files(metadata_path, input_path)
            print("")
            print("Renomeação de arquivos FASTQ concluída com sucesso!")
            print("")
            print("")
            print("")
        except Exception as e:
            raise RuntimeError(f"Erro ao renomear arquivos FASTQ: {str(e)}")  # Interrompe a inicialização se houver erro
       
       
        # Define os comandos após garantir a renomeação dos arquivos
        self.output_folder = output_folder
        self.metadata_path = metadata_path
        self.config_path = config_path
        self.input_path = input_path

        commands = [(command_viralflow, "Executando ViralFlow...")]
        super().__init__(commands)


    def run(self):
        try:
            super().run()  # Executa os comandos principais
            # Emitir o sinal de finalização com mensagem de sucesso
            self.process_finished.emit("ViralFlow executado com sucesso!")
            self.process_finished.emit(" ")
        except Exception as e:
            # Emitir o sinal de finalização com mensagem de erro
            self.process_finished.emit(f"Erro durante a execução: {str(e)}")
            
        # Se metadata_path e config_path forem válidos, gera o relatório
        if self.metadata_path and self.config_path:
            self.generate_report()
        else:
            print("Metadados ou configuração ausentes, gerando apenas análise de qualidade.")
            try:
                compiled_output_folder = self.output_folder
                reads, coverage = data_processing(compiled_output_folder)
                mod_pasta(compiled_output_folder)
                Quality_monitor(coverage, reads, compiled_output_folder)
            except Exception as e:
                print(f"Erro ao executar Quality_monitor: {e}")

    def generate_report(self):
        self.process_started.emit("""Gerando o relatório...""")
        self.process_started.emit("")
        
        generate_report(
            output_folder=self.output_folder,
            metadata_path=self.metadata_path,
            config_path=self.config_path
        )
        self.process_started.emit("Relatório gerado com sucesso!")
        self.process_started.emit(" ")

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
            ("Arquivo metadados (.csv) [Opcional]", "metadata", True),
            ("Arquivo configuração (.yaml) [Opcional]", "config_file", True),
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
            f"micromamba run -n viralflow "
            f"nextflow run ~/ViralFlow//vfnext/main.nf "
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
        self.thread = AssemblerRun_sc2(command_viralflow,
                                    os.path.join(params['outDir'], "COMPILED_OUTPUT"),
                                    metadata_path=params['metadata'],
                                    config_path=params['config_file'],
                                    input_path=params['inDir'])

        # Conectar os sinais do thread com as funções da GUI
        self.thread.process_started.connect(self.update_status)
        self.thread.process_finished.connect(self.update_status)

        # Iniciar o thread
        self.thread.start()

    def generate_report_after_run(self):
        """Gera o relatório após a execução do comando ser concluída."""
        params = {key: entry.text() for key, entry in self.entries.items()}

        # Gera o relatório
        generate_report(
            output_folder=os.path.join(params['outDir'], "COMPILED_OUTPUT"),
            metadata_path=params['metadata'],
            config_path=params['config_file']
        )

        self.update_status("Relatório gerado com sucesso!")

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
