#!/usr/bin/env python3
import sys
import os
from unidecode import unidecode
import pandas as pd
import csv
import subprocess
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QComboBox, QGroupBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QSettings
from scripts.gui.AssemblerRun_custom import ViralFlowGUI, AssemblerRun_custom # Importa a base
from scripts.analysis.report.modules_general import padronizar_colunas,load_config, data_processing, \
                                                    mod_pasta, Quality_monitor, Quality_monitor_interactive
from scripts.analysis.report.report_generator_denv import gerar_arquivo_fasta, arquivo_epiarbo 
from scripts.analysis.report.report_generator_orov import generate_compiled_report_orov
from scripts.analysis.rename_fastq import rename_fastq_files

# Assegura que o PYTHONPATH encontre os módulos necessários
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUBMISSION_INFO_PATH = os.path.join(CONFIG_DIR, "submission_info.yaml")

# --- Mapeamento Segmentado ---
SEGMENTS = [
    {"segment": "L", "accession": "OL689334.1"},
    {"segment": "M", "accession": "OL689333.1"},
    {"segment": "S", "accession": "OL689332.1"},
]

# =========================================================================
COLUNAS_MAPEADAS = {
    "Código_da_Amostra": [r"C[oó]digo[_ ]*Amostra", r"C[oó]digo[_ ]*(?:da[_ ])*Amostra", r"C[oó]digo\s*(?:da\s*)?Amostra"],
    "Requisição": [r"^(Requisiç[ãa]o)$", r"^(Requisicao)$", r"^(Requisiç[ãa]o[_ ]*GAL)$", r"^(Requisicao[_ ]*GAL)$"],
    "Municipio_do_Solicitante": [r"Munic[ií]pio\s*(?:do\s*)?(?:Requisitante|Solicitante)"],
    "Estado_do_Solicitante": [r"Estado\s*(?:do\s*)?(?:Requisitante|Solicitante)"],
    "CNES_Laboratório_responsável": [r"CNES\s*(?:do\s*)?Laboratório\s*[Rr]espons[aá]vel" , r"CNES[_ ]*Laboratorio[_ ]*Responsavel"]
}

def _prepare_and_rename_metadata(metadata_path, input_path):
    """ 
    Carrega, padroniza as colunas e executa a renomeação dos arquivos FASTQ
    em memória, eliminando a dependência do script externo.
    """
    
    # 1. Carrega o metadado bruto e detecta delimitador
    with open(metadata_path, 'r', encoding='latin-1') as file:
        sample = file.read(1024)
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter

    metadata = pd.read_csv(metadata_path, sep=delimiter, encoding='latin-1', on_bad_lines='skip')
    
    # 2. Padroniza colunas
    metadata.columns = metadata.columns.map(unidecode) # Limpa acentos
    metadata.columns = metadata.columns.str.replace(' ', '_') # Limpa espaços
    padronizar_colunas(metadata, COLUNAS_MAPEADAS) # Aplica o RegEx

    # 3. Validação final
    required_cols = ['Código_da_Amostra', 'Requisição']
    if not set(required_cols).issubset(metadata.columns):
        raise ValueError(
            f"As colunas necessárias {required_cols} não foram encontradas no metadado após a padronização. "
        )

    # 4. Cria o dicionário de renomeação (Requisição -> Código Amostra)
    metadata['Requisição'] = metadata['Requisição'].astype(str)
    metadata['Código_da_Amostra'] = metadata['Código_da_Amostra'].astype(str)
    requisicao_to_codigo = dict(zip(metadata['Requisição'], metadata['Código_da_Amostra']))
    
    # 5. Executa a renomeação (In-place)
    renamed_count = 0
    for filename in os.listdir(input_path):
        if "fastq" in filename or "fq" in filename:
            file_path = os.path.join(input_path, filename)
            sample_name = filename.split("_")[0] 

            if sample_name in metadata['Código_da_Amostra'].values:
                continue

            if sample_name in requisicao_to_codigo:
                new_code = requisicao_to_codigo[sample_name]
                new_name = new_code + filename[filename.index("_"):]
                new_path = os.path.join(input_path, new_name)
                
                os.rename(file_path, new_path)
                renamed_count += 1
    
    if renamed_count > 0:
         print(f"Renomeação de arquivos FASTQ concluída ({renamed_count} arquivos renomeados).")
    else:
         print("Renomeação de arquivos FASTQ pulada (arquivos já renomeados ou sem correspondência).")

