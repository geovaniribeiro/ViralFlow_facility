#!/usr/bin/env python3

#Carregar todas as lib usadas ao longo de todo script
import pandas as pd
import numpy as np
import subprocess
from matplotlib import pyplot as plt
import matplotlib.pyplot as plt
from matplotlib.cm import viridis 
import matplotlib.image as mpimg
from Bio import SeqIO
from Bio.SeqIO import FastaIO
import csv
import os
import sys
import shutil
import yaml
from unidecode import unidecode
import seaborn as sns

from scripts.modules.modules import load_config, mod_pasta, Quality_monitor, \
    remover_csv, input_folder,process_and_combine_data
from scripts.modules.modules_EpiArbo import filter_depth, format_virus_name 

# Load serotype and genotype files
def lineage_denv(output_folder):
    # Construct the file path for the serotype CSV file
    serotype_path = os.path.join(output_folder, "serotype.csv")
    serotype = pd.read_csv(serotype_path, sep=';')

    # Process serotype DataFrame
    serotype['seqName'] = serotype['seqName'].replace(to_replace='_.*', value='', regex=True)
    serotype.rename(columns={'seqName': 'cod', 'clade': 'serotype'}, inplace=True)
    serotype_filtered = serotype[['cod', 'serotype']]

    # Construct the file path for the genotype CSV file
    genotype_path = os.path.join(output_folder, "genotype.csv")
    genotype = pd.read_csv(genotype_path, sep=';')

    # Process genotype DataFrame
    genotype['seqName'] = genotype['seqName'].replace(to_replace='_.*', value='', regex=True)
    genotype.rename(columns={'seqName': 'cod', 'clade': 'lineage'}, inplace=True)
    genotype_filtered = genotype[['cod', 'lineage']]

    # Combine serotype and genotype filtered DataFrames
    lineage = pd.merge(serotype_filtered, genotype_filtered, on='cod', how='outer')

    return lineage

#Define as colunas do dataframe a serem renomeadas
rename_columns = {
        'cod': 'Código Amostra',
        'mepf_reads_aligned': 'Reads',
        'PCT_10X': 'Coverage',
        'MEAN_COVERAGE': 'Depth of Coverage',
        'serotype': 'Sorotipo',
        'lineage': 'Linhagem',
        'Requisição': 'Requisição',
        'Material_Biológico': 'Tipo Amostra',
        'Municipio_do_Solicitante': 'Município',
        'Data_da_Coleta': 'Data Coleta',
        'Sexo': 'Sexo'
    }

#Definir ordem das colunas
result_cols = [
        'Código Amostra', 'Requisição', 'CT', 'Tipo Amostra', 'Município', 'Data Coleta', 
        'Sexo', 'Reads', 'Coverage', 'Depth of Coverage', 'Sorotipo', 'Linhagem'
    ]

def planilha_resultado(arbo_virus_name, final_df, output_folder):

    print("planilha_resultado")

    result_table = arbo_virus_name[['id','arbo_virus_name']]

    #Merge df
    result_table = pd.merge(result_table, final_df, left_on = 'id', right_on = 'Código Amostra', how='right')

    #drop team_name column
    result_table.drop('Código Amostra', axis=1, inplace=True)

    #Change order header
    result_table = result_table[[ 'Requisição','id','arbo_virus_name', 'CT', 'Tipo Amostra', 'Município', 'Data Coleta', 'Sexo', 
                                 'Reads', 'Coverage', 'Depth of Coverage', 'Sorotipo', 'Linhagem']]
    #Mudar nomes da coluna
    result_table = result_table.rename(columns={'Requisição':'Gal Sequenciamento','id': 'Código Amostra', 
                                                'arbo_virus_name': 'Nome da Sequencia', 'Coverage': 'Cobertura', 
                                                'Depth of Coverage': 'Profundidade Média'})

    # Salve o DataFrame resultante em um arquivo Excel
    result_table.to_excel(os.path.join(output_folder, 'RNSG_REPORT/Planilha_de_Resultado.xlsx'), index=False)


