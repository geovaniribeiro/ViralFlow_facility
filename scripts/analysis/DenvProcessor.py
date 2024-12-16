import os
import time
import pandas as pd
import subprocess

class DenvProcessor:
    def __init__(self, out_dir):
        self.out_dir = out_dir
        self.compiled_output_dir = os.path.join(out_dir, "COMPILED_OUTPUT")
        os.makedirs(self.compiled_output_dir, exist_ok=True)

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
                   f'--output-csv="{output_csv}" '
                   f'"{seqbatch_path}"'
        )
        self.run_command(command)

    def process_serotype(self):
        """Processa o arquivo de serótipo e retorna o valor de DENV."""
        serotype_csv_path = os.path.join(self.compiled_output_dir, "serotype.csv")
        self.wait_for_file(serotype_csv_path)
        serotype_df = pd.read_csv(serotype_csv_path, sep = ';')
        serotype_df['clade'] = serotype_df['clade'].str.lower()
        return serotype_df.iloc[0, 2]  # Acessando a coluna 3 (index 2) da primeira linha

    def execute_pipeline(self):
        """Executa o pipeline completo para processar os dados."""
        # Passo 1: Executar Nextclade inicial
        initial_dataset = "nextstrain/dengue/all"
        initial_output_csv = os.path.join(self.compiled_output_dir, "serotype.csv")
        seqbatch_path = os.path.join(self.compiled_output_dir, "seqbatch.fa")

        self.run_nextclade(initial_dataset, initial_output_csv, seqbatch_path)

        # Passo 2: Obter o valor de serótipo
        DENV_value = self.process_serotype()

        # Passo 3: Executar Nextclade para genotipagem
        genotype_dataset = f"community/v-gen-lab/dengue/{DENV_value}"
        genotype_output_csv = os.path.join(self.compiled_output_dir, "genotype.csv")

        self.run_nextclade(genotype_dataset, genotype_output_csv, seqbatch_path)