class ViralFlowOROV(ViralFlowGUI):
    def __init__(self, menu_inicial):
        # A classe base ViralFlowGUI precisa de um argumento 'virus'
        super().__init__(menu_inicial, virus="OROV")
        self.menu_principal = menu_inicial
        self.current_segment_index = 0
        self.segment_commands = []
        self.initial_params = {}
        
        # O self.thread da classe base será reescrito a cada segmento

        try:
            self.run_button.clicked.disconnect()
        except Exception:
            pass # Ignora se não houver conexão anterior
            
        self.run_button.clicked.connect(self.run_command)

    def report_generator_OROV(self, message):
        """
        Gera o relatório OROV após as 3 execuções.
        Compila e salva o relatório de QC na pasta OROV_COMPILED_OUT.
        """
        
        # --- 1. DEFINIÇÃO E CRIAÇÃO DA PASTA COMPILADA ---
        COMPILED_DIR = os.path.join(self.initial_params['outDir'], "OROV_COMPILED_OUT")
        os.makedirs(COMPILED_DIR, exist_ok=True) # Cria a pasta se não existir
        
        # Identifica a pasta do último segmento (temporário para carregar os dados)
        LAST_SEGMENT_INFO = SEGMENTS[-1]
        FINAL_SEGMENT = LAST_SEGMENT_INFO['segment']
        LAST_SEGMENT_OUTPUT_DIR = os.path.join(
            self.initial_params['outDir'], 
            f"OROV_{FINAL_SEGMENT}",
            "COMPILED_OUTPUT" # Local onde o ViralFlow salvou os arquivos do último segmento
        )

        try:

            # ATENÇÃO: Carregamos os dados do ÚLTIMO SEGMENTO. 
            reads, coverage, errors = data_processing(LAST_SEGMENT_OUTPUT_DIR) 
            
            # 2. Criar a pasta RNSG_REPORT no novo local centralizado
            #mod_pasta(COMPILED_DIR)

            # 3. Gerar o relatório de QC final (HTML) no diretório COMPILADO
            Quality_monitor_interactive(
                coverage, 
                reads, 
                errors, 
                COMPILED_DIR,
                eligibility_threshold=60,
                report_title="Relatório Final OROV (Amostras Positivas - QC Consolidado)"
            )
            
            print("\nPipeline OROV completo!")
            QMessageBox.information(self, "Relatório OROV", "Pipeline OROV (L, M, S) concluído com sucesso.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro no Relatório", f"Falha ao gerar relatório OROV final: {str(e)}")


    def run_segment_step(self, message=""):
        """
        Função de loop principal, chamada a cada conclusão de segmento.
        Gera o relatório de QC do segmento que acabou de finalizar antes de iniciar o próximo.
        """
        
        # O índice do segmento que acabou de ser concluído é o 'index - 1'
        finished_index = self.current_segment_index - 1 

        # --- 1. Geração de Relatório de QC para o Segmento ANTERIOR (Finalizado) ---
        if finished_index >= 0:
            segment_info = SEGMENTS[finished_index]
            segment_name = segment_info['segment']
            
            # Obter a pasta de saída do segmento que acabou de terminar
            segment_output_dir = os.path.join(
                self.initial_params['outDir'],
                f"OROV_{segment_name}"
            )
            
            # Gerar o relatório de qualidade (QC) específico daquele segmento
            self.generate_segment_qc(segment_output_dir, segment_name)
        
        # --- 2. Disparar Relatório Final ou Próximo Segmento ---
        
        if self.current_segment_index >= len(SEGMENTS):
            print("Todos os segmentos concluídos. Disparando relatório final...")
            print("")
            # Chama a função que será desenvolvida para agregação de dados e relatório final
            self.report_generator_OROV("Execução Multi-Segmento Concluída.")
            return

        # 3. Iniciar o Próximo Segmento
        segment_info = SEGMENTS[self.current_segment_index]
        segment_name = segment_info['segment']
        accession = segment_info['accession']

        print(f"\n--- INICIANDO MONTAGEM DO SEGMENTO: OROV {segment_name} ---")

        # Definir Pasta de Saída Específica
        segment_output_dir = os.path.join(
            self.initial_params['outDir'],
            f"OROV_{segment_name}"
        )
        os.makedirs(segment_output_dir, exist_ok=True)
        
        # Sincronizar e Montar Comando
        primer_filename = f"orov_{segment_name.lower()}_primers.bed"
        bed_path = os.path.join(self.initial_params['resources_path'], primer_filename)


        command_viralflow = (
            f"micromamba run -n viralflow nextflow run ~/ViralFlow/vfnext/main.nf "
            f"--primersBED {bed_path} "
            f"--outDir {segment_output_dir} "
            f"--inDir {self.initial_params['inDir']} "
            f"--virus custom "
            f"--refGenomeCode {accession} " # Usa o código de acesso específico do segmento
            f"--runSnpEff {'true' if self.param_manager.parameters['run_snp_eff'] else 'false'} "
            f"--writeMappedReads {'true' if self.param_manager.parameters['write_mapped_reads'] else 'false'} "
            f"--minLen {self.param_manager.parameters['min_len']} "
            f"--depth {self.param_manager.parameters['depth']} "
            f"--minDpIntrahost {self.param_manager.parameters['min_dp_intrahost']} "
            f"--nextflowSimCalls {self.param_manager.parameters['nextflow_sim_calls']} "
            f"--fastp_threads {self.param_manager.parameters['fastp_threads']} "
            f"--bwa_threads {self.param_manager.parameters['bwa_threads']} "
            f"--mafft_threads {self.param_manager.parameters['mafft_threads']} "
            f"--trimLen 0 "
            f"--referenceGFF null --referenceGenome null -resume"
        )

        # Executar o Segmento
        self.thread = AssemblerRun_custom(
            command_viralflow,
            segment_output_dir, # Pasta de saída específica
            self.initial_params['metadata'],
            self.initial_params['config_path'],
            self.initial_params['input_path']
        )
        
        # Conecta o sinal de finalização À PRÓXIMA ETAPA (self.run_segment_step)
        self.thread.process_finished.connect(self.run_segment_step)
        self.thread.process_started.connect(self.update_status)
        self.thread.start()

        self.current_segment_index += 1


    def generate_segment_qc(self, output_folder, segment_name):
        """ Gera o relatório de QC (apenas) para um segmento individual (L, M, ou S). """
        try:
            # 1. Definir o caminho de saída do ViralFlow
            segment_folder = f"OROV_{segment_name}"
            base_output = os.path.join(
                self.entries['outDir'].text(),
                segment_folder,
                "COMPILED_OUTPUT") # Este é o caminho do output do ViralFlow
            
            # Garantir que a pasta do ViralFlow existe (para segurança)
            os.makedirs(base_output, exist_ok=True) 

            # 2. Carregar dados
            reads, coverage, errors = data_processing(base_output)

            # --- CORREÇÃO: CRIAR A PASTA RNSG_REPORT ANTES DE ESCREVER ---
            mod_pasta(base_output) 
            # -------------------------------------------------------------

            # Limiar de QC
            threshold = 60

            Quality_monitor(coverage, reads, base_output)

            # 3. Chamada ao monitor (que agora consegue escrever o arquivo)
            Quality_monitor_interactive(
                coverage,
                reads,
                errors,
                base_output,
                eligibility_threshold=threshold,
                report_title=f"Segmento OROV {segment_name}" # Passar o título customizado
            )

            print(f"QC do Segmento OROV {segment_name} gerado!")

        except Exception as e:
            # Inclui o caminho no erro para debug
            print(f"Aviso: Falha ao gerar relatório QC para o Segmento {segment_name}. Base: {base_output}. Erro: {e}")
            QMessageBox.critical(self, "Erro QC Segmento", f"Falha no QC OROV {segment_name}: {str(e)}")


    def report_generator_OROV(self, message):
        """
        Função final que inicia o processo de compilação de dados OROV (L, M, S).
        """
        # --- DEFINIÇÃO DOS PARÂMETROS ---
        metadata_path = self.initial_params['metadata']
        base_out_dir = self.initial_params['outDir']
        config_path = self.initial_params['config_path']
        
        # Cria a pasta de saída compilada
        COMPILED_DIR = os.path.join(base_out_dir, "OROV_COMPILED_OUT")
        os.makedirs(COMPILED_DIR, exist_ok=True)
        # --- FIM DA DEFINIÇÃO ---
        
        try:
            compiled_coverage, compiled_reads = generate_compiled_report_orov(
                metadata_path,
                base_out_dir,
                config_path
            )

            print("\nPipeline OROV completo. Relatório Compilado de QC gerado.")
            QMessageBox.information(self, "Relatório OROV", "Pipeline OROV (L, M, S) concluído. Relatório Compilado Gerado.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro no Relatório", f"Falha ao gerar relatório OROV final: {str(e)}")

    def run_command(self):
        """
        Sobrescreve o método run_command para iniciar a execução em cadeia.
        """
        params = {}
        for key, entry in self.entries.items():
            # Simplificando a leitura dos parâmetros aqui
            if isinstance(entry, QComboBox):
                params[key] = entry.currentData()
            else:
                params[key] = entry.text()

        # Armazenar parâmetros iniciais e recursos
        self.initial_params = {
            'outDir': params['outDir'],
            'inDir': params['inDir'],
            'metadata': params.get('metadata'),
            'config_path': SUBMISSION_INFO_PATH, # Hardcoded
            'resources_path': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "resources"),
            'input_path': params['inDir']
        }
        self.current_segment_index = 0
        
        # PADRONIZAÇÃO E RENOMEAÇÃO INICIAL
        metadata_path = self.initial_params['metadata']
        input_path = self.initial_params['input_path']

        if metadata_path and input_path:
            try:
                # 1. Carrega e Padroniza o metadado
                # (Assumindo que você importou/copiou padronizar_colunas e colunas_mapeadas)
                # Você deve incluir um bloco try/except robusto aqui que detecte o delimitador
                # Como não temos a função aqui, vou usar um placeholder:
                _prepare_and_rename_metadata(metadata_path, input_path)

                #print("Iniciando pré-processamento e renomeação de arquivos FASTQ...")
                
                # CHAME A FUNÇÃO DE PADRONIZAÇÃO DE COLUNAS AQUI!
                # Exemplo: padronizar_metadata_e_salvar(metadata_path, self.colunas_mapeadas)

                # 2. Renomeia os arquivos FASTQ
                # Este é o comando que você precisa garantir que funcione com o metadado padronizado
                #rename_fastq_files(metadata_path, input_path) 
                #print("Renomeação de arquivos FASTQ concluída!")
                
            except Exception as e:
                QMessageBox.critical(self, "Erro de Metadados", 
                    f"Falha ao pré-processar metadados ou renomear FASTQ. Erro: {str(e)}")
                return # Interrompe a execução

        # Desconecta qualquer sinal anterior que possa ter sido conectado.
        if self.thread and self.thread.isRunning():
            self.thread.process_finished.disconnect()

        # Inicia o loop para o primeiro segmento (L)
        self.run_segment_step("Iniciando Pipeline OROV Multi-Segmento...")