#Função para gerar o arquivo fasta para ser submetido ao Gisaid
def gerar_arquivo_fasta(records, metadata, final_df, output_folder):

    print("gerar_arquivo_fasta")

    # Convert Column ID name to string
    metadata['Código_da_Amostra'] = metadata['Código_da_Amostra'].astype(str)

    # Dictionary to change the Name of the state to SIGLA
    states = {
        'Acre': 'AC',
        'Alagoas': 'AL',
        'Amapá': 'AP',
        'Amazonas': 'AM',
        'Bahia': 'BA',
        'Ceará': 'CE',
        'Distrito Federal': 'DF',
        'Espírito Santo': 'ES',
        'Goiás': 'GO',
        'Maranhão': 'MA',
        'Mato Grosso': 'MT',
        'Mato Grosso do Sul': 'MS',
        'Minas Gerais': 'MG',
        'Pará': 'PA',
        'Paraíba': 'PB',
        'Paraná': 'PR',
        'Pernambuco': 'PE',
        'Piauí': 'PI',
        'Rio de Janeiro': 'RJ',
        'Rio Grande do Norte': 'RN',
        'Rio Grande do Sul': 'RS',
        'Rondônia': 'RO',
        'Roraima': 'RR',
        'Santa Catarina': 'SC',
        'São Paulo': 'SP',
        'Sergipe': 'SE',
        'Tocantins': 'TO'
    }

    # Change the Name of the state to SIGLA
    metadata['Estado_do_Solicitante'] = metadata['Estado_do_Solicitante'].replace(states)

    # Dictionary to change the Name of the state to SIGLA
    cnes_lacen = {
        '2306352': 'AC',
        '2009129': 'AL',
        '2018764': 'AP',
        '2019639': 'AM',
        '4162': 'BA',
        '2611678': 'CE',
        '11371': 'DF',
        '12424': 'ES',
        '2338343': 'GO',
        '2697718': 'MA',
        '2604175': 'MT',
        '9997': 'MS',
        '2695294': 'MG',
        '2333163': 'PA',
        '2399350': 'PB',
        '2795965': 'PR',
        '2712075': 'PE',
        '2551888': 'PI',
        '2019639': 'RJ',
        '2693615': 'RN',
        '4066251': 'RS',
        '2496860': 'RO',
        '2476835': 'RR',
        '3157237': 'SC',
        '2091364': 'SP',
        '3532259': 'SE',
        '2494086': 'TO'
    }

    #convert column to string
    metadata['CNES_Laboratório_responsável'] = metadata['CNES_Laboratório_responsável'].astype(str)

    # Change the CNES of the executor LAB to SIGLA
    metadata['CNES_Laboratório_responsável'] = metadata['CNES_Laboratório_responsável'].replace(cnes_lacen)


    # Extract the sequence and ID from each record and store in a dictionary
    data = {'id': [r.id for r in records], 'sequence': [str(r.seq) for r in records]}

    # Convert the dictionary to a pandas DataFrame
    df_sequence = pd.DataFrame(data)

    #Remover campos apos o ID
    df_sequence = df_sequence[['id','sequence']].replace(to_replace ='_.*', value = '', regex = True)

    ##Combinte the both subset based on ID sequence name
    df_combine_sequence = pd.merge(df_sequence, metadata, left_on="id", right_on="Código_da_Amostra")

    #Controle de qualidade (cobertura)
    final_df = final_df.loc[final_df['Coverage'] >= 60]

    final_df = final_df.astype(str)

    df_combine_sequence = pd.merge(df_combine_sequence, final_df, left_on="id", right_on="Código Amostra")

    #Extract yerar collect date
    df_combine_sequence['Data_da_Coleta'] = pd.to_datetime(df_combine_sequence['Data_da_Coleta'], format="%d-%m-%Y")
    df_combine_sequence['ANO_SEMANA_EPIDEMIOLOGICA'] = df_combine_sequence['Data_da_Coleta'].dt.strftime('%Y')

    #Cria um arquivo chamado 'seq_df.csv' para ser usado na geração do fasta
    df_combine_sequence.to_csv(os.path.join(output_folder, 'seq_df.csv'), sep = ',')

    # Convert DataFrame df_combine_sequence to a fasta file with the required header format
    with open(os.path.join(output_folder, 'seq_df.csv')) as csvfile, open(os.path.join(output_folder,'RNSG_REPORT/LACEN_seq.fasta'), 'w') as outfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
                seq_id = f">h{row['Sorotipo']}/Brazil/{row['Estado_do_Solicitante']}-LACEN{row['CNES_Laboratório_responsável']}-{row['id']}/{row['ANO_SEMANA_EPIDEMIOLOGICA']}"
                seq_id = format_virus_name(seq_id)
                seq = row['sequence']
                outfile.write(f"{seq_id}\n{seq}\n")
    
    return df_combine_sequence

