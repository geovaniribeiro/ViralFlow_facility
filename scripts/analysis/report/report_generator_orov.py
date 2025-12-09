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
from scripts.analysis.report.modules_EpiArbo import filter_depth, format_virus_name

# Mapeamento de segmentos
SEGMENTS = [
    {"segment": "L", "accession": "OL689334.1"},
    {"segment": "M", "accession": "OL689333.1"},
    {"segment": "S", "accession": "OL689332.1"},
]

# --- FUNÇÕES DE CARGA E AGREGAÇÃO ---

def load_segment_consensus(base_out_dir, segments_list):
    """ 
    Carrega os arquivos de consenso (seqbatch.fa) de cada segmento.
    """
    all_sequences = []
    id_cleaner = re.compile(r'(\|.*|_.*)')
    
    for info in segments_list:
        segment_name = info['segment']
        path = os.path.join(base_out_dir, f"OROV_{segment_name}", "COMPILED_OUTPUT", "seqbatch.fa")
        
        if os.path.exists(path):
            try:
                records = list(SeqIO.parse(path, "fasta"))
                for r in records:
                    cod_raw = id_cleaner.sub('', r.id.split("|")[0])
                    all_sequences.append({
                        'Código_da_Amostra': cod_raw,
                        'sequence': str(r.seq),
                        'segment': segment_name 
                    })
            except Exception as e:
                print(f"Aviso: Falha ao ler FASTA em {path}. Erro: {e}")
                continue

    sequences_df = pd.DataFrame(all_sequences)
    
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
            print(f"Erro ao processar dados do segmento OROV_{segment_name}: {e}")
            continue 

    if all_coverage_data and all_reads_data:
        compiled_coverage = pd.concat(all_coverage_data, ignore_index=True)
        compiled_reads = pd.concat(all_reads_data, ignore_index=True)
        return compiled_coverage, compiled_reads
    
    return pd.DataFrame(), pd.DataFrame()


# --- FUNÇÕES DE GERAÇÃO DE ARQUIVOS (ADAPTAÇÃO OROV) ---

