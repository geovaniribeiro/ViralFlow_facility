#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QDialog, QCheckBox, QSpinBox
)
import subprocess

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

#from scripts.analysis.report_generator_sc2 import generate_report


class ParametersDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Configurar Parâmetros")
        self.setGeometry(100, 100, 400, 400)

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

class ViralFlowGUI(QWidget):
    def __init__(self):
        super().__init__()

        # Inicializar a janela
        self.setWindowTitle("ViralFlow GUI")
        self.setGeometry(100, 100, 500, 250)

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


        #Customizing the snpEff database
        snpeff_custom = (
            f"NXF_VER=22.04.0 nextflow run ~/ViralFlow//vfnext/main.nf"
            f"viralflow -add_entry_to_snpeff --org_name custom --genome_code {params['refGenomeCode']}")

        # Construir o comando
        command_viralflow = (
            f"NXF_VER=22.04.0 nextflow run ~/ViralFlow//vfnext/main.nf --primersBED {params['primersBED']} "
            f"--outDir {params['outDir']} --inDir {params['inDir']} --virus custom "
            f"--runSnpEff {'true' if self.parameters['run_snp_eff'] else 'false'} "
            f"--writeMappedReads {'true' if self.parameters['write_mapped_reads'] else 'false'} "
            f"--minLen {self.parameters['min_len']} --depth {self.parameters['depth']} "
            f"--minDpIntrahost {self.parameters['min_dp_intrahost']} "
            f"--nextflowSimCalls {self.parameters['nextflow_sim_calls']} "
            f"--fastp_threads {self.parameters['fastp_threads']} "
            f"--bwa_threads {self.parameters['bwa_threads']} "
            f"--mafft_threads {self.parameters['mafft_threads']} "
            f"--trimLen 0 --refGenomeCode {params['refGenomeCode']} --referenceGFF null "
            f"--referenceGenome null -resume"
        )

        try:
            print("Running snpeff_custom...")
            subprocess.run(snpeff_custom, shell=True, check=True)
            print("snpeff_custom completed successfully.")
            subprocess.run(command_viralflow, shell=True, check=True)
            print("ViralFlow executado com sucesso!")
            print(" ")
            print(" ")
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")

        try:
            generate_report(
                output_folder=os.path.join(params['outDir'], "COMPILED_OUTPUT"),
                metadata_path=params['metadata'],
                config_path=params['config_file']
            )
            print("Relatorio e arquivos gerados com sucesso!")
            print(" ")
            print(" ")
            print("O terminal pode ser fechado ;)")
            print(" ")
        except Exception as report_error:
            print(f"Failed to generate the report: {report_error}")


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
