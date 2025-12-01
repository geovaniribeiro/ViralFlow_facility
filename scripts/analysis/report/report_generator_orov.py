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
    fasta_output_dir = os.path.join(output_folder)
    fasta_output_path = os.path.join(fasta_output_dir, 'LACEN_seq_OROV.fasta')
    
    with open(fasta_output_path, 'w') as outfile:
        
        for index, row in df_combine_sequence.iterrows():

            #try:
                # Condição de escrita simplificada (sem filtro de elegibilidade)
                #is_eligible = True # Não verificamos Coverage >= 60% aqui
                
                #if is_eligible: 

                    seq = row['sequence']
                    
                    # --- NOVO BLOCO DE DEBUG CRÍTICO ---
                    codigo_amostra = str(row['Código_da_Amostra'])
                    if not seq or seq.strip() == "":
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

# Em report_generator_orov.py

def arquivo_epiarbo_orov(config, metadata, df_combine_sequence, output_folder):
    """ Gera o arquivo EpiArbo para OROV com desduplicação de amostras. """
    print("Gerando arquivo EpiArbo OROV...")

    # 1. Carrega Info Usuário
    submitter = config['user_info']['submitter']
    arbo_authors = config['user_info']['authors']
    arbo_orig_lab = config['user_info']['subm_lab']
    arbo_orig_lab_addr = config['user_info']['subm_lab_addr']
    arbo_subm_lab = config['user_info']['subm_lab']
    arbo_subm_lab_addr = config['user_info']['subm_lab_addr']

    # 2. Desduplicação (1 linha por amostra)
    # Agrupa e pega o primeiro registro (pois dados demográficos são iguais para os 3 segmentos)
    df_unique = df_combine_sequence.groupby('Código_da_Amostra').first().reset_index()

    df_unique = df_unique.loc[:, ~df_unique.columns.duplicated()]

    df_unique = df_unique.rename(columns={'Código_da_Amostra': 'id'})

    # 3. Preparação Demográfica
    arbo_patient_age = df_unique[['id', 'Data_de_Nascimento', 'Data_da_Coleta']].copy()
    arbo_patient_age['Data_de_Nascimento'] = arbo_patient_age['Data_de_Nascimento'].astype(str).replace(to_replace=' .*', value='', regex=True)
    arbo_patient_age['Data_da_Coleta'] = pd.to_datetime(arbo_patient_age['Data_da_Coleta'], errors='coerce')
    arbo_patient_age['Data_de_Nascimento'] = pd.to_datetime(arbo_patient_age['Data_de_Nascimento'], errors='coerce', dayfirst=True)
    
    # Cálculo de Idade
    arbo_patient_age['arbo_patient_age'] = ((arbo_patient_age['Data_da_Coleta'] - arbo_patient_age['Data_de_Nascimento']).dt.days / 365.25).round().astype('Int64')
    arbo_patient_age = arbo_patient_age[['id', 'arbo_patient_age']]

    # 4. Construção do Nome do Vírus
    arbo_virus_name = df_unique[['Estado_do_Solicitante', 'CNES_Laboratório_responsável', 'id', 'ANO_SEMANA_EPIDEMIOLOGICA']].astype(str)
    
    # Nome do vírus base
    arbo_virus_name['arbo_virus_name'] = "hOROV/Brazil/" + \
        arbo_virus_name['Estado_do_Solicitante'] + "-LACEN" + \
        arbo_virus_name['CNES_Laboratório_responsável'] + "-" + \
        arbo_virus_name['id'] + "/" + arbo_virus_name['ANO_SEMANA_EPIDEMIOLOGICA']
    
    arbo_virus_name['arbo_virus_name'] = arbo_virus_name['arbo_virus_name'].apply(format_virus_name)
    arbo_virus_name = arbo_virus_name[['id', 'arbo_virus_name']]

    # Inserção de Colunas Fixas
    arbo_virus_name.insert(0, 'submitter', submitter)
    arbo_virus_name.insert(1, 'fn', 'LACEN_seq_OROV.fasta')
    arbo_virus_name.insert(3, 'arbo_type', 'Oropouche virus')
    arbo_virus_name.insert(4, 'arbo_host', 'Human')
    arbo_virus_name.insert(5, 'arbo_passage', 'Original')

    # 5. Merges Finais
    arbo_collection_date = df_unique[['id', 'Data_da_Coleta']].copy()
    arbo_collection_date['Data_da_Coleta'] = pd.to_datetime(arbo_collection_date['Data_da_Coleta']).dt.strftime('%Y-%m-%d')
    arbo_collection_date.rename(columns={'Data_da_Coleta': 'arbo_collection_date'}, inplace=True)
    gisaid_temp = pd.merge(arbo_virus_name, arbo_collection_date, on='id')

    # Location (Estados)
    states = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia', 'CE': 'Ceará',
        'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso',
        'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
        'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
        'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
    }
    
    # Preparação de Location
    arbo_location = df_unique[['id', 'Estado_do_Solicitante', 'Municipio_do_Solicitante']].copy()
    arbo_location['Estado_do_Solicitante'] = arbo_location['Estado_do_Solicitante'].replace(states)
    
    # --- CORREÇÃO AQUI (Uso de .str.capitalize() em vez de .apply(str.capitalize)) ---
    arbo_location['Municipio_do_Solicitante'] = arbo_location['Municipio_do_Solicitante'].astype(str).str.capitalize().apply(unidecode)
    arbo_location['Estado_do_Solicitante'] = arbo_location['Estado_do_Solicitante'].astype(str).str.capitalize().apply(unidecode)
    # ---------------------------------------------------------------------------------
    
    arbo_location['arbo_location'] = "South America / Brazil / " + arbo_location['Estado_do_Solicitante'] + " / " + arbo_location['Municipio_do_Solicitante']
    gisaid_temp = pd.merge(gisaid_temp, arbo_location[['id', 'arbo_location']], on='id')

    # Insere colunas vazias padrão
    gisaid_temp.insert(8, 'arbo_add_location', '')

    gisaid_temp.insert(10, 'arbo_add_host_info', '')
    gisaid_temp.insert(11, 'arbo_sampling_strategy', '')

    # Gender
    gender_map = {
        'MASCULINO': 'Male', 'FEMININO': 'Female', 'M': 'Male', 'F': 'Female',
        'Masculino': 'Male', 'Feminino': 'Female'
    }
    arbo_gender = df_unique[['id', 'Sexo']].copy()
    arbo_gender['Sexo'] = arbo_gender['Sexo'].replace(gender_map)
    gisaid_temp = pd.merge(gisaid_temp, arbo_gender.rename(columns={'Sexo': 'arbo_gender'}), on='id')

    # Merge Age
    gisaid_temp = pd.merge(gisaid_temp, arbo_patient_age, on='id')
    
    # Status
    gisaid_temp['arbo_patient_status'] = 'Unknown'
    gisaid_temp['arbo_clinical_symptoms'] = ''

    # Specimen
    bio_material_translation = {
        "Soro": "Serum", "Sangue": "Blood", "Urina": "Urine", "Liquor": "Cerebrospinal fluid (CSF)",
        "Plasma": "Plasma", "Swab": "Swab"
    }
    arbo_specimen = df_unique[['id', 'Material_Biológico']].copy()
    arbo_specimen['arbo_specimen'] = arbo_specimen['Material_Biológico'].map(bio_material_translation).fillna('Unknown')
    gisaid_temp = pd.merge(gisaid_temp, arbo_specimen[['id', 'arbo_specimen']], on='id')

    # Outras colunas fixas
    gisaid_temp['arbo_outbreak'] = ''
    gisaid_temp['arbo_last_vaccination_date'] = ''
    gisaid_temp['arbo_treatment'] = ''
    gisaid_temp['arbo_seq_technology'] = 'Illumina MiSeq'
    gisaid_temp['arbo_assembly_method'] = 'Viralflow'

    # Coverage
    arbo_coverage = df_unique[['id', 'Depth of Coverage']].copy()
    gisaid_temp = pd.merge(gisaid_temp, arbo_coverage.rename(columns={'Depth of Coverage': 'arbo_coverage'}), on='id')

    # Labs
    gisaid_temp['arbo_publications'] = ''
    gisaid_temp['arbo_orig_lab'] = arbo_orig_lab
    gisaid_temp['arbo_orig_lab_addr'] = arbo_orig_lab_addr
    gisaid_temp['arbo_provider_sample_id'] = ''
    gisaid_temp['arbo_subm_lab'] = arbo_subm_lab
    gisaid_temp['arbo_subm_lab_addr'] = arbo_subm_lab_addr
    gisaid_temp['arbo_subm_sample_id'] = ''
    gisaid_temp['arbo_authors'] = arbo_authors

    gisaid_temp = gisaid_temp.drop('id', axis=1)

    # Ordenação Final
    final_cols = ['submitter', 'fn', 'arbo_virus_name', 'arbo_type', 'arbo_passage', 'arbo_collection_date',
            'arbo_location', 'arbo_add_location', 'arbo_host', 'arbo_add_host_info', 'arbo_sampling_strategy',
            'arbo_gender', 'arbo_patient_age', 'arbo_patient_status',  'arbo_clinical_symptoms',
            'arbo_specimen', 'arbo_outbreak', 'arbo_last_vaccination_date', 'arbo_treatment',
            'arbo_seq_technology', 'arbo_assembly_method', 'arbo_coverage', 'arbo_publications', 'arbo_orig_lab', 'arbo_orig_lab_addr',
            'arbo_provider_sample_id', 'arbo_subm_lab', 'arbo_subm_lab_addr',
            'arbo_subm_sample_id', 'arbo_authors']
    
    # Header descritivo EpiArbo
    columns_desc = ['Submitter', 'FASTA filename', 'Virus name', 'Type', 'Passage details/history', 'Collection date',
            'Location', 'Additional location information', 'Host', 'Additional host information', 'Sampling Strategy',
            'Gender', 'Patient age', 'Patient status',  'Specific clinical symptoms',
            'Specimen source', 'Outbreak', 'Vaccination History', 'Treatment',
            'Sequencing technology', 'Assembly method', 'Depth of coverage', 'Publications', 'Originating lab', 'Address',
            'Sample ID given by the sample provider', 'Submitting lab', 'Address',
            'Sample ID given by the submitting laboratory', 'Authors']

    # Garante a ordem e cria o DF final
    gisaid_temp = gisaid_temp[final_cols]
    
    header_df = pd.DataFrame([columns_desc], columns=final_cols)
    final_epiarbo = pd.concat([header_df, gisaid_temp], ignore_index=True)
    
    # Salvar
    output_path = os.path.join(output_folder, 'EpiArbo.csv')
    final_epiarbo.to_csv(output_path, index=False)
    print(f"Arquivo EpiArbo OROV gerado com sucesso em: {output_path}")