def gerar_arquivo_fasta_orov(sequences_df, metadata, final_df, output_folder, run_codes, cnes_codes='cnes_lacen.csv'):
    """
    Gera o arquivo FASTA compilado e retorna o DataFrame combinado mestre.
    CORREÇÃO: Cria o DataFrame baseado estritamente nas amostras da corrida (run_codes),
    trazendo o metadado via Left Join. Isso filtra o metadado excedente.
    """
    
    # --- 1. PREPARAÇÃO DOS DADOS ---
    
    # Garante que run_codes é uma lista de strings limpas
    run_codes = [str(c).strip() for c in run_codes if str(c).strip()]
    
    # Cria o DataFrame MESTRE apenas com as amostras da corrida
    df_combine_sequence = pd.DataFrame({'Código_da_Amostra': run_codes})
    df_combine_sequence['Código_da_Amostra'] = df_combine_sequence['Código_da_Amostra'].astype(str)

    # Prepara Metadados (Estados e CNES)
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

    if os.path.exists(cnes_path):
        cnes_codes_df = pd.read_csv(cnes_path, dtype={'CNES': str, 'SIGLA': str})
        metadata['CNES_Laboratório_responsável'] = metadata['CNES_Laboratório_responsável'].astype(str)
        cnes_codes_df['CNES'] = cnes_codes_df['CNES'].astype(str)
        metadata = metadata.merge(cnes_codes_df, how='left', left_on='CNES_Laboratório_responsável', right_on='CNES')
        metadata['CNES_Laboratório_responsável'] = metadata['SIGLA'].fillna('NA_LAB')
        metadata.drop(columns=['CNES', 'SIGLA'], inplace=True)

    # Conversão de tipos
    if 'id' in sequences_df.columns:
        sequences_df = sequences_df.rename(columns={'id': 'Código_da_Amostra'})
    
    sequences_df['Código_da_Amostra'] = sequences_df['Código_da_Amostra'].astype(str)
    metadata['Código_da_Amostra'] = metadata['Código_da_Amostra'].astype(str)
    final_df['Código_da_Amostra'] = final_df['Código_da_Amostra'].astype(str)

    # --- 2. MERGES ESTRATÉGICOS (LEFT JOIN no Mestre) ---
    
    # Merge 1: Mestre (Run Codes) + Metadata
    # Isso garante que só fiquem as linhas do metadado que estão na corrida.
    # Se uma amostra da corrida não tiver metadado, ela fica com campos NaN (o que é correto para alertar).
    df_combine_sequence = pd.merge(df_combine_sequence, metadata, on="Código_da_Amostra", how='left', suffixes=('', '_dup'))

    # Merge 2: + Sequências (Consenso)
    df_combine_sequence = pd.merge(df_combine_sequence, sequences_df, on="Código_da_Amostra", how='left', suffixes=('', '_dup'))

    # Merge 3: + Métricas (Coverage/Reads)
    df_combine_sequence = pd.merge(df_combine_sequence, final_df, on="Código_da_Amostra", how='left', suffixes=('', '_dup'))

    # --------------------------------------------------------

    df_combine_sequence['Data_da_Coleta'] = pd.to_datetime(df_combine_sequence['Data_da_Coleta'], dayfirst=True, errors='coerce')
    df_combine_sequence['ANO_SEMANA_EPIDEMIOLOGICA'] = df_combine_sequence['Data_da_Coleta'].dt.strftime('%Y').fillna('ND')

    # Escrita do FASTA (Apenas para amostras com sequência válida)
    fasta_output_dir = os.path.join(output_folder)
    fasta_output_path = os.path.join(fasta_output_dir, 'LACEN_seq_OROV.fasta')
    
    with open(fasta_output_path, 'w') as outfile:
        for index, row in df_combine_sequence.iterrows():
            seq = row['sequence']
            
            # Validações de sequência
            if pd.isna(seq) or not isinstance(seq, str) or not seq.strip():
                continue
            if len(seq) > 10 and seq.upper().count('N') / len(seq) > 0.9:
                continue

            # Garante strings para evitar erro de concatenação com NaN
            estado = str(row['Estado_do_Solicitante']) if pd.notna(row['Estado_do_Solicitante']) else "Unknown"
            cnes = str(row['CNES_Laboratório_responsável']) if pd.notna(row['CNES_Laboratório_responsável']) else "Unknown"
            codigo_amostra = str(row['Código_da_Amostra'])
            ano = str(row['ANO_SEMANA_EPIDEMIOLOGICA'])
            segmento = str(row['segment']) if pd.notna(row['segment']) else "Unknown"
            
            base_header = f"hOROV/Brazil/{estado}-LACEN{cnes}-{codigo_amostra}/{ano}"
            seq_id = f">{base_header}|{segmento}"
            seq_id = format_virus_name(seq_id)
            
            outfile.write(f"{seq_id}\n{seq}\n")

    return df_combine_sequence


