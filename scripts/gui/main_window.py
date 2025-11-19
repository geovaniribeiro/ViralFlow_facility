#!/usr/bin/env python3

import yaml
from PySide6.QtWidgets import (
    QApplication, QVBoxLayout, QLabel, QPushButton, QWidget, QMessageBox, QRadioButton,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QGroupBox)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QThread, Signal
import subprocess
import os
import sys
import matplotlib
matplotlib.use('Agg')

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.gui.AssemblerRun_SC2 import ViralFlowGUI_SC2  # Interface para SARS-CoV-2
from scripts.gui.AssemblerRun_custom import ViralFlowGUI as ViralFlowGUI_custom  # Interface para vírus customizados
from scripts.gui.AssemblerRun_OROV import ViralFlowOROV  # Interface para OROV
from scripts.utilities.update_database import atualizar_banco_dados  # Função para atualizar banco de dados
from scripts.utilities.update_viralflow import atualizar_viralflow  # Função para atualizar viralflow
from scripts.utilities.update_GUI import atualizar_GUI  # Função para atualizar viralflow
from scripts.analysis.report.report_generator_denv import generate_report_denv  # Classe para geração de relatórios
from scripts.analysis.report.report_generator_chikv import generate_report_chikv  # Classe para geração de relatórios
from scripts.analysis.nextclade_runners import DenvNextclade, ChikvNextclade # Classes para rodar Nextclade (genotyping e linhagem)

# --- Bloco de código para FORÇAR ASPAS no YAML ---
class ForceQuote(str):
    pass

def force_quote_representer(dumper, data):
    """
    Define um 'representer' para o PyYAML que força aspas duplas (style='"').
    """
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(ForceQuote, force_quote_representer)

CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUBMISSION_INFO_PATH = os.path.join(CONFIG_DIR, "submission_info.yaml")
# --- Bloco de código para FORÇAR ASPAS no YAML ---

