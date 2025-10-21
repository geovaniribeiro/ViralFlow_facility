#!/usr/bin/env python3

import os
import time
import pandas as pd
import subprocess

class ChikvNextclade:
    def __init__(self, out_dir):
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)

    def run_command(self, command):
        """Executa um comando e lança uma exceção em caso de erro."""
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Erro ao executar o comando: {command}\n{result.stderr}")

    def wait_for_file(self, file_path, timeout=60):
        """Espera até que o arquivo especificado seja criado ou atinja o tempo limite."""
        start_time = time.time()
        while not os.path.exists(file_path):
            if time.time() - start_time > timeout:
                raise FileNotFoundError(f"Timeout: O arquivo {file_path} não foi encontrado após {timeout} segundos.")
            time.sleep(1)

    def run_nextclade(self, dataset_name, output_csv, seqbatch_path):
        """Executa o comando Docker para o Nextclade."""
        command = (f'nextclade run --dataset-name="{dataset_name}" '
                   f'--output-csv="{output_csv}" --min-match-length 20 '
                   f'"{seqbatch_path}"'
        )
        self.run_command(command)

    def execute_pipeline(self):
        """Executa o pipeline completo para processar os dados."""
        # Passo 1: Executar Nextclade inicial
        seqbatch_path = os.path.join(self.out_dir, "seqbatch.fa")

        # Passo 2: Executar Nextclade para genotipagem
        genotype_dataset = f"community/v-gen-lab/chikV/genotypes"
        genotype_output_csv = os.path.join(self.out_dir, "genotype.csv")

        self.run_nextclade(genotype_dataset, genotype_output_csv, seqbatch_path)
