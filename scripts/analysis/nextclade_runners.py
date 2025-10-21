#!/usr/bin/env python3

import os
import time
import pandas as pd
import subprocess

class BaseNextclade:
    """
    Classe base que contém a lógica comum para executar o Nextclade.
    """
    def __init__(self, out_dir):
        self.out_dir = out_dir
        self.seqbatch_path = os.path.join(self.out_dir, "seqbatch.fa")
        os.makedirs(self.out_dir, exist_ok=True)

    def run_command(self, command):
        """Executa um comando no shell e lança uma exceção em caso de erro."""
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Erro ao executar o comando: {command}\n--- ERRO ---\n{result.stderr}\n------------")
        return result

    def wait_for_file(self, file_path, timeout=60):
        """Espera até que um arquivo exista ou o tempo limite seja atingido."""
        start_time = time.time()
        while not os.path.exists(file_path):
            if time.time() - start_time > timeout:
                raise FileNotFoundError(f"Timeout: O arquivo {file_path} não foi encontrado após {timeout} segundos.")
            time.sleep(1)

    def run_nextclade(self, dataset_name, output_csv):
        """Executa o comando Nextclade com os parâmetros fornecidos."""
        command = (f'nextclade run --dataset-name="{dataset_name}" '
                   f'--output-csv="{output_csv}" --min-match-length 20 '
                   f'"{self.seqbatch_path}"'
        )
        self.run_command(command)

    def execute_pipeline(self):
        """Método 'abstrato' a ser implementado pelas subclasses."""
        raise NotImplementedError("Subclasses devem implementar o método execute_pipeline.")


class DenvNextclade(BaseNextclade):
    """Implementação do pipeline Nextclade específico para Dengue."""

    def process_serotype(self):
        """Processa o arquivo de serótipo para encontrar o primeiro valor DENV válido."""
        serotype_csv_path = os.path.join(self.out_dir, "serotype.csv")
        self.wait_for_file(serotype_csv_path)
        serotype_df = pd.read_csv(serotype_csv_path, sep=';')
        
        if 'clade' not in serotype_df.columns:
            raise ValueError("A coluna 'clade' não foi encontrada no arquivo serotype.csv")

        for clade_value in serotype_df['clade']:
            if pd.notna(clade_value) and str(clade_value).strip():
                return str(clade_value).lower()

        raise ValueError("Nenhum valor válido de sorotipo (clade) encontrado no arquivo serotype.csv.")

    def execute_pipeline(self):
        """Executa o pipeline de duas etapas para Dengue: sorotipagem e genotipagem."""
        #Passo 1: Sorotipagem
        self.run_nextclade("nextstrain/dengue/all", os.path.join(self.out_dir, "serotype.csv"))

        #Passo 2: Processando resultado da sorotipagem
        denv_serotype = self.process_serotype()

        #Passo 3: Genotipagem"
        self.run_nextclade(f"community/v-gen-lab/dengue/{denv_serotype}", os.path.join(self.out_dir, "genotype.csv"))


class ChikvNextclade(BaseNextclade):
    """Implementação do pipeline Nextclade específico para Chikungunya."""

    def execute_pipeline(self):
        """Executa o pipeline de etapa única para Chikungunya."""
        #Executando genotipagem direta.")
        self.run_nextclade("community/v-gen-lab/chikV/genotypes", os.path.join(self.out_dir, "genotype.csv"))