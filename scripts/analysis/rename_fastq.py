#!/usr/bin/env python3

import pandas as pd
import csv
import os
import re # Necessário para o padronizar_colunas
from unidecode import unidecode # Necessário para a limpeza de acentos

# =========================================================================
COLUNAS_MAPEADAS = {
    "Código_da_Amostra": [r"C[oó]digo[_ ]*Amostra", r"C[oó]digo[_ ]*(?:da[_ ])*Amostra", r"C[oó]digo\s*(?:da\s*)?Amostra"],
    "Requisição": [r"^(Requisiç[ãa]o)$", r"^(Requisicao)$", r"^(Requisiç[ãa]o[_ ]*GAL)$", r"^(Requisicao[_ ]*GAL)$"],
    "Municipio_do_Solicitante": [r"Munic[ií]pio\s*(?:do\s*)?(?:Requisitante|Solicitante)"],
    "Estado_do_Solicitante": [r"Estado\s*(?:do\s*)?(?:Requisitante|Solicitante)"],
    "CNES_Laboratório_responsável": [r"CNES\s*(?:do\s*)?Laboratório\s*[Rr]espons[aá]vel" , r"CNES[_ ]*Laboratorio[_ ]*Responsavel"]
}

def padronizar_colunas(df, mapeamento):
    """ Função que padroniza os nomes das colunas (copiada do modules_general.py) """
    novo_nomes = {}
    for padrao_padronizado, regex_variacoes in mapeamento.items():
        for regex in regex_variacoes:
            for coluna in df.columns:
                if pd.Series(coluna).str.contains(regex, regex=True, case=False).any():
                    novo_nomes[coluna] = padrao_padronizado
    df.rename(columns=novo_nomes, inplace=True)

# =========================================================================


def rename_fastq_files(metadata_path, input_path):
    
    # 1. Carrega o metadado bruto e detecta delimitador
    with open(metadata_path, 'r', encoding='latin-1') as file:
        sample = file.read(1024)
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter

    metadata = pd.read_csv(metadata_path, sep=delimiter, encoding='latin-1', on_bad_lines='skip')
    
    # --- CORREÇÃO PRINCIPAL: PADRONIZAÇÃO IMEDIATA ---
    # 2. Limpa acentos/caracteres corrompidos (ex: RequisiÃ§Ã£o -> Requisicao)
    metadata.columns = metadata.columns.map(unidecode)
    
    # 3. Substitui espaços por underscores (requerido para o padrão)
    metadata.columns = metadata.columns.str.replace(' ', '_')
    
    # 4. Aplica o mapeamento REGEX (agora as colunas estão limpas para o Regex funcionar)
    padronizar_colunas(metadata, COLUNAS_MAPEADAS)
    # ----------------------------------------------------

    # 5. O restante do código usa os nomes limpos (Requisição e Código_da_Amostra)
    
    # Garantir que as colunas existam após a padronização (Verificação robusta)
    required_cols = ['Código_da_Amostra', 'Requisição']
    if not set(required_cols).issubset(metadata.columns):
        raise ValueError(
            f"As colunas necessárias {required_cols} não foram encontradas no metadado após a padronização. "
        )

    # Cria o dicionário de correspondência (Requisição -> Código Amostra)
    metadata['Requisição'] = metadata['Requisição'].astype(str)
    metadata['Código_da_Amostra'] = metadata['Código_da_Amostra'].astype(str)
    
    requisicao_to_codigo = dict(zip(metadata['Requisição'], metadata['Código_da_Amostra']))

    # Lógica de renomeação de arquivos
    renamed_count = 0
    for filename in os.listdir(input_path):
        if "fastq" in filename or "fq" in filename:
            file_path = os.path.join(input_path, filename)
            
            # Extrai o nome base (que deve ser a Requisição original)
            # O nome do arquivo FASTQ começa com a Requisição.
            sample_name = filename.split("_")[0] 

            # Ignorar se o nome base já for o código da amostra final
            if sample_name in metadata['Código_da_Amostra'].values:
                continue

            # Se o nome (Requisição) estiver no dicionário, renomear
            if sample_name in requisicao_to_codigo:
                new_code = requisicao_to_codigo[sample_name]
                # Preserva o resto do nome do arquivo (ex: _S1_L001_R1_001.fastq.gz)
                new_name = new_code + filename[filename.index("_"):]
                new_path = os.path.join(input_path, new_name)
                
                os.rename(file_path, new_path)
                renamed_count += 1

    if renamed_count > 0:
         print(f"Renomeação de arquivos FASTQ concluída ({renamed_count} arquivos renomeados).")
    else:
         print("Renomeação de arquivos FASTQ pulada (arquivos já renomeados ou sem correspondência).")