#Função para gerar o arquivo EpiArbo para ser submetido ao Gisaid
def arquivo_epiarbo(config, metadata, df_combine_sequence, output_folder):

    print("arquivo_epiarbo")

    #Columnas que serão inseridas manualmente
    #Nickname do submitter no gisaid
    submitter = config['user_info']['submitter']

    #Lista de autores CGLAB + LACEN
    arbo_authors = config['user_info']['authors']

    arbo_orig_lab = config['user_info']['subm_lab']

    arbo_orig_lab_addr = config['user_info']['subm_lab_addr']

    arbo_subm_lab = config['user_info']['subm_lab']

    arbo_subm_lab_addr = config['user_info']['subm_lab_addr']


    #Nome do arquivo fasta
    fn = "LACEN_seq.fasta"

    #Dicionario para mudar o Nome do estado para SIGLA
    states = {
        'AC': 'Acre',
        'AL': 'Alagoas',
        'AP': 'Amapá',
        'AM': 'Amazonas',
        'BA': 'Bahia',
        'CE': 'Ceará',
        'DF': 'Distrito Federal',
        'ES': 'Espírito Santo',
        'GO': 'Goiás',
        'MA': 'Maranhão',
        'MT': 'Mato Grosso',
        'MS': 'Mato Grosso do Sul',
        'MG': 'Minas Gerais',
        'PA': 'Pará',
        'PB': 'Paraíba',
        'PR': 'Paraná',
        'PE': 'Pernambuco',
        'PI': 'Piauí',
        'RJ': 'Rio de Janeiro',
        'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul',
        'RO': 'Rondônia',
        'RR': 'Roraima',
        'SC': 'Santa Catarina',
        'SP': 'São Paulo',
        'SE': 'Sergipe',
        'TO': 'Tocantins'
    }

    #Insert arbo_patient_age column
    ##Extrair campos de intersse
    arbo_patient_age = df_combine_sequence[['id','Data_de_Nascimento','Data_da_Coleta']]

    ##Remover campo extrar (hora)
    arbo_patient_age.loc[:,'Data_de_Nascimento'] = arbo_patient_age['Data_de_Nascimento'].replace(to_replace =' .*', value = '', regex = True)

    ##Conveter colunas para Data
    arbo_patient_age.loc[:,'Data_de_Nascimento'] = pd.to_datetime(arbo_patient_age['Data_de_Nascimento'], errors='coerce', dayfirst=True)
    arbo_patient_age.loc[:,'Data_da_Coleta'] = pd.to_datetime(arbo_patient_age['Data_da_Coleta'], errors='coerce')

    # Garante que estamos trabalhando em uma cópia segura
    arbo_patient_age = arbo_patient_age.copy()  
    # Certifique-se de que as colunas estão no formato datetime
    arbo_patient_age['Data_da_Coleta'] = pd.to_datetime(arbo_patient_age['Data_da_Coleta'], errors='coerce')
    arbo_patient_age['Data_de_Nascimento'] = pd.to_datetime(arbo_patient_age['Data_de_Nascimento'], errors='coerce')
    #Subtrair a data da coleta e data de nascimento
    arbo_patient_age.loc[:, 'arbo_patient_age'] = (arbo_patient_age['Data_da_Coleta'] - arbo_patient_age['Data_de_Nascimento'])
    arbo_patient_age = arbo_patient_age[['id','arbo_patient_age']]

    #Virus name
    arbo_virus_name = df_combine_sequence[['Estado_do_Solicitante','CNES_Laboratório_responsável','id','ANO_SEMANA_EPIDEMIOLOGICA', 'Sorotipo']].astype(str)
    arbo_virus_name.loc[:,'arbo_virus_name'] = "h" + arbo_virus_name['Sorotipo'] + "/Brazil/" + arbo_virus_name['Estado_do_Solicitante'] + "-LACEN" + arbo_virus_name['CNES_Laboratório_responsável'] + "-" + arbo_virus_name['id'] + "/" + arbo_virus_name['ANO_SEMANA_EPIDEMIOLOGICA']
    # Converte nome 1º e Ultima Maiúscula
    arbo_virus_name['arbo_virus_name'] = arbo_virus_name['arbo_virus_name'].apply(format_virus_name)
    arbo_virus_name = arbo_virus_name[['id', 'arbo_virus_name']]

    #Insert submitter column
    arbo_virus_name.insert(0, 'submitter','')
    arbo_virus_name.loc[:, 'submitter'] = submitter


    #Insert fn (fasta file name) column
    arbo_virus_name.insert(1, 'fn', '')

    arbo_virus_name.loc[:, 'fn'] = 'LACEN_seq.fasta'


    #Insert arbo_type column
    arbo_virus_name.insert(4, 'arbo_type', '')
    arbo_virus_name.loc[:, 'arbo_type'] = 'Dengue Virus'

    #Insert arbo_subtype column
    arbo_virus_name.insert(5, 'arbo_subtype', '')
    arbo_virus_name.loc[:, 'arbo_subtype'] = df_combine_sequence['Sorotipo']

    #Insert arbo_passage column
    arbo_virus_name.insert(6, 'arbo_passage', '')

    arbo_virus_name.loc[:, 'arbo_passage'] = 'Original'

    arbo_virus_name.to_excel(os.path.join(output_folder,'RNSG_REPORT/Planilha_de_Resultado.xlsx'), index=False)

    #Collection date
    arbo_collection_date = df_combine_sequence[['id','Data_da_Coleta']]
    arbo_collection_date = arbo_collection_date.copy()  # Garante que estamos trabalhando em uma cópia segura
    arbo_collection_date['Data_da_Coleta'] = pd.to_datetime(arbo_collection_date['Data_da_Coleta']).dt.strftime('%Y-%m-%d')
    arbo_collection_date = arbo_collection_date.rename(columns={'Data_da_Coleta': 'arbo_collection_date'})

    arbo_collection_date = arbo_collection_date.astype(str)

    gisaid_temp = pd.merge(arbo_virus_name,arbo_collection_date,on='id')

   #Location
    ##Continent / Country / State / Municipality
    arbo_location = df_combine_sequence[['id','Estado_do_Solicitante','Municipio_do_Solicitante']]

    ##Mudar as linhas da SIGLA para NOME
    arbo_location.loc[:,'Estado_do_Solicitante'] = arbo_location['Estado_do_Solicitante'].replace(states)

    #Deixar apenas primeira letra maiuscula, pois no GAL geralmente vem tudo maiúsculo, e remove acentos (Municío solicitante e estados)
    arbo_location.loc[:,'Municipio_do_Solicitante'] = arbo_location['Municipio_do_Solicitante'].apply(str.capitalize).apply(unidecode)
    arbo_location.loc[:,'Estado_do_Solicitante'] = arbo_location['Estado_do_Solicitante'].apply(str.capitalize).apply(unidecode)

    arbo_location = arbo_location.copy()  # Garante que estamos trabalhando em uma cópia segura
    arbo_location.loc[:,'arbo_location'] = "South America / Brazil / " + arbo_location['Estado_do_Solicitante'] + " / " + arbo_location['Municipio_do_Solicitante']
    arbo_location = arbo_location[['id','arbo_location']]

    arbo_location = arbo_location.astype(str)

    gisaid_temp = pd.merge(gisaid_temp,arbo_location,on='id')

    #Insert arbo_add_location column
    gisaid_temp.insert(9, 'arbo_add_location', '')


    #Insert arbo_host column
    gisaid_temp.insert(10, 'arbo_host', '')
    gisaid_temp.loc[:, 'arbo_host'] = 'Human'



    #Insert arbo_add_host_info column
    gisaid_temp.insert(11, 'arbo_add_host_info', '')


    #Insert arbo_sampling_strategy column
    gisaid_temp.insert(12, 'arbo_sampling_strategy', '')


    #Gender (Male / Female)
    arbo_gender = df_combine_sequence[['id','Sexo_x']]

    gender = {
        'Masculino':'Male',
        'Feminino':'Female'
    }



    arbo_gender.loc[:,'Sexo_x'] = arbo_gender['Sexo_x'].replace(gender)

    arbo_gender = arbo_gender.rename(columns={'Sexo_x': 'arbo_gender'})

    arbo_gender = arbo_gender.astype(str)

    gisaid_temp = pd.merge(gisaid_temp,arbo_gender,on='id')


    #Insert arbo_patient_age column
    ##Extrair campos de intersse
    arbo_patient_age = df_combine_sequence[['id','Data_de_Nascimento','Data_da_Coleta']]

    ##Remover campo extrar (hora)
    arbo_patient_age.loc[:,'Data_de_Nascimento'] = arbo_patient_age['Data_de_Nascimento'].replace(to_replace =' .*', value = '', regex = True)

    ##Conveter colunas para Data
    #arbo_patient_age.loc[:,'Data_de_Nascimento'] = pd.to_datetime(arbo_patient_age['Data_de_Nascimento'], errors='coerce')
    arbo_patient_age.loc[:, 'Data_de_Nascimento'] = pd.to_datetime(arbo_patient_age['Data_de_Nascimento'], errors='coerce', dayfirst=True)
    arbo_patient_age.loc[:,'Data_da_Coleta'] = pd.to_datetime(arbo_patient_age['Data_da_Coleta'], errors='coerce')

    # Garante que estamos trabalhando em uma cópia segura
    arbo_patient_age = arbo_patient_age.copy()  
    # Certifique-se de que as colunas estão no formato datetime
    arbo_patient_age['Data_da_Coleta'] = pd.to_datetime(arbo_patient_age['Data_da_Coleta'], errors='coerce')
    arbo_patient_age['Data_de_Nascimento'] = pd.to_datetime(arbo_patient_age['Data_de_Nascimento'], errors='coerce')
    ##Subtrair a data da coleta e data de nascimento (em dias), converter para ano (dividindo por 365.25), e aredendar (remove decimal)
    arbo_patient_age['arbo_patient_age'] = ((arbo_patient_age['Data_da_Coleta'] - arbo_patient_age['Data_de_Nascimento']).dt.days / 365.25).round().astype(int)
    arbo_patient_age = arbo_patient_age[['id','arbo_patient_age']]

    arbo_patient_age = arbo_patient_age.astype(str)

    gisaid_temp = pd.merge(gisaid_temp,arbo_patient_age,on='id')


    #Insert arbo_patient_status column
    gisaid_temp.insert(15, 'arbo_patient_status','')
    gisaid_temp.loc[:, 'arbo_patient_status'] = 'Unknown'


    #Insert arbo_patient_status column
    gisaid_temp.insert(16, 'arbo_disease_manifestation','')
    gisaid_temp.loc[:, 'arbo_disease_manifestation'] = ''

    #Insert arbo_patient_status column
    gisaid_temp.insert(17, 'arbo_clinical_symptoms','')
    gisaid_temp.loc[:, 'arbo_clinical_symptoms'] = ''


    #Insert arbo_specimen column
    gisaid_temp.insert(18, 'arbo_specimen','')


    #Insert arbo_outbreak column
    gisaid_temp.insert(19, 'arbo_outbreak','')

    #Insert arbo_outbreak column
    gisaid_temp.insert(20, 'arbo_last_vaccinated','')


    #Insert arbo_last_vaccination_date column
    gisaid_temp.insert(21, 'arbo_last_vaccination_date','')


    #Insert arbo_treatment column
    gisaid_temp.insert(22, 'arbo_treatment','')

    #Insert arbo_seq_technology column
    gisaid_temp.insert(23, 'arbo_seq_technology','')
    gisaid_temp.loc[:, 'arbo_seq_technology'] = 'Illumina MiSeq'

    #Insert arbo_assembly_method column
    gisaid_temp.insert(24, 'arbo_assembly_method','')
    gisaid_temp.loc[:, 'arbo_assembly_method'] = 'Viralflow'


    #Insert arbo_coverage column
    ##Extrair campos de intersse
    arbo_coverage = df_combine_sequence[['id','Depth of Coverage']]

    arbo_coverage = arbo_coverage.rename(columns={'Depth of Coverage': 'arbo_coverage'})

    arbo_coverage = arbo_coverage.astype(str)

    gisaid_temp = pd.merge(gisaid_temp,arbo_coverage,on='id')

    #Insert arbo_orig_lab column
    gisaid_temp.insert(26, 'arbo_publications','')


    #Insert arbo_orig_lab column
    gisaid_temp.insert(27, 'arbo_orig_lab','')
    gisaid_temp.loc[:, 'arbo_orig_lab'] = arbo_orig_lab


    #Insert arbo_orig_lab_addr column
    gisaid_temp.insert(28, 'arbo_orig_lab_addr','')
    gisaid_temp.loc[:, 'arbo_orig_lab_addr'] = arbo_orig_lab_addr


    #Insert arbo_provider_sample_id column
    gisaid_temp.insert(29, 'arbo_provider_sample_id','')


    #Insert arbo_subm_lab column
    gisaid_temp.insert(30, 'arbo_subm_lab','')
    gisaid_temp.loc[:, 'arbo_subm_lab'] = arbo_subm_lab


    #Insert arbo_subm_lab_addr column
    gisaid_temp.insert(31, 'arbo_subm_lab_addr','')
    gisaid_temp.loc[:, 'arbo_subm_lab_addr'] = arbo_subm_lab_addr


    #Insert arbo_subm_sample_id column
    gisaid_temp.insert(32, 'arbo_subm_sample_id','')



    #Insert arbo_authors column
    gisaid_temp.insert(33, 'arbo_authors','')
    gisaid_temp.loc[:, 'arbo_authors'] = arbo_authors

    gisaid_temp = gisaid_temp.drop('id', axis=1)

    # # Define column names
    columns = ['Submitter', 'FASTA filename', 'Virus name', 'Type', 'Serotype', 'Passage details/history', 'Collection date',
            'Location', 'Additional location information', 'Host', 'Additional host information', 'Sampling Strategy',
            'Gender', 'Patient age', 'Patient status',  'Disease manifestation', 'Specific clinical symptoms',
            'Specimen source', 'Outbreak', 'Vaccination History', 'Last vaccinated', 'Treatment',
            'Sequencing technology', 'Assembly method', 'Depth of coverage', 'Publications', 'Originating lab', 'Address',
            'Sample ID given by the sample provider', 'Submitting lab', 'Address',
            'Sample ID given by the submitting laboratory', 'Authors']


    # Crie um novo DataFrame com as colunas desejadas
    new_row = pd.DataFrame([columns], columns=gisaid_temp.columns)

    # Concatene o novo DataFrame com o DataFrame original e redefina o índice
    gisaid_temp = pd.concat([new_row, gisaid_temp], ignore_index=True)

    gisaid_temp = gisaid_temp.set_index('submitter')

    gisaid_temp.to_csv(os.path.join(output_folder, 'RNSG_REPORT/EpiArbo.csv'))

    pass


