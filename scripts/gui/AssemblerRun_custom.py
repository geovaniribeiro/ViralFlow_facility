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
from scripts.analysis.rename_fastq import rename_fastq_files
from scripts.analysis.report.modules_general import data_processing, mod_pasta, Quality_monitor

CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUBMISSION_INFO_PATH = os.path.join(CONFIG_DIR, "submission_info.yaml")

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
    process_finished = Signal(str)

    def __init__(self, menu_inicial, virus="DENV"):
        super().__init__()
        self.menu_inicial = menu_inicial
        self.virus = virus  # define o vírus em execução (DENV ou CHIKV)

        self.settings = QSettings("ViralFlowGUI", "ViralFlow")

        self.setWindowTitle("ViralFlow GUI")
        self.setGeometry(100, 100, 600, 380)
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
            ("Pasta de saída", "outDir", False),
            ("Metadados (.csv) [Opcional]", "metadata", True)
        ]

        for label_text, field_name, is_file in self.fields:
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            row_layout.addWidget(label)

            if field_name == "primersBED":
                combo = QComboBox()
                self.populate_bed_files(combo)
                row_layout.addWidget(combo)
                combo.currentIndexChanged.connect(self.on_primers_changed)
                self.entries[field_name] = combo

            elif field_name == "refGenomeCode":
                if self.virus.upper() == "DENV":
                    combo = QComboBox()
                    combo.addItem("DENV1", "NC_001477.1")
                    combo.addItem("DENV2", "NC_001474.2")
                    combo.addItem("DENV3", "NC_001475.2")
                    combo.addItem("DENV4", "NC_002640.1")
                    combo.currentIndexChanged.connect(self.on_refseq_changed)
                    row_layout.addWidget(combo)
                    self.entries[field_name] = combo
                elif self.virus.upper() == "CHIKV":
                    hidden_entry = QLineEdit()
                    hidden_entry.setText("NC_004162.2")
                    hidden_entry.setVisible(False)
                    self.entries[field_name] = hidden_entry

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

    # -----------------------------
    # Métodos auxiliares
    # -----------------------------
    def populate_bed_files(self, combo):
        resources_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "resources"
        )
        if not os.path.isdir(resources_dir):
            return
        beds = []
        for f in os.listdir(resources_dir):
            if f.endswith(".bed"):
                if self.virus.upper() == "DENV" and f.lower().startswith("denv"):
                    beds.append(f)
                elif self.virus.upper() == "CHIKV" and f.lower().startswith("chikv"):
                    beds.append(f)
        beds.sort(key=lambda s: s.lower())
        for f in beds:
            combo.addItem(f, os.path.join(resources_dir, f))

        try:
            if "refGenomeCode" in self.entries and isinstance(self.entries["refGenomeCode"], QComboBox):
                self.sync_bed_with_refseq()
        except Exception:
            pass

    def select_file(self, entry):
        start = entry.text() or self.settings.value("last_browse_dir", os.path.expanduser("~"))
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecione um arquivo", start)
        if file_path:
            entry.setText(file_path)
            self.settings.setValue("last_browse_dir", os.path.dirname(file_path))

    def select_folder(self, entry):
        start = entry.text() or self.settings.value("last_browse_dir", os.path.expanduser("~"))
        folder_path = QFileDialog.getExistingDirectory(self, "Selecione uma pasta", start)
        if folder_path:
            entry.setText(folder_path)
            self.settings.setValue("last_browse_dir", folder_path)

    def configure_parameters(self):
        dialog = ParametersDialog(self.param_manager.parameters, self)
        if dialog.exec():
            self.param_manager.parameters = dialog.get_parameters()

    def post_processing(self):
        try:
            reads, coverage = data_processing(os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT"))
            mod_pasta(os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT"))
            Quality_monitor(coverage, reads, os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT"))
            print("Quality check realizado!")
        except Exception as e:
            print(f"Erro ao executar pós-processamento: {e}")

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
                if key == 'primersBED':
                    params[key] = entry.currentData() # O caminho completo
                    self.selected_primer_name = entry.currentText()
                else:
                    params[key] = entry.currentData()

        ref_code = None
        ref_entry = self.entries.get('refGenomeCode')
        if isinstance(ref_entry, QComboBox):
            ref_code = ref_entry.currentData() or ref_entry.currentText()
        elif isinstance(ref_entry, QLineEdit):
            ref_code = ref_entry.text()
        params['refGenomeCode'] = ref_code

        nextflow_path = self.get_nextflow_path()

        command_viralflow = (
            f"micromamba run -n viralflow {nextflow_path} run ~/ViralFlow/vfnext/main.nf "
            f"--primersBED {params.get('primersBED','')} "
            f"--outDir {params.get('outDir','')} "
            f"--inDir {params.get('inDir','')} "
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
            f"--trimLen 0 --refGenomeCode {params.get('refGenomeCode','')} "
            f"--referenceGFF null --referenceGenome null -resume"
        )

        print("Comando montado, iniciando execução...")

        self.thread = AssemblerRun_custom(
            command_viralflow,
            os.path.join(params.get('outDir', ""), "COMPILED_OUTPUT"),
            metadata_path=params.get('metadata'),
            config_path=SUBMISSION_INFO_PATH,
            input_path=params.get('inDir')
        )

        self.thread.process_started.connect(self.update_status)
        self.thread.process_finished.connect(self.update_status)
        
        if params.get('metadata'):
            if hasattr(self, "report_generator") and callable(getattr(self, "report_generator")):
                self.thread.process_finished.connect(self.report_generator)
        else:
             print("Aviso: metadata_path não foi definido, pulando a geração do relatório.")

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

    # -----------------------------
    # Sincronização RefSeq <-> BED
    # -----------------------------
    def on_refseq_changed(self, index):
        try:
            ref_combo = self.entries.get('refGenomeCode')
            bed_combo = self.entries.get('primersBED')
            if not (isinstance(ref_combo, QComboBox) and isinstance(bed_combo, QComboBox)):
                return
            accession = ref_combo.itemData(index)
            acc_map = {
                "NC_001477.1": "1",
                "NC_001474.2": "2",
                "NC_001475.2": "3",
                "NC_002640.1": "4",
            }
            sor = acc_map.get(accession)
            if not sor:
                return
            for i in range(bed_combo.count()):
                text = bed_combo.itemText(i).lower()
                if f"_{sor}" in text or f"denv{sor}" in text:
                    bed_combo.setCurrentIndex(i)
                    break
        except Exception as e:
            print(f"Erro na sincronização refseq->bed: {e}")

    def on_primers_changed(self, index):
        try:
            bed_combo = self.entries.get('primersBED')
            ref_combo = self.entries.get('refGenomeCode')
            if not (isinstance(bed_combo, QComboBox) and isinstance(ref_combo, QComboBox)):
                return
            bed_name = bed_combo.itemText(index).lower()
            for acc, sor in {
                "NC_001477.1": "1",
                "NC_001474.2": "2",
                "NC_001475.2": "3",
                "NC_002640.1": "4"
            }.items():
                if f"_{sor}" in bed_name or f"denv{sor}" in bed_name:
                    for i in range(ref_combo.count()):
                        if ref_combo.itemData(i) == acc:
                            ref_combo.setCurrentIndex(i)
                            return
        except Exception as e:
            print(f"Erro na sincronização bed->refseq: {e}")

    def sync_bed_with_refseq(self):
        try:
            ref_combo = self.entries.get('refGenomeCode')
            bed_combo = self.entries.get('primersBED')
            if not (isinstance(ref_combo, QComboBox) and isinstance(bed_combo, QComboBox)):
                return
            accession = ref_combo.currentData()
            acc_map = {
                "NC_001477.1": "1",
                "NC_001474.2": "2",
                "NC_001475.2": "3",
                "NC_002640.1": "4",
            }
            sor = acc_map.get(accession)
            if not sor:
                return
            for i in range(bed_combo.count()):
                text = bed_combo.itemText(i).lower()
                if f"_{sor}" in text or f"denv{sor}" in text:
                    bed_combo.setCurrentIndex(i)
                    break
        except Exception:
            pass


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