# --- FUNÇÃO ORQUESTRADORA (Principal) ---
def generate_compiled_report_orov(metadata_path, base_out_dir, config_path):
    print("Iniciando compilação de dados OROV (L, M, S)...")
    
    COMPILED_DIR = os.path.join(base_out_dir, "OROV_COMPILED_OUT")
    #mod_pasta(COMPILED_DIR)
    
    LAST_SEGMENT_DIR = os.path.join(base_out_dir, f"OROV_{SEGMENTS[-1]['segment']}", "COMPILED_OUTPUT")
    
    try:
        # Carrega Config
        config = load_config(config_path)
        
        # 1. Carga e Agregação de QC
        compiled_coverage, compiled_reads = load_and_compile_segment_qc(base_out_dir, SEGMENTS)
        
        if compiled_coverage.empty:
            raise ValueError("Nenhum dado de cobertura válido encontrado para a compilação OROV.")

        # 2. Carregar Metadados e Errors
        metadata, _, records, _, _, errors = input_folder(LAST_SEGMENT_DIR, metadata_path)
    
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        # Retorna DFs vazios ou levanta erro
        raise RuntimeError(f"Falha crítica no pipeline OROV: {e}")

    # 3. Validação do CN
    cn_message, compiled_positive_coverage = validate_negative_control(compiled_coverage, errors)

    # 4. Geração do FASTA (e DataFrame Mestre)
    sequences_df = load_segment_consensus(base_out_dir, SEGMENTS)
    
    temp_coverage_filter = compiled_coverage.groupby('cod').agg({
        'coverage_breadth': 'max',       # Pega a melhor cobertura entre os segmentos
        'mean_depth_coverage': 'mean'    # Pega a profundidade média dos segmentos
    }).reset_index()

    # Ajusta os valores
    temp_coverage_filter['coverage_breadth'] = temp_coverage_filter['coverage_breadth'].multiply(100).round(2)
    temp_coverage_filter['mean_depth_coverage'] = temp_coverage_filter['mean_depth_coverage'].round(2)

    # Renomeia para os nomes esperados pelas funções de relatório (EpiArbo/Fasta)
    temp_coverage_filter.rename(columns={
        'cod': 'Código_da_Amostra',
        'coverage_breadth': 'Coverage',
        'mean_depth_coverage': 'Depth of Coverage'
    }, inplace=True)

    # Gera FASTA e obtém o DF combinado
    df_combine_sequence = gerar_arquivo_fasta_orov(sequences_df, metadata, temp_coverage_filter, COMPILED_DIR)

    # 5. Geração dos relatórios finais (EpiArbo)
    try:
        arquivo_epiarbo_orov(config, metadata, df_combine_sequence, COMPILED_DIR)
        # planilha_resultado_orov(...) # Chame se implementado
    except Exception as e:
        print(f"Erro ao gerar EpiArbo: {e}")
        import traceback
        traceback.print_exc()

    # 6. Geração do Relatório de QC HTML (Plotly)
    # 6. Geração do Relatório de QC HTML (Plotly) - Versão OROV Compilada
    try:
        # Passamos os DataFrames compilados. A função detectará a coluna 'Segmento' 
        # e gerará os gráficos comparativos automaticamente.
        Quality_monitor_interactive(
            coverage=compiled_coverage,
            reads=compiled_reads,
            errors=errors,
            output_folder=COMPILED_DIR,
            eligibility_threshold=60,
            report_title="Relatório de Qualidade Compilado OROV (L, M, S)"
        )
        print(f"Relatório QC Compilado gerado em: {COMPILED_DIR}/RNSG_REPORT/Quality_check.html")
        
    except Exception as e:
        print(f"Erro ao gerar QC Plotly Compilado: {e}")
        import traceback
        traceback.print_exc()
    
    return compiled_coverage, compiled_reads