def generate_report_denv(metadata_path, config_path, output_folder):

    # Carregar configurações
    config = load_config(config_path)
    
    mod_pasta(output_folder)
    
    # Processar os arquivos na pasta de entrada
    metadata, sequence, records, reads, coverage = input_folder(output_folder, metadata_path)
    lineage = lineage_denv(output_folder)

    df_combine_sequence = process_and_combine_data(metadata, reads, coverage, lineage, 
                                                   output_folder, rename_columns,result_cols)

    # Trabalhar com arquivos de resultados
    resultado_file = os.path.join(output_folder, "tabela_resultados.csv")
    if os.path.exists(resultado_file):
        final_df = pd.read_csv(resultado_file)
        filter_depth(final_df, output_folder)
    else:
        raise FileNotFoundError(f"Arquivo {resultado_file} não encontrado!")

    resultado_filt_file = os.path.join(output_folder, "tabela_resultados_filt.csv")
    if os.path.exists(resultado_filt_file):
        final_df_filt = pd.read_csv(resultado_filt_file)
    else:
        raise FileNotFoundError(f"Arquivo {resultado_filt_file} não encontrado!")

    # Gerar arquivos auxiliares
    gerar_arquivo_fasta(records, metadata, final_df, output_folder)

    seq_file = os.path.join(output_folder, "seq_df.csv")
    if os.path.exists(seq_file):
        df_combine_sequence = pd.read_csv(seq_file)
        arquivo_epiarbo(config, metadata, df_combine_sequence, output_folder)
    else:
        raise FileNotFoundError(f"Arquivo {seq_file} não encontrado!")

    arbo_virus_name = os.path.join(output_folder, 'RNSG_REPORT/Planilha_de_Resultado.xlsx')
    if os.path.exists(arbo_virus_name):
        covv_virus_name = pd.read_excel(arbo_virus_name)
        planilha_resultado(covv_virus_name, final_df, output_folder)
    else:
        raise FileNotFoundError(f"Arquivo {arbo_virus_name} não encontrado!")



    Quality_monitor(coverage, reads, final_df, output_folder)

    # Limpar arquivos temporários e monitorar qualidade
    remover_csv(output_folder)

# Mantém a funcionalidade standalone
if __name__ == "__main__":
    output_folder = sys.argv[1]
    metadata_path = sys.argv[2]
    config_path = sys.argv[3]
    generate_report_denv(output_folder, metadata_path, config_path)