def planilha_resultado_orov(df_combine_sequence, output_folder):
    """ 
    Gera a Planilha de Resultado (Excel) para OROV. 
    Inclui lógica para lidar com falhas parciais e deixa Nome da Sequência vazio se falhou.
    """
    print("Gerando Planilha de Resultado OROV...")

    # 1. Identificar quais segmentos foram recuperados
    # Agrupa segmentos não-nulos
    segmentos_recuperados = df_combine_sequence.dropna(subset=['segment']).groupby('Código_da_Amostra')['segment'].apply(lambda x: ', '.join(sorted(x.unique()))).reset_index(name='Segmentos Recuperados')

    # 2. Desduplicação (1 linha por amostra)
    df_unique = df_combine_sequence.groupby('Código_da_Amostra').first().reset_index()
    
    # Remover colunas duplicadas
    df_unique = df_unique.loc[:, ~df_unique.columns.duplicated()]
    
    # Merge com a info dos segmentos
    df_unique = pd.merge(df_unique, segmentos_recuperados, on='Código_da_Amostra', how='left')
    df_unique['Segmentos Recuperados'] = df_unique['Segmentos Recuperados'].fillna("Nenhum")

    # Tratamento de NaNs (Falhas totais)
    df_unique['Reads'] = df_unique['Reads'].fillna(0)
    df_unique['Depth of Coverage'] = df_unique['Depth of Coverage'].fillna(0)
    df_unique['Coverage'] = df_unique['Coverage'].fillna(0)

    # 3. Montagem da Tabela
    result_table = pd.DataFrame()
    result_table['Gal Sequenciamento'] = df_unique['Requisição']
    result_table['Código Amostra'] = df_unique['Código_da_Amostra']
    
    # --- LÓGICA CONDICIONAL PARA O NOME DA SEQUÊNCIA ---
    # Gera o nome base para todos
    virus_name_raw = "hOROV/Brazil/" + \
        df_unique['Estado_do_Solicitante'].astype(str) + "-LACEN" + \
        df_unique['CNES_Laboratório_responsável'].astype(str) + "-" + \
        df_unique['Código_da_Amostra'].astype(str) + "/" + \
        df_unique['ANO_SEMANA_EPIDEMIOLOGICA'].astype(str)
    
    formatted_names = virus_name_raw.apply(format_virus_name)
    
    # Aplica a condição: Se "Segmentos Recuperados" for "Nenhum", deixa vazio.
    # Caso contrário, usa o nome formatado.
    result_table['Nome da Sequencia'] = np.where(
        (df_unique['Segmentos Recuperados'] == "Nenhum") | (df_unique['Segmentos Recuperados'] == ""), 
        "", 
        formatted_names
    )
    # ---------------------------------------------------

    result_table['Município'] = df_unique['Municipio_do_Solicitante']
    result_table['UF município solicitante'] = df_unique['Estado_do_Solicitante']
    result_table['Data Coleta'] = df_unique['Data_da_Coleta'].dt.strftime('%d/%m/%Y')
    result_table['Tipo Amostra'] = df_unique['Material_Biológico']
    result_table['Idade'] = df_unique['Idade']
    result_table['Tipo Idade'] = df_unique['Tipo_Idade']
    result_table['Sexo'] = df_unique['Sexo']

    result_table['Reads'] = df_unique['Reads']
    result_table['Profundiade Média'] = df_unique['Depth of Coverage']
    result_table['Cobertura'] = df_unique['Coverage']
    
    result_table['Segmentos Recuperados'] = df_unique['Segmentos Recuperados']

    # Colunas Fixas
    result_table["LACEN Executor"] = ""
    result_table["Unidade Federativa (UF)"] = "" 
    result_table["Responsável envio dos dados"] = ""
    result_table["Data sequenciamento"] = ""
    result_table["Vírus"] = "Oropouche"
    result_table["CT"] = "" 
    result_table["Software Montagem"] = "ViralFlow"
    result_table["Versão software"] = "1.0"
    result_table["Versão primer"] = "OROV_Naveca2023" 
    result_table["Versão Pangolin"] = ""
    result_table["Genótipo"] = "" 
    result_table["Linhagem"] = ""

    # Ordenação
    cols_order = [
        "LACEN Executor", "Unidade Federativa (UF)", "Responsável envio dos dados", "Data sequenciamento",
        "Vírus", 'Código Amostra', 'Gal Sequenciamento', "CT", 'Município', 'UF município solicitante',
        'Data Coleta', 'Tipo Amostra', 'Idade', "Tipo Idade", 'Sexo', 'Software Montagem', 
        "Versão software", "Versão primer", "Versão Pangolin", 'Reads','Profundiade Média', 'Cobertura', 
        'Segmentos Recuperados', 'Genótipo', 'Nome da Sequencia'
    ]
    
    # Garante colunas
    for c in cols_order:
        if c not in result_table.columns:
            result_table[c] = ""
            
    result_table = result_table[cols_order]

    # Salvar
    output_path = os.path.join(output_folder, 'Planilha_de_Resultado.xlsx')
    result_table.to_excel(output_path, index=False)
    print(f"Planilha de Resultados OROV gerada com sucesso!")


