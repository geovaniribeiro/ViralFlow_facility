#!/usr/bin/env python3

import sys
import os
import subprocess
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QComboBox, QGroupBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QSettings


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.gui.ParametersDialog import ParametersDialog
from scripts.gui.ParametersManager import ParametersManager
from scripts.analysis.assembler.assembler_thread import AssemblerThread

class AssemblerRun_custom(AssemblerThread):
    def __init__(self, snpeff_custom, command_viralflow, output_folder, input_path):
        commands = [
            (snpeff_custom, "Iniciando snpeff_custom..."),
            (command_viralflow, "Executando ViralFlow...")
        ]
        super().__init__(commands)
        self.output_folder = output_folder
        self.input_path = input_path

    def run(self):
        try:
            super().run()
            self.process_finished.emit("ViralFlow executado com sucesso!")
        except Exception as e:
            self.process_finished.emit(f"Erro: {str(e)}")


class ViralFlowGUI(QWidget):
    process_finished = Signal(str)

    def __init__(self, menu_inicial):
        super().__init__()
        self.menu_inicial = menu_inicial

        self.setWindowTitle("ViralFlow GUI")
        self.setGeometry(100, 100, 500, 250)
        self.setWindowIcon(QIcon(os.path.expanduser("~/ViralFlow/docs/source/img/viralflow_logo.png")))

        self.param_manager = ParametersManager()
        main_layout = QVBoxLayout()
        self.entries = {}


        # -------------------------
        # Grupo: Dados de entrada
        # -------------------------
        
        input_group = QGroupBox("Dados de entrada")
        input_layout = QVBoxLayout()
        
        self.fields = [
            ("Código refseq", "refGenomeCode", False),
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
                    
                    if field_name != "refGenomeCode":
                        # CRIA o botão apenas se NÃO for 'refGenomeCode'
                        browse_button = QPushButton("Browse", self)
                        
                        # Configura a ação do botão
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

        # Botões
        params_button = QPushButton("Configurar Parâmetros")
        params_button.clicked.connect(self.configure_parameters)
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

        self.setLayout(exec_layout)
        self.parameters = {
            "run_snp_eff": True,
            "write_mapped_reads": True,
            "min_len": 75,
            "depth": 10,
            "min_dp_intrahost": 100,
        }
        self.thread = None

        exec_group.setLayout(exec_layout)
        main_layout.addWidget(exec_group)

        self.setLayout(main_layout)
        self.thread = None

    # -----------------------------
    # Métodos auxiliares
    # -----------------------------

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

    def get_nextflow_path(self):
        try:
            result = subprocess.run(["which", "nextflow"], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "nextflow"

    def run_command(self):
        params = {key: entry.text() for key, entry in self.entries.items()}

        nextflow_path = self.get_nextflow_path()
        snpeff_custom = f"micromamba run -n viralflow bash ~/ViralFlow/vfnext/containers/add_entries_SnpeffDB.sh custom {params['refGenomeCode']}"

        #Arquivo bed como opcional
        primers_bed_path = params.get('primersBED', '').strip() 
        primers_bed_param = ""
        if primers_bed_path:
            primers_bed_param = f"--primersBED {primers_bed_path} "

        command_viralflow = (
            f"micromamba run -n viralflow {nextflow_path} run ~/ViralFlow/vfnext/main.nf "
            f"{primers_bed_param}" 
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
                                          input_path=params.get('inDir'))
        self.thread.process_started.connect(self.update_status)
        self.thread.process_finished.connect(self.update_status)
        self.thread.start()

    def update_status(self, message):
        print(message)

    def voltar_menu_inicial(self):
        self.close()
        self.menu_inicial.show()

    def sair(self):
        if QMessageBox.question(self, "Confirmação", "Deseja sair?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
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
    window = ViralFlowGUI(None)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()