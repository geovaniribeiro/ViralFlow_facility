import os
import pandas as pd
import csv

# Função para padronizar os nomes das colunas usando regex
def rename_fastq_files(metadata_path, input_path):

    colunas_mapeadas = {
        "Código_da_Amostra": [
            r"C[oó]digo_?(?:da_?)?Amostra",  # cobre 'Código_Amostra', 'Código_da_Amostra'
            r"C[oó]digoAmostra"             # só por segurança, se vier tudo junto
        ]
    }

    def padronizar_colunas(df, mapeamento):
        novo_nomes = {}
        for padrao_padronizado, regex_variacoes in mapeamento.items():
            for regex in regex_variacoes:
                for coluna in df.columns:
                    if pd.Series(coluna).str.contains(regex, regex=True, case=False).any():
                        novo_nomes[coluna] = padrao_padronizado
        df.rename(columns=novo_nomes, inplace=True)
        

    """ Renomeia arquivos FASTQ com base no arquivo de metadados """
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Arquivo de metadados não encontrado: {metadata_path}")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Diretório FASTQ não encontrado: {input_path}")

    # Detecta o delimitador do arquivo
    with open(metadata_path, 'r', encoding='latin-1') as file:
        sample = file.read(1024)  # Lê uma amostra do arquivo
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter  # Detecta o delimitador

    # Carrega o arquivo usando o delimitador detectado
    metadata = pd.read_csv(metadata_path, sep=delimiter, encoding='latin-1', on_bad_lines='skip')
    
    # Substitui espaços por '_' nos nomes das colunas
    metadata.columns = metadata.columns.str.replace(' ', '_')

    # Padroniza os nomes das colunas
    padronizar_colunas(metadata, colunas_mapeadas)

    # Converter as colunas para string
    metadata['Requisição'] = metadata['Requisição'].astype(str)
    metadata['Código_da_Amostra'] = metadata['Código_da_Amostra'].astype(str)

    # Garantir que as colunas necessárias existam
    if not {'Código_da_Amostra', 'Requisição'}.issubset(metadata.columns):
        raise ValueError("O arquivo de metadados deve conter as colunas 'Código_da_Amostra' e 'Requisição'")

    # Criar um dicionário de correspondência Requisição -> Código_da_Amostra
    requisicao_to_codigo = dict(zip(metadata['Requisição'], metadata['Código_da_Amostra']))

    # Percorrer os arquivos no diretório FASTQ
    for filename in os.listdir(input_path):
        if "fastq" in filename or "fq" in filename:  # Considerando extensões comuns
            file_path = os.path.join(input_path, filename)
            sample_name = filename.split("_")[0]  # Extrair o nome base do arquivo

            # Se o nome já está na coluna 'Código_da_Amostra', não fazer nada
            if sample_name in metadata['Código_da_Amostra'].values:
                continue

            # Se o nome estiver na coluna 'Requisição', renomear
            if sample_name in requisicao_to_codigo:
                new_name = requisicao_to_codigo[sample_name] + filename[filename.index("_"):]
                new_path = os.path.join(input_path, new_name)
                os.rename(file_path, new_path)
                print(f"Renomeado: {filename} -> {new_name}")