#!/usr/bin/env python3

import pandas as pd
import csv
import os
import sys
import plotly.express as px
from Bio import SeqIO
from unidecode import unidecode
import numpy as np
import re

# Acessa as funções gerais e EpiArbo
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.analysis.report.modules_general import load_config, mod_pasta, Quality_monitor, \
    Quality_monitor_interactive, remover_csv, input_folder, process_and_combine_data, validate_negative_control
from scripts.analysis.report.modules_EpiArbo import filter_depth, format_virus_name # Importa lógica de filtro/formato

# Define as colunas do dataframe a serem renomeadas (Contexto para outras funções)
RENAME_COLUMNS_OROV = {'cod': 'Código Amostra',
                       'mepf_reads_aligned': 'Reads',
                       'coverage_breadth': 'Coverage',
                       'mean_depth_coverage_x': 'Depth of Coverage',
                       'mean_depth_coverage': 'Depth of Coverage',
                       'Requisição': 'Requisição',
                       'Material_Biológico': 'Tipo Amostra',
                       'Municipio_do_Solicitante': 'Município',
                       'Data_da_Coleta': 'Data Coleta',
                       'Sexo': 'Sexo',
                       'lineage': 'Linhagem'} # Aqui 'lineage' é o nome da coluna de linhagem/genótipo


# Mapeamento de segmentos (Deve ser idêntico ao de AssemblerRun_OROV.py)
SEGMENTS = [
    {"segment": "L", "accession": "OL689334.1"},
    {"segment": "M", "accession": "OL689333.1"},
    {"segment": "S", "accession": "OL689332.1"},
]

# --- FUNÇÕES DE CARGA E AGREGAÇÃO (Núcleo da Compilação) ---

# Em report_generator_orov.py

def load_segment_consensus(base_out_dir, segments_list):
    """ 
    Carrega os arquivos de consenso (seqbatch.fa) de cada segmento, 
    criando a coluna com o nome final 'Código_da_Amostra'. 
    """
    all_sequences = []
    # Usamos o padrão de limpeza de IDconc
    id_cleaner = re.compile(r'(\|.*|_.*)')
    
    for info in segments_list:
        segment_name = info['segment']
        path = os.path.join(base_out_dir, f"OROV_{segment_name}", "COMPILED_OUTPUT", "seqbatch.fa")
        
        if os.path.exists(path):
            try:
                records = list(SeqIO.parse(path, "fasta"))
                for r in records:
                    cod_raw = id_cleaner.sub('', r.id.split("|")[0])
                    
                    # --- CORREÇÃO: Usamos o nome final da coluna aqui ---
                    all_sequences.append({
                        'Código_da_Amostra': cod_raw, # <-- O DataFrame é criado com a chave correta
                        'sequence': str(r.seq),
                        'segment': segment_name 
                    })
                    # -----------------------------------------------------
            except Exception as e:
                print(f"Aviso: Falha ao ler FASTA em {path}. Erro: {e}")
                continue

    sequences_df = pd.DataFrame(all_sequences)
    
    # Retorna o DataFrame, que agora tem a chave de merge correta
    if 'Código_da_Amostra' not in sequences_df.columns:
        return pd.DataFrame(columns=['Código_da_Amostra', 'sequence', 'segment']) 
        
    return sequences_df



def load_and_compile_segment_qc(base_out_dir, segments_list):
    """ Carrega e concatena short_summary.csv e reads_count.csv de todos os segmentos. """
    all_coverage_data = []
    all_reads_data = []
    
    for info in segments_list:
        segment_name = info['segment']
        segment_output_path = os.path.join(base_out_dir, f"OROV_{segment_name}", "COMPILED_OUTPUT")

        try:
            coverage_path = os.path.join(segment_output_path, 'short_summary.csv')
            coverage_df = pd.read_csv(coverage_path, sep=',')
            reads_path = os.path.join(segment_output_path, 'reads_count.csv')
            reads_df = pd.read_csv(reads_path, sep=',')

            if 'Unnamed: 0' in coverage_df.columns:
                coverage_df = coverage_df.drop('Unnamed: 0', axis=1)
            
            coverage_df['cod'] = coverage_df['cod'].replace(to_replace='_.*', value='', regex=True)
            if 'taxon' in coverage_df.columns:
                coverage_df = coverage_df[~coverage_df['taxon'].str.contains('_minor', na=False)] 
            reads_df['cod'] = reads_df['cod'].replace(to_replace='_.*', value='', regex=True)

            coverage_df['Segmento'] = segment_name
            reads_df['Segmento'] = segment_name
            
            all_coverage_data.append(coverage_df)
            all_reads_data.append(reads_df)

        except Exception as e:
            # Em caso de falha de leitura (ex: arquivo faltando), continua, mas reporta
            print(f"Erro ao processar dados do segmento OROV_{segment_name}: {e}")
            continue 

    if all_coverage_data and all_reads_data:
        compiled_coverage = pd.concat(all_coverage_data, ignore_index=True)
        compiled_reads = pd.concat(all_reads_data, ignore_index=True)
        return compiled_coverage, compiled_reads
    
    return pd.DataFrame(), pd.DataFrame()


