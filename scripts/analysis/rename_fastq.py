#!/usr/bin/env python3

import pandas as pd
import csv
import os
import re

# =========================================================================
COLUNAS_MAPEADAS = {
    "Código_da_Amostra": [r"C.*digo[_ ]*(?:da[_ ])*Amostra", r"^ID$", r"^Amostra$"],
    "Requisição": [r"^Requisi.*o$", r"^Requisi.*o[_ ]*GAL$", r"^GAL$"],
    "Municipio_do_Solicitante": [r"Munic.*pio\s*(?:do\s*)?(?:Requisitante|Solicitante)", r"^Munic.*pio$"],
    "Estado_do_Solicitante": [r"Estado\s*(?:do\s*)?(?:Requisitante|Solicitante)", r"^Estado$", r"^UF$"],
    "CNES_Laboratório_responsável": [r"CNES\s*(?:do\s*)?Laborat.*rio\s*[Rr]espons.*vel", r"CNES[_ ]*Laboratorio[_ ]*Responsavel", r"^CNES$"],
    "Material_Biológico": [r"Material[_ ]*Biol.*gico", r"^Material$", r"^Tipo[_ ]*Amostra$"],
    "Data_da_Coleta": [r"Data[_ ]*(?:da[_ ])?Coleta"],
    "Data_de_Nascimento": [r"Data[_ ]*(?:de[_ ])?Nascimento"],
    "Sexo": [r"^Sexo$", r"^G.*nero$"],
    "Idade": [r"^Idade$"],
    "Tipo_Idade": [r"^Tipo[_ ]*Idade$"]
}

def padronizar_colunas(df, mapeamento):
    novo_nomes = {}
    padroes_encontrados = set() # NOVO: Rastreador de colunas já mapeadas
    
    for padrao_padronizado, regex_variacoes in mapeamento.items():
        for regex in regex_variacoes:
            # Se já achamos a coluna oficial para este padrão, não procura mais
            if padrao_padronizado in padroes_encontrados:
                break 
            
            for coluna in df.columns:
                if coluna in novo_nomes:
                    continue
                
                if re.search(regex, coluna, re.IGNORECASE):
                    novo_nomes[coluna] = padrao_padronizado
                    padroes_encontrados.add(padrao_padronizado)
                    break # Para de procurar nesta regex e vai para o próximo padrão oficial
    
    if novo_nomes:
        df.rename(columns=novo_nomes, inplace=True)

# =========================================================================

def rename_fastq_files(metadata_path, input_path):
    
    # 1. Carrega o metadado bruto e detecta delimitador ignorando quebras de encoding
    try:
        with open(metadata_path, 'r', encoding='utf-8', errors='ignore') as file:
            sample = file.read(1024)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
    except Exception:
        # Se a planilha for pequena ou manual, assume ponto e vírgula
        delimiter = ';'
        
    # 2. DUPLA TENTATIVA DE LEITURA (Anti-Corrupção de Acentos)
    try:
        # Tenta ler no padrão mundial (UTF-8)
        metadata = pd.read_csv(metadata_path, sep=delimiter, encoding='utf-8', on_bad_lines='skip')
    except UnicodeDecodeError:
        # Se falhar, tenta no padrão antigo do Windows (Latin-1)
        metadata = pd.read_csv(metadata_path, sep=delimiter, encoding='latin-1', on_bad_lines='skip')
    
    # 3. Padronização via Regex
    padronizar_colunas(metadata, COLUNAS_MAPEADAS)
    
    # 4. Substitui espaços restantes por underscores
    metadata.columns = metadata.columns.str.replace(' ', '_')
    
    # 5. INJEÇÃO DE SEGURANÇA: Se não tiver Requisição, copia o Código da Amostra
    if 'Requisição' not in metadata.columns:
        if 'Código_da_Amostra' in metadata.columns:
            metadata['Requisição'] = metadata['Código_da_Amostra']
    
    # 6. Validação
    required_cols = ['Código_da_Amostra', 'Requisição']
    if not set(required_cols).issubset(metadata.columns):
        raise ValueError(
            f"As colunas necessárias {required_cols} não foram encontradas no metadado após a padronização. "
            f"Colunas detectadas: {list(metadata.columns)}"
        )

    # 7. Cria o dicionário de correspondência (Requisição -> Código Amostra)
    metadata['Requisição'] = metadata['Requisição'].astype(str)
    metadata['Código_da_Amostra'] = metadata['Código_da_Amostra'].astype(str)
    
    requisicao_to_codigo = dict(zip(metadata['Requisição'], metadata['Código_da_Amostra']))

    # 8. Lógica de renomeação de arquivos
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