def arquivo_epiarbo_orov(config, metadata, df_combine_sequence, output_folder):
    """ Gera o arquivo EpiArbo para OROV. """
    print("Gerando arquivo EpiArbo OROV...")

    # Info Usuário
    submitter = config['user_info']['submitter']
    arbo_authors = config['user_info']['authors']
    arbo_orig_lab = config['user_info']['subm_lab']
    arbo_orig_lab_addr = config['user_info']['subm_lab_addr']
    arbo_subm_lab = config['user_info']['subm_lab']
    arbo_subm_lab_addr = config['user_info']['subm_lab_addr']

    # Desduplicação
    df_unique = df_combine_sequence.groupby('Código_da_Amostra').first().reset_index()
    df_unique = df_unique.loc[:, ~df_unique.columns.duplicated()]
    
    # IMPORTANTE: Filtrar apenas as amostras que geraram sequências para o EpiArbo?
    # Geralmente EpiArbo/GISAID só aceita se tiver fasta.
    # Verifica se tem sequence válida antes de incluir no CSV de submissão
    df_unique_valid = df_unique.dropna(subset=['sequence']).copy()
    
    if df_unique_valid.empty:
        print("Aviso: Nenhuma amostra gerou sequência válida para o EpiArbo.")
        return

    df_unique_valid = df_unique_valid.rename(columns={'Código_da_Amostra': 'id'})

    # Demografia
    arbo_patient_age = df_unique_valid[['id', 'Data_de_Nascimento', 'Data_da_Coleta']].copy()
    arbo_patient_age['Data_de_Nascimento'] = arbo_patient_age['Data_de_Nascimento'].astype(str).replace(to_replace=' .*', value='', regex=True)
    arbo_patient_age['Data_da_Coleta'] = pd.to_datetime(arbo_patient_age['Data_da_Coleta'], errors='coerce')
    arbo_patient_age['Data_de_Nascimento'] = pd.to_datetime(arbo_patient_age['Data_de_Nascimento'], errors='coerce', dayfirst=True)
    arbo_patient_age['arbo_patient_age'] = ((arbo_patient_age['Data_da_Coleta'] - arbo_patient_age['Data_de_Nascimento']).dt.days / 365.25).round().astype('Int64')
    arbo_patient_age = arbo_patient_age[['id', 'arbo_patient_age']]

    # Nome Vírus
    arbo_virus_name = df_unique_valid[['Estado_do_Solicitante', 'CNES_Laboratório_responsável', 'id', 'ANO_SEMANA_EPIDEMIOLOGICA']].astype(str)
    arbo_virus_name['arbo_virus_name'] = "hOROV/Brazil/" + \
        arbo_virus_name['Estado_do_Solicitante'] + "-LACEN" + \
        arbo_virus_name['CNES_Laboratório_responsável'] + "-" + \
        arbo_virus_name['id'] + "/" + arbo_virus_name['ANO_SEMANA_EPIDEMIOLOGICA']
    arbo_virus_name['arbo_virus_name'] = arbo_virus_name['arbo_virus_name'].apply(format_virus_name)
    arbo_virus_name = arbo_virus_name[['id', 'arbo_virus_name']]

    # Colunas Fixas
    arbo_virus_name.insert(0, 'submitter', submitter)
    arbo_virus_name.insert(1, 'fn', 'LACEN_seq_OROV.fasta')
    arbo_virus_name.insert(3, 'arbo_type', 'Oropouche virus')
    arbo_virus_name.insert(4, 'arbo_host', 'Human')
    arbo_virus_name.insert(5, 'arbo_passage', 'Original')

    # Merges
    arbo_collection_date = df_unique_valid[['id', 'Data_da_Coleta']].copy()
    arbo_collection_date['Data_da_Coleta'] = pd.to_datetime(arbo_collection_date['Data_da_Coleta']).dt.strftime('%Y-%m-%d')
    arbo_collection_date.rename(columns={'Data_da_Coleta': 'arbo_collection_date'}, inplace=True)
    gisaid_temp = pd.merge(arbo_virus_name, arbo_collection_date, on='id')

    # Location
    states = {'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA', 'Ceará': 'CE', 'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO', 'Maranhão': 'MA', 'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG', 'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE', 'Piauí': 'PI', 'Rio de Janeiro': 'RJ', 'Rio Grande do Norte': 'RN', 'Rio Grande do Sul': 'RS', 'Rondônia': 'RO', 'Roraima': 'RR', 'Santa Catarina': 'SC', 'São Paulo': 'SP', 'Sergipe': 'SE', 'Tocantins': 'TO'}
    arbo_location = df_unique_valid[['id', 'Estado_do_Solicitante', 'Municipio_do_Solicitante']].copy()
    arbo_location['Estado_do_Solicitante'] = arbo_location['Estado_do_Solicitante'].replace(states)
    arbo_location['Municipio_do_Solicitante'] = arbo_location['Municipio_do_Solicitante'].astype(str).str.capitalize().apply(unidecode)
    arbo_location['Estado_do_Solicitante'] = arbo_location['Estado_do_Solicitante'].astype(str).str.capitalize().apply(unidecode)
    arbo_location['arbo_location'] = "South America / Brazil / " + arbo_location['Estado_do_Solicitante'] + " / " + arbo_location['Municipio_do_Solicitante']
    gisaid_temp = pd.merge(gisaid_temp, arbo_location[['id', 'arbo_location']], on='id')

    gisaid_temp.insert(8, 'arbo_add_location', '')
    gisaid_temp.insert(10, 'arbo_add_host_info', '')
    gisaid_temp.insert(11, 'arbo_sampling_strategy', '')

    # Gender
    gender_map = {'MASCULINO': 'Male', 'FEMININO': 'Female', 'M': 'Male', 'F': 'Female', 'Masculino': 'Male', 'Feminino': 'Female'}
    arbo_gender = df_unique_valid[['id', 'Sexo']].copy()
    arbo_gender['Sexo'] = arbo_gender['Sexo'].replace(gender_map)
    gisaid_temp = pd.merge(gisaid_temp, arbo_gender.rename(columns={'Sexo': 'arbo_gender'}), on='id')

    gisaid_temp = pd.merge(gisaid_temp, arbo_patient_age, on='id')
    gisaid_temp['arbo_patient_status'] = 'Unknown'
    gisaid_temp['arbo_clinical_symptoms'] = ''

    bio_material_translation = {"Soro": "Serum", "Sangue": "Blood", "Urina": "Urine", "Liquor": "Cerebrospinal fluid (CSF)", "Plasma": "Plasma", "Swab": "Swab"}
    arbo_specimen = df_unique_valid[['id', 'Material_Biológico']].copy()
    arbo_specimen['arbo_specimen'] = arbo_specimen['Material_Biológico'].map(bio_material_translation).fillna('Unknown')
    gisaid_temp = pd.merge(gisaid_temp, arbo_specimen[['id', 'arbo_specimen']], on='id')

    gisaid_temp['arbo_outbreak'] = ''
    gisaid_temp['arbo_last_vaccination_date'] = ''
    gisaid_temp['arbo_treatment'] = ''
    gisaid_temp['arbo_seq_technology'] = 'Illumina MiSeq'
    gisaid_temp['arbo_assembly_method'] = 'Viralflow'

    arbo_coverage = df_unique_valid[['id', 'Depth of Coverage']].copy()
    gisaid_temp = pd.merge(gisaid_temp, arbo_coverage.rename(columns={'Depth of Coverage': 'arbo_coverage'}), on='id')

    gisaid_temp['arbo_publications'] = ''
    gisaid_temp['arbo_orig_lab'] = arbo_orig_lab
    gisaid_temp['arbo_orig_lab_addr'] = arbo_orig_lab_addr
    gisaid_temp['arbo_provider_sample_id'] = ''
    gisaid_temp['arbo_subm_lab'] = arbo_subm_lab
    gisaid_temp['arbo_subm_lab_addr'] = arbo_subm_lab_addr
    gisaid_temp['arbo_subm_sample_id'] = ''
    gisaid_temp['arbo_authors'] = arbo_authors

    gisaid_temp = gisaid_temp.drop('id', axis=1)

    final_cols = ['submitter', 'fn', 'arbo_virus_name', 'arbo_type', 'arbo_passage', 'arbo_collection_date',
            'arbo_location', 'arbo_add_location', 'arbo_host', 'arbo_add_host_info', 'arbo_sampling_strategy',
            'arbo_gender', 'arbo_patient_age', 'arbo_patient_status',  'arbo_clinical_symptoms',
            'arbo_specimen', 'arbo_outbreak', 'arbo_last_vaccination_date', 'arbo_treatment',
            'arbo_seq_technology', 'arbo_assembly_method', 'arbo_coverage', 'arbo_publications', 'arbo_orig_lab', 'arbo_orig_lab_addr',
            'arbo_provider_sample_id', 'arbo_subm_lab', 'arbo_subm_lab_addr',
            'arbo_subm_sample_id', 'arbo_authors']
    
    columns_desc = ['Submitter', 'FASTA filename', 'Virus name', 'Type', 'Passage details/history', 'Collection date',
            'Location', 'Additional location information', 'Host', 'Additional host information', 'Sampling Strategy',
            'Gender', 'Patient age', 'Patient status',  'Specific clinical symptoms',
            'Specimen source', 'Outbreak', 'Vaccination History', 'Treatment',
            'Sequencing technology', 'Assembly method', 'Depth of coverage', 'Publications', 'Originating lab', 'Address',
            'Sample ID given by the sample provider', 'Submitting lab', 'Address',
            'Sample ID given by the submitting laboratory', 'Authors']

    gisaid_temp = gisaid_temp[final_cols]
    header_df = pd.DataFrame([columns_desc], columns=final_cols)
    final_epiarbo = pd.concat([header_df, gisaid_temp], ignore_index=True)
    
    output_path = os.path.join(output_folder, 'EpiArbo.csv')
    final_epiarbo.to_csv(output_path, index=False)