# --- FUNÇÕES DE GERAÇÃO DE ARQUIVOS (ADAPTAÇÃO OROV) ---

def gerar_arquivo_fasta_orov(sequences_df, metadata, final_df, output_folder, cnes_codes='cnes_lacen.csv'):
    """
    Gera o arquivo FASTA compilado (multi-segmento) para submissão, com header no padrão PIPE (|).
    
    A função retorna o DataFrame combinado (df_combine_sequence) para uso no EpiArbo/Planilha.
    """
    print("Gerando arquivo fasta OROV compilado em memória...")

    # --- LÓGICA DE PREPARAÇÃO DE METADADOS (Copied from DENV/CHIKV flow) ---
    
    # Dictionary to change the Name of the state to SIGLA
    states = {
        'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA', 'Ceará': 'CE',
        'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO', 'Maranhão': 'MA', 'Mato Grosso': 'MT', 
        'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG', 'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR',
        'Pernambuco': 'PE', 'Piauí': 'PI', 'Rio de Janeiro': 'RJ', 'Rio Grande do Norte': 'RN', 'Rio Grande do Sul': 'RS',
        'Rondônia': 'RO', 'Roraima': 'RR', 'Santa Catarina': 'SC', 'São Paulo': 'SP', 'Sergipe': 'SE', 'Tocantins': 'TO'
    }
    metadata['Estado_do_Solicitante'] = metadata['Estado_do_Solicitante'].replace(states)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cnes_path = os.path.join(script_dir, cnes_codes)

    cnes_codes_df = pd.read_csv(cnes_path, dtype={'CNES': str, 'SIGLA': str})
    metadata['CNES_Laboratório_responsável'] = metadata['CNES_Laboratório_responsável'].astype(str)
    cnes_codes_df['CNES'] = cnes_codes_df['CNES'].astype(str)

    # Merge para obter a SIGLA do Laboratório (CNES -> SIGLA)
    metadata = metadata.merge(cnes_codes_df, how='left', left_on='CNES_Laboratório_responsável', right_on='CNES')
    metadata['CNES_Laboratório_responsável'] = metadata['SIGLA'].fillna('NA_LAB') # Trata NaNs da SIGLA
    metadata.drop(columns=['CNES', 'SIGLA'], inplace=True)

    sequences_df = sequences_df.rename(columns={'id': 'Código_da_Amostra'})
    sequences_df['Código_da_Amostra'] = sequences_df['Código_da_Amostra'].astype(str)

    # Filtro de cobertura
    #final_df = final_df.loc[final_df['Coverage'].astype(float) >= 60]
    final_df = final_df.astype(str)
    
    metadata['Código_da_Amostra'] = metadata['Código_da_Amostra'].astype(str)
    final_df['Código_da_Amostra'] = final_df['Código_da_Amostra'].astype(str)
    
    
# 2. Merge de Sequences com Metadados
    df_combine_sequence = pd.merge(sequences_df, metadata, left_on="Código_da_Amostra", right_on="Código_da_Amostra", suffixes=('', '_dup'))

    # Merge 2: Junta com o filtro de elegibilidade (final_df)
    df_combine_sequence = pd.merge(df_combine_sequence, final_df, on="Código_da_Amostra", suffixes=('', '_dup'))

    # Processamento Final das Colunas de Data/Ano
    df_combine_sequence['Data_da_Coleta'] = pd.to_datetime(df_combine_sequence['Data_da_Coleta'], dayfirst=True, errors='coerce')
    df_combine_sequence['ANO_SEMANA_EPIDEMIOLOGICA'] = df_combine_sequence['Data_da_Coleta'].dt.strftime('%Y').fillna('ND')

    df_combine_sequence['ANO_SEMANA_EPIDEMIOLOGICA'] = df_combine_sequence['Data_da_Coleta'].dt.strftime('%Y').fillna('ND')
    
    # 3. Escrita do FASTA no padrão OROV (com PIPE e Segmento)
    fasta_output_dir = os.path.join(output_folder, 'RNSG_REPORT')
    fasta_output_path = os.path.join(fasta_output_dir, 'LACEN_seq_OROV.fasta')
    
    with open(fasta_output_path, 'w') as outfile:
        
        for index, row in df_combine_sequence.iterrows():

            #try:
                # Condição de escrita simplificada (sem filtro de elegibilidade)
                #is_eligible = True # Não verificamos Coverage >= 60% aqui
                
                #if is_eligible: 
                    print(f"DEBUG {index}: Tentando Amostra {row['Código_da_Amostra']} / Segmento {row['segment']}")

                    seq = row['sequence']
                    
                    # --- NOVO BLOCO DE DEBUG CRÍTICO ---
                    codigo_amostra = str(row['Código_da_Amostra'])
                    if not seq or seq.strip() == "":
                        print(f"DEBUG VAZIO: Amostra {codigo_amostra} | Segmento {row['segment']} | Sequência é VAZIA.")
                        continue # Pula a escrita
                    
                    # Verifica se a sequência é apenas 'N's (o que indicaria falha na montagem)
                    elif len(seq) > 10 and seq.upper().count('N') / len(seq) > 0.9: 
                        print(f"DEBUG AVISO: Amostra {codigo_amostra} | Segmento {row['segment']} | Sequência é quase só 'N's ({len(seq)}pb).")
                        # Opcional: Você pode optar por pular aqui tbm se 90% for N.
                        
                    # ------------------------------------

                    # --- Lógica de escrita (Executada se a sequência não for vazia) ---
                    estado = str(row['Estado_do_Solicitante'])
                    cnes = str(row['CNES_Laboratório_responsável'])
                    ano = str(row['ANO_SEMANA_EPIDEMIOLOGICA'])

                    base_header = f"hOROV/Brazil/{estado}-LACEN{cnes}-{codigo_amostra}/{ano}"
                    seq_id = f">{base_header}|{row['segment']}"
                    
                    seq_id = format_virus_name(seq_id) 
                    
                    outfile.write(f"{seq_id}\n{seq}\n")
                    
            #except Exception as e:
             #   print(f"ERRO DE ESCRITA: Falha ao processar a amostra no índice {index}. Motivo: {type(e).__name__} - {e}.")
              #  continue 

    print(f"\nArquivo FASTA OROV compilado gerado com sucesso em: {fasta_output_path}")
    return df_combine_sequence