class WorkerThread(QThread):
    finished = Signal()
    error = Signal(str)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.function(*self.args, **self.kwargs)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class SubmissionInfoDialog(QDialog):
    """
    Uma janela de diálogo para carregar, editar e salvar
    o arquivo Submission_info.yaml.
    """
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Informações do Submissor")
        self.file_path = file_path
        self.data = {}

        self.setMinimumWidth(600)

        # Layout
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Campos
        self.fields = {
            'submitter': QLineEdit(),
            'subm_lab': QLineEdit(),
            'subm_lab_addr': QLineEdit(),
            'authors': QLineEdit()
        }
        
        form_layout.addRow("Submitter (usuário GISAID/EpiArbo):", self.fields['submitter'])
        form_layout.addRow("Laboratório (submissor):", self.fields['subm_lab'])
        form_layout.addRow("Endereço do Laboratório:", self.fields['subm_lab_addr'])
        form_layout.addRow("Autores:", self.fields['authors'])

        layout.addLayout(form_layout)

        # Botões Salvar/Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_data)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.load_data()

    def load_data(self):
        """Carrega os dados do arquivo YAML, se existir."""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    self.data = yaml.safe_load(f)
                
                info = self.data.get('user_info', {})
                self.fields['submitter'].setText(info.get('submitter', ''))
                self.fields['subm_lab'].setText(info.get('subm_lab', ''))
                self.fields['subm_lab_addr'].setText(info.get('subm_lab_addr', ''))
                self.fields['authors'].setText(info.get('authors', ''))
            else:
                print(f"Arquivo de configuração não encontrado em {self.file_path}. Campos estarão em branco.")

        except Exception as e:
            QMessageBox.critical(self, "Erro ao Carregar", f"Não foi possível ler o arquivo YAML: {e}")

    def save_data(self):
        """Salva os dados dos campos de volta no arquivo YAML."""
        # Garante que o diretório de configuração exista
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        self.data['user_info'] = {
            'submitter': self.fields['submitter'].text(),
            'subm_lab': ForceQuote(self.fields['subm_lab'].text()),
            'subm_lab_addr': ForceQuote(self.fields['subm_lab_addr'].text()),
            'authors': ForceQuote(self.fields['authors'].text())}

        try:
            with open(self.file_path, 'w') as f:
                yaml.dump(self.data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            QMessageBox.information(self, "Sucesso", "Informações salvas com sucesso!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", f"Não foi possível salvar o arquivo YAML: {e}")

class MenuInicial(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu Inicial - ViralFlow GUI")
        self.setGeometry(200, 200, 600, 300)
        self.setWindowIcon(QIcon(os.path.expanduser("~/ViralFlow/docs/source/img/viralflow_logo.png")))

        main_layout = QVBoxLayout()
        #main_layout.addWidget(QLabel("Escolha uma opção:"))

        # --- 1. Grupo de Utilitários ---
        util_group = QGroupBox("Utilitários")
        util_layout = QVBoxLayout()
        
        update_button = QPushButton("Atualizar Interface")
        update_button.clicked.connect(self.atualizar_GUI)
        util_layout.addWidget(update_button)

        update_viralflow_btn = QPushButton("Atualizar ViralFlow")
        update_viralflow_btn.clicked.connect(self.atualizar_viralflow)
        util_layout.addWidget(update_viralflow_btn)

        db_update_button = QPushButton("Atualizar Banco de dados")
        db_update_button.clicked.connect(self.atualizar_banco_dados)
        util_layout.addWidget(db_update_button)
        
        util_group.setLayout(util_layout)
        main_layout.addWidget(util_group)

        # --- 2. Grupo de Cadastro ---
        cadastro_group = QGroupBox("Cadastro")
        cadastro_layout = QVBoxLayout()
        
        self.info_button = QPushButton("Cadastrar Informações do Submissor")
        self.info_button.clicked.connect(self.abrir_info_dialog)
        cadastro_layout.addWidget(self.info_button)
        
        cadastro_group.setLayout(cadastro_layout)
        main_layout.addWidget(cadastro_group)

        # --- 3. Grupo de Análises ---
        analise_group = QGroupBox("Análises")
        analise_layout = QVBoxLayout()
        
        self.radio_sc2 = QRadioButton("SARS-CoV-2")
        self.radio_denv = QRadioButton("DENV")
        self.radio_chikv = QRadioButton("CHIKV")
        self.radio_orov = QRadioButton("OROV")
        analise_layout.addWidget(self.radio_sc2)
        analise_layout.addWidget(self.radio_denv)
        analise_layout.addWidget(self.radio_chikv)
        analise_layout.addWidget(self.radio_orov)
        
        # Iniciar Análise
        confirm_button = QPushButton("Iniciar Análise")
        confirm_button.clicked.connect(self.executar_analise)
        analise_layout.addWidget(confirm_button)
        
        analise_group.setLayout(analise_layout)
        main_layout.addWidget(analise_group)

        # Espaçador para empurrar o botão Sair para baixo
        main_layout.addStretch(1) 

        # Botão de Sair (fora dos grupos)
        exit_button = QPushButton("Sair")
        exit_button.clicked.connect(self.sair)
        main_layout.addWidget(exit_button)

        self.setLayout(main_layout)

    def atualizar_GUI(self):
        if QMessageBox.question(self, "Confirmação", "Você deseja atualizar a interface?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.thread = WorkerThread(atualizar_GUI)
            self.thread.error.connect(lambda msg: QMessageBox.critical(self, "Erro", msg))
            self.thread.start()

    def atualizar_viralflow(self):
        if QMessageBox.question(self, "Confirmação", "Você deseja atualizar o ViralFlow?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.thread = WorkerThread(atualizar_viralflow)
            self.thread.error.connect(lambda msg: QMessageBox.critical(self, "Erro", msg))
            self.thread.start()

    def atualizar_banco_dados(self):
        if QMessageBox.question(self, "Confirmação", "Atualizar banco de dados? Isso pode levar algum tempo.", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.thread_banco = WorkerThread(atualizar_banco_dados)
            self.thread_banco.finished.connect(lambda: QMessageBox.information(self, "Sucesso", "Banco de dados atualizado!"))
            self.thread_banco.error.connect(lambda msg: QMessageBox.critical(self, "Erro", msg))
            self.thread_banco.start()

    def abrir_info_dialog(self):
        """Abre a janela de diálogo para editar o Submission_info.yaml."""
        dialog = SubmissionInfoDialog(SUBMISSION_INFO_PATH, self)
        dialog.exec()

    def executar_analise(self):
        if self.radio_sc2.isChecked():
            self.close()
            self.tela_assembly = ViralFlowGUI_SC2(self)
            self.tela_assembly.show()
        elif self.radio_denv.isChecked():
            self.close()
            self.tela_assembly = ViralFlowDENV(self)
            self.tela_assembly.show()
        elif self.radio_chikv.isChecked():
            self.close()
            self.tela_assembly = ViralFlowCHIKV(self)
            self.tela_assembly.show()
        elif self.radio_orov.isChecked(): # Se você adicionou um QRadioButton para OROV
            self.close()
            self.tela_assembly = ViralFlowOROV(self)
            self.tela_assembly.show()
        else:
                # Adicionado um aviso caso nada seja selecionado
                QMessageBox.warning(self, "Seleção Inválida", "Por favor, selecione um vírus para iniciar a análise.")

    def sair(self):
        if QMessageBox.question(self, "Confirmação", "Deseja sair?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            QApplication.quit()


class ViralFlowVirusHandler(ViralFlowGUI_custom):
    def __init__(self, menu_inicial=None, virus=None):
        super().__init__(menu_inicial, virus=virus)
        self.menu_principal = menu_inicial
        
        # Dicionário de configuração para cada vírus
        self.virus_config = {
            "DENV": {"processor": DenvNextclade, "report_func": generate_report_denv},
            "CHIKV": {"processor": ChikvNextclade, "report_func": generate_report_chikv}
        }

    def report_generator(self, message):
        """
        Este método usa o dicionário de configuração para chamar o processador e a função de relatório.
        """
        config = self.virus_config.get(self.virus)
        if not config:
            QMessageBox.critical(self, "Erro", f"Configuração para o vírus '{self.virus}' não encontrada.")
            return

        try:
            metadata_path = self.entries['metadata'].text()
            config_path = SUBMISSION_INFO_PATH
            output_folder = os.path.join(self.entries['outDir'].text(), "COMPILED_OUTPUT")
            primer_version = self.selected_primer_name

            print(f"\nGerando relatório {self.virus}...")
            
            processor = config["processor"](output_folder)
            processor.execute_pipeline()
            
            config["report_func"](metadata_path, config_path, output_folder, primer_version)
            
            print("\nRelatório gerado com sucesso")
            QMessageBox.information(self, "Relatório", f"Relatório {self.virus} gerado com sucesso.")
        except KeyError as e:
            QMessageBox.critical(self, "Erro", f"Campo não encontrado: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar relatório {self.virus}: {str(e)}")


class ViralFlowDENV(ViralFlowVirusHandler):
    def __init__(self, menu_inicial=None):
        super().__init__(menu_inicial, virus="DENV")


class ViralFlowCHIKV(ViralFlowVirusHandler):
    def __init__(self, menu_inicial=None):
        super().__init__(menu_inicial, virus="CHIKV")

#class ViralFlowOROV(ViralFlowVirusHandler):
    #def __init__(self, menu_inicial=None):
        #super().__init__(menu_inicial, virus="OROV")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("ViralFlowGUI")
    menu = MenuInicial()
    menu.show()
    sys.exit(app.exec())