# --- FUNÇÃO ORQUESTRADORA (Principal) ---
# Em report_generator_orov.py

def generate_compiled_report_orov(metadata_path, base_out_dir, config_path):
    print("Iniciando compilação de dados OROV (L, M, S)...")
    
    COMPILED_DIR = os.path.join(base_out_dir, "OROV_COMPILED_OUT")
    mod_pasta(COMPILED_DIR)
    
    LAST_SEGMENT_DIR = os.path.join(base_out_dir, f"OROV_{SEGMENTS[-1]['segment']}", "COMPILED_OUTPUT")
    
    # 1. Carga de QC e Erros (Base para definir quem foi sequenciado)
    compiled_coverage, compiled_reads = load_and_compile_segment_qc(base_out_dir, SEGMENTS)
    
    # Tenta carregar erros (necessário para listar amostras que falharam totalmente)
    errors = pd.DataFrame(columns=['cod'])
    try:
        errors_path = os.path.join(LAST_SEGMENT_DIR, 'errors_detected.csv')
        if os.path.exists(errors_path) and os.path.getsize(errors_path) > 0:
            errors = pd.read_csv(errors_path, sep=',')
            if 'cod' in errors.columns:
                errors['cod'] = errors['cod'].replace(to_replace='_.*', value='', regex=True)
    except Exception:
        pass # Erros não críticos aqui

    if compiled_coverage.empty and errors.empty:
        raise ValueError("Nenhum dado de cobertura ou erro encontrado. A pasta de saída parece vazia.")

    # --- DEFINIÇÃO DO UNIVERSO DE AMOSTRAS DA CORRIDA ---
    # Une códigos que tiveram sucesso (coverage) com códigos que falharam (errors)
    codes_success = set(compiled_coverage['cod'].unique()) if not compiled_coverage.empty else set()
    codes_failed = set(errors['cod'].unique()) if not errors.empty else set()
    run_codes = list(codes_success.union(codes_failed))
    # ----------------------------------------------------

    # Inicializa variáveis
    metadata = None
    config = None

    if metadata_path:
        print(f"Metadados fornecidos. Filtrando para {len(run_codes)} amostras da corrida atual.")
        try:
            config = load_config(config_path)
            # Carrega metadados brutos (pode ter erros_df vindo daqui tbm, mas já carregamos acima)
            metadata, _, records, _, _, _ = input_folder(LAST_SEGMENT_DIR, metadata_path)
            
            # --- AGREGAR MÉTRICAS ---
            if not compiled_coverage.empty:
                temp_coverage_filter = compiled_coverage.groupby('cod').agg({
                    'coverage_breadth': 'max',       
                    'mean_depth_coverage': 'mean'    
                }).reset_index()
                
                temp_reads_filter = compiled_reads.groupby('cod')['mepf_reads_aligned'].sum().reset_index(name='Reads')
                
                temp_coverage_filter = pd.merge(temp_coverage_filter, temp_reads_filter, on='cod', how='left')
                temp_coverage_filter['coverage_breadth'] = temp_coverage_filter['coverage_breadth'].multiply(100).round(2)
                temp_coverage_filter['mean_depth_coverage'] = temp_coverage_filter['mean_depth_coverage'].round(2)
                
                temp_coverage_filter.rename(columns={
                    'cod': 'Código_da_Amostra',
                    'coverage_breadth': 'Coverage',
                    'mean_depth_coverage': 'Depth of Coverage'
                }, inplace=True)
            else:
                temp_coverage_filter = pd.DataFrame(columns=['Código_da_Amostra', 'Coverage', 'Depth of Coverage', 'Reads'])

            # Carregar sequências
            sequences_df = load_segment_consensus(base_out_dir, SEGMENTS)
            
            # --- GERAÇÃO DO DATAFRAME MESTRE ---
            # Passamos run_codes para filtrar o metadado dentro da função
            df_combine_sequence = gerar_arquivo_fasta_orov(
                sequences_df, 
                metadata, 
                temp_coverage_filter, 
                COMPILED_DIR, 
                run_codes=run_codes # <--- Novo argumento
            )

            # Gera Relatórios
            arquivo_epiarbo_orov(config, metadata, df_combine_sequence, COMPILED_DIR)
            planilha_resultado_orov(df_combine_sequence, COMPILED_DIR)

        except Exception as e:
            print(f"ERRO ao processar metadados/arquivos finais: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Metadados NÃO fornecidos. Executando apenas Relatório de Qualidade Compilado.")

    # Validação e QC Gráfico
    cn_message, compiled_positive_coverage = validate_negative_control(compiled_coverage, errors)
    
    try:
        titulo = "Relatório de Qualidade OROV (Completo)" if metadata_path else "Relatório de Qualidade OROV (Sem Metadados)"
        Quality_monitor_interactive(
            coverage=compiled_coverage,
            reads=compiled_reads,
            errors=errors,
            output_folder=COMPILED_DIR,
            eligibility_threshold=60,
            report_title=titulo
        )
        print(f"Relatório QC Compilado gerado com sucesso!")
        
    except Exception as e:
        print(f"Erro ao gerar QC Plotly Compilado: {e}")
        import traceback
        traceback.print_exc()
    
    return compiled_coverage, compiled_reads