# ... (Funções planilha_resultado_orov e arquivo_epiarbo_orov - devem ser implementadas com lógica de agrupamento) ...


# --- FUNÇÃO ORQUESTRADORA (Principal) ---
def generate_compiled_report_orov(metadata_path, base_out_dir, config_path):
    print("Iniciando compilação de dados OROV (L, M, S)...")
    
    COMPILED_DIR = os.path.join(base_out_dir, "OROV_COMPILED_OUT")
    mod_pasta(COMPILED_DIR)
    
    LAST_SEGMENT_DIR = os.path.join(base_out_dir, f"OROV_{SEGMENTS[-1]['segment']}", "COMPILED_OUTPUT")
    
    # 1. Carga de QC
    compiled_coverage, compiled_reads = load_and_compile_segment_qc(base_out_dir, SEGMENTS)
    
    if compiled_coverage.empty:
        raise ValueError("Nenhum dado de cobertura válido encontrado.")

    # 2. Carga de Metadados e Sequências
    try:
        metadata, _, records, _, _, errors = input_folder(LAST_SEGMENT_DIR, metadata_path)
        print(f"DEBUG: Metadados carregados. Linhas: {len(metadata)}")
    except Exception as e:
        raise RuntimeError(f"Falha na carga de dados essenciais: {e}") 

    sequences_df = load_segment_consensus(base_out_dir, SEGMENTS)
    print(f"DEBUG: Sequências carregadas. Linhas: {len(sequences_df)}")
    
    if sequences_df.empty:
        print("CRÍTICO: sequences_df está vazio! O arquivo FASTA não será gerado.")

    # 3. Validação CN
    cn_message, compiled_positive_coverage = validate_negative_control(compiled_coverage, errors)

    # 4. Preparação para FASTA (O erro pode estar aqui)
    try:
        print("DEBUG: Preparando filtro de cobertura...")
        temp_coverage_filter = compiled_coverage.groupby('cod')['coverage_breadth'].max().reset_index(name='Coverage')
        temp_coverage_filter['Coverage'] = temp_coverage_filter['Coverage'].multiply(100).round(2)
        temp_coverage_filter.rename(columns={'cod': 'Código_da_Amostra'}, inplace=True) 
        print(f"DEBUG: Filtro de cobertura pronto. Linhas: {len(temp_coverage_filter)}")
    except Exception as e:
        print(f"ERRO FATAL ao preparar filtro de cobertura: {e}")
        return None, None

    # --- CHAMADA DA FUNÇÃO (AQUI É ONDE ESTAVA O MISTÉRIO) ---
    print("DEBUG: Chamando gerar_arquivo_fasta_orov agora...")
    try:
        df_combine_sequence = gerar_arquivo_fasta_orov(sequences_df, metadata, temp_coverage_filter, COMPILED_DIR)
        print(f"DEBUG: Retornou de gerar_arquivo_fasta_orov. Linhas combinadas: {len(df_combine_sequence)}")
    except Exception as e:
        print(f"ERRO FATAL DENTRO de gerar_arquivo_fasta_orov: {e}")
        # Importante: imprimir o traceback completo se possível, ou pelo menos o erro
        import traceback
        traceback.print_exc()
    # ---------------------------------------------------------

    # 5. Geração dos relatórios finais
    # (Placeholder para planilha/epiarbo)
    
    # 6. QC HTML
    # ... (Código do Plotly omitido para brevidade, mantenha o que você já tem) ...
    # Apenas para garantir que o script não quebre aqui se o anterior falhar:
    if not compiled_coverage.empty:
        # ... (Lógica do Plotly) ...
        pass # Substitua pelo seu código Plotly real
    
    return compiled_coverage, compiled_reads