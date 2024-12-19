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

## Função que carrega o arquivo yaml e armazena em um dicionario
def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

#faz algumas mudancas em alguns nomes (deixar apenas o codigo de amostra)
def input_folder(output_folder, metadata_path):

    #print("input_folder")

    # #OBS: VERIFICAR QUAL CAMPO SEPARADOR NO ARQUIVO GAL
    metadata_redundante = pd.read_csv(metadata_path, sep =';', encoding='latin-1', on_bad_lines='skip', 
                           low_memory=False)
    
    # Remover duplicatas com base na coluna 'Requisição'
    metadata = metadata_redundante.drop_duplicates(subset=['Requisição'])

    # #Substituir espaços por '_' entre palavras da coluns
    metadata.columns = metadata.columns.str.replace(' ', '_')

    #Ler arquivo fasta
    #Certificar se o cabelho das sequencias possuem apenas o codigo da amostra.

    # Construct the file path for the CSV file
    sequence_path = os.path.join(output_folder, "seqbatch.fa")

    sequence = open(sequence_path)

    #converter fasta to dataframe
    ## Load the FASTA file into a list of SeqRecord objects
    records = list(SeqIO.parse(sequence_path, "fasta"))

    #Carregar os seguintes arquivos do ViralFlow

    # Construct the file path for the CSV file
    reads_path = os.path.join(output_folder, "reads_count.csv")

    reads = pd.read_csv(reads_path, sep =',')

    reads['cod'] = reads['cod'].replace(to_replace ='_.*', value = '', regex = True)

    #short_summary.csv
    #coverage = pd.read_csv('/content/short_summary.csv', sep =',')
    #coverage['cod'] = coverage['cod'].replace(to_replace ='_.*', value = '', regex = True)

    #wgs
    # Construct the file path for the CSV file
    coverage_path = os.path.join(output_folder, 'wgs.csv')

    coverage = pd.read_csv(coverage_path, sep =',')
    coverage['cod'] = coverage['cod'].replace(to_replace ='_.*', value = '', regex = True)


    # Construct the file path for the serotype CSV file
    serotype_path = os.path.join(output_folder, "serotype.csv")

    serotype = pd.read_csv(serotype_path, sep =';')

    serotype['seqName'] = serotype['seqName'].replace(to_replace ='_.*', value = '', regex = True)
    serotype.rename(columns={'seqName': 'cod'}, inplace=True)


    # Construct the file path for the genotype CSV file
    genotype_path = os.path.join(output_folder, "genotype.csv")

    genotype = pd.read_csv(genotype_path, sep =';')

    genotype['seqName'] = genotype['seqName'].replace(to_replace ='_.*', value = '', regex = True)
    genotype.rename(columns={'seqName': 'cod'}, inplace=True)


    return metadata, sequence, records, reads, serotype, genotype, coverage


#Adiciona a pasta de RNSG_REPORT, a qual serao a adiciona os graficos, planilha, e outros
# Adiciona a pasta de output no caminho informado
def mod_pasta(output_folder):
    # O caminho informado no argumento $1
    nome_pasta = output_folder

    # Verifica se a pasta 'RNSG_REPORT' já existe, se sim, a remove
    output_path = os.path.join(nome_pasta, 'RNSG_REPORT')
    
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    
    # Cria a pasta 'RNSG_REPORT' dentro da pasta de saida do viralflow
    os.mkdir(output_path)


def planilha_results(metadata, reads, coverage, serotype, genotype, output_folder):

    #print("Gerando Planilhas resultados")

    # Mudar o SEXO de nome para sigla
    sexo = {'MASCULINO': 'M', 'FEMININO': 'F'}
    metadata['Sexo'] = metadata['Sexo'].replace(sexo)


    # Remover redundância nome Tipo de Amotra
    metadata['Material_Biológico'] = metadata['Material_Biológico'].replace(to_replace=' .*', value='', regex=True)

    # Extrair as informações de cada dataset
    metadata_GAL_update = metadata[['Código_da_Amostra', 'Requisição', 'CT', 'Material_Biológico', 'Municipio_do_Solicitante', 'Data_da_Coleta', 'Sexo']]
    metadata_GAL_update.loc[:,'Data_da_Coleta'] = pd.to_datetime(metadata_GAL_update['Data_da_Coleta'], format="%d-%m-%Y").dt.strftime('%d-%m-%Y')

    #reads_update = reads[['cod', 'total_reads']]

    # DEFINIR A PROFUNDIDADE MÍNIMA USADA PARA MONTAGEM
    coverage_update = coverage[['cod', 'PCT_10X', 'MEAN_COVERAGE']]

    # Juntar todas as planilhas
    resultado_df_1 = pd.merge(pd.merge(pd.merge(reads, coverage_update, on='cod'), serotype, on='cod'), genotype, on='cod')
    #resultado_df_1 = pd.merge(reads, coverage_update, on='cod')
    resultado_df_1['cod'] = resultado_df_1['cod'].astype(str)
    metadata_GAL_update.loc[:,'Código_da_Amostra'] = metadata_GAL_update['Código_da_Amostra'].astype(str)
    metadata_GAL_update.loc[:,'Requisição'] = metadata_GAL_update['Requisição'].astype(str)

    resultado_df = pd.merge(resultado_df_1, metadata_GAL_update, left_on="cod", right_on="Código_da_Amostra")

    # Mudar nomes da coluna
    resultado_df = resultado_df.rename(columns={'cod': 'Código Amostra', 'mepf_reads_aligned': 'Reads', 'PCT_10X': 'Coverage', 
                                                'MEAN_COVERAGE': 'Depth of Coverage', 'clade_x' : 'Sorotipo', 'clade_y' : 'Linhagem',
                                                'Requisição': 'Requisição', 'Material_Biológico': 'Tipo Amostra', 
                                                'Municipio_do_Solicitante': 'Município','Data_da_Coleta': 'Data Coleta', 'Sexo': 'Sexo'})

    # Mudar ordem das colunas
    cols = ['Código Amostra', 'Requisição', 'CT', 'Tipo Amostra', 'Município', 'Data Coleta', 'Sexo', 'Reads', 'Coverage', 
            'Depth of Coverage', 'Sorotipo', 'Linhagem']
    resultado_df = resultado_df[cols]

    # Convert Column ID name to string
    resultado_df['Coverage'] = resultado_df['Coverage'].astype(float)

    # Converter valor de coverage para porcentagem
    resultado_df['Coverage'] = resultado_df['Coverage'].multiply(100).round(2)

    # Convert Column ID name to string
    resultado_df['Depth of Coverage'] = resultado_df['Depth of Coverage'].astype(float).round(2)

    resultado_df = resultado_df.set_index('Requisição')

    resultado_df.to_csv(os.path.join(output_folder, "tabela_resultados.csv"))

    return resultado_df

def planilha_resultado(arbo_virus_name, resultado_df, output_folder):

    print("planilha_resultado")

    result_table = arbo_virus_name[['id','arbo_virus_name']]

    #Merge df
    result_table = pd.merge(result_table, resultado_df, left_on = 'id', right_on = 'Código Amostra', how='right')

    #drop team_name column
    result_table.drop('Código Amostra', axis=1, inplace=True)

    #Change order header
    result_table = result_table[[ 'Requisição','id','arbo_virus_name', 'CT', 'Tipo Amostra', 'Município', 'Data Coleta', 'Sexo', 
                                 'Reads', 'Coverage', 'Depth of Coverage', 'Sorotipo', 'Linhagem']]

    # add an empty column named 'Barcode' at index 0
    result_table.insert(0, 'Barcode',None)

    # add an empty column named 'N Barcode' at index 1
    result_table.insert(1, 'N Barcode',None)

    #Mudar nomes da coluna
    result_table = result_table.rename(columns={'Requisição':'Gal Sequenciamento','id': 'Código Amostra', 
                                                'arbo_virus_name': 'Nome da Sequencia', 'Coverage': 'Cobertura', 
                                                'Depth of Coverage': 'Profundidade Média'})

    # Salve o DataFrame resultante em um arquivo Excel
    result_table.to_excel(os.path.join(output_folder, 'RNSG_REPORT/Planilha_de_Resultado.xlsx'), index=False)

#A função 'filter_depth' gera um arquivo intermediário 'tabela_resultados_filt.csv' com informações apenas das amostras com cobertua > 60%
def filter_depth(resultado_df, output_folder):

    resultado_df_filt = resultado_df.loc[resultado_df['Coverage'] >= 60]

    resultado_df_filt.to_csv(os.path.join(output_folder, "tabela_resultados_filt.csv"))

    return resultado_df_filt



#Função para gerar o arquivo fasta para ser submetido ao Gisaid
def gerar_arquivo_fasta(records, metadata, resultado_df, output_folder):

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
    resultado_df = resultado_df.loc[resultado_df['Coverage'] >= 60]

    resultado_df = resultado_df.astype(str)

    df_combine_sequence = pd.merge(df_combine_sequence, resultado_df, left_on="id", right_on="Código Amostra")

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
                seq_id = seq_id.replace('DENV', 'DenV')
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
    arbo_virus_name = arbo_virus_name.replace('DENV', 'DenV')
    arbo_virus_name = arbo_virus_name[['id','arbo_virus_name']]


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

#Função para criar um grafico com métricas gerais da corrida, para aferição de controle de qualidade
def Quality_monitor(coverage, reads, resultado_df, output_folder):

    print("QualityCheck")

    coverage['PCT_10X'] = coverage['PCT_10X']*100

    #Criar os subplots e os seus respec. eixos x
    fig = plt.figure()
    #axs = axs.flatten()

    gs = fig.add_gridspec(2,2)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])
    #ax4 = fig.add_subplot(gs[2, :])


    # Depth of Coverage (X)
    sns.violinplot(y='MEAN_COVERAGE', data=coverage, 
               inner="points", ax=ax1, cut= 0)
    
    sns.swarmplot(y='MEAN_COVERAGE', data=coverage, ax=ax1,
                  color = 'black', size=3)

    # Pinte a linha com 'CN' de outra cor (neste caso, vermelho)
    linha_cn = coverage[coverage['cod'] == 'CN']

    if not linha_cn.empty:
            ax1.scatter(x=0, y=linha_cn['PCT_10X'], color='red', 
                        marker='o', label='CN', s=20)

            ax2.scatter(x=0, y=linha_cn['MEAN_COVERAGE'], color='red', 
                        marker='o', label='CN', s=20)

    # Coverage (%)
    sns.violinplot(y='PCT_10X', data=coverage, ax=ax2, cut= 0)
    

    sns.swarmplot(y='PCT_10X', data=coverage, ax=ax2,
                  color = 'black', size=3)


    #Reads Mapeadas X reads unmapped
    #Calcular o numero de redas unmmapped
    reads['unmapped'] = reads['total_reads'] - reads['mepf_reads_aligned']

    #select reads columns
    reads_df = reads[['cod','mepf_reads_aligned','unmapped']]


    # Define a color palette using Seaborn
    colors = sns.color_palette("viridis")
    #create stacked bar chart
    reads_df.set_index('cod').plot(kind='bar', stacked=True, ax=ax3)
    
    #Gênero x Idade


    #Depth X Coverage
    #ax4.scatter(x=coverage['MEAN_COVERAGE'], y=coverage['PCT_10X'])



    # Set ylabels
    ax1.set_ylabel('Profundidade')
    ax2.set_ylabel('Cobertura (%)')
    ax3.set_ylabel('Leituras Geradas')
    ax3.set_xlabel('Amostras')
    #ax3.set_xticklabels(size=6)
    ax3.tick_params(axis='x', labelsize=6)
    ax3.legend(["Leituras mapeadas", "Leituras não-mapeadas"], bbox_to_anchor=(0.5, 1),
               prop = { "size": 6})
    #axs[3].set_ylabel('Reads Mapeadas vs não-mapeadas', fontsize=12)


    # save the plot as SVG file
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, "RNSG_REPORT/Quality_ckeck.png"), format='png', dpi = 300)

def Quality_monitor(coverage, reads, resultado_df, output_folder):

    #print("QualityCheck")

    coverage['PCT_10X'] = coverage['PCT_10X']*100

    #Criar os subplots e os seus respec. eixos x
    fig = plt.figure()
    #axs = axs.flatten()

    gs = fig.add_gridspec(2,2)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])
    #ax4 = fig.add_subplot(gs[2, :])


    # Depth of Coverage (X)
    sns.violinplot(y='MEAN_COVERAGE', data=coverage, 
               inner="points", ax=ax1, cut= 0)
    
    sns.swarmplot(y='MEAN_COVERAGE', data=coverage, ax=ax1,
                  color = 'black', size=3)

    # Pinte a linha com 'CN' de outra cor (neste caso, vermelho)
    linha_cn = coverage[coverage['cod'] == 'CN']

    if not linha_cn.empty:
            ax1.scatter(x=0, y=linha_cn['PCT_10X'], color='red', 
                        marker='o', label='CN', s=20)

            ax2.scatter(x=0, y=linha_cn['MEAN_COVERAGE'], color='red', 
                        marker='o', label='CN', s=20)

    # Coverage (%)
    sns.violinplot(y='PCT_10X', data=coverage, ax=ax2, cut= 0)
    

    sns.swarmplot(y='PCT_10X', data=coverage, ax=ax2,
                  color = 'black', size=3)


    #Reads Mapeadas X reads unmapped
    #Calcular o numero de redas unmmapped
    reads['unmapped'] = reads['total_reads'] - reads['mepf_reads_aligned']

    #select reads columns
    reads_df = reads[['cod','mepf_reads_aligned','unmapped']]


    # Define a color palette using Seaborn
    colors = sns.color_palette("viridis")
    #create stacked bar chart
    reads_df.set_index('cod').plot(kind='bar', stacked=True, ax=ax3)
    
    #Gênero x Idade


    #Depth X Coverage
    #ax4.scatter(x=coverage['MEAN_COVERAGE'], y=coverage['PCT_10X'])



    # Set ylabels
    ax1.set_ylabel('Profundidade')
    ax2.set_ylabel('Cobertura (%)')
    ax3.set_ylabel('Leituras Geradas')
    ax3.set_xlabel('Amostras')
    #ax3.set_xticklabels(size=6)
    ax3.tick_params(axis='x', labelsize=6)
    ax3.legend(["Leituras mapeadas", "Leituras não-mapeadas"], bbox_to_anchor=(0.5, 1),
               prop = { "size": 6})
    #axs[3].set_ylabel('Reads Mapeadas vs não-mapeadas', fontsize=12)


    # save the plot as SVG file
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, "RNSG_REPORT/Quality_ckeck.png"), format='png', dpi = 300)


#Função para remover os arquivos intermediários
def remover_csv(output_folder):
    # Caminho informado ao executar o script ($1)
    caminho = output_folder

    # Arquivos específicos que queremos remover
    arquivos_para_remover = ['seq_df.csv', 'tabela_resultados.csv', 'tabela_resultados_filt.csv']

    # Lista os arquivos no caminho informado
    arquivos_no_caminho = os.listdir(caminho)

    # Verifica e remove os arquivos específicos
    for arquivo in arquivos_para_remover:
        arquivo_path = os.path.join(caminho, arquivo)
        if arquivo in arquivos_no_caminho:
            os.remove(arquivo_path)


def generate_report_denv(metadata_path, config_path, output_folder):

    # Carregar configurações
    config = load_config(config_path)
    
    mod_pasta(output_folder)
    
    # Processar os arquivos na pasta de entrada
    metadata, sequence, records, reads, serotype, genotype, coverage = input_folder(output_folder, metadata_path)
    df_combine_sequence = planilha_results(metadata, reads, coverage, serotype, genotype, output_folder)

    # Trabalhar com arquivos de resultados
    resultado_file = os.path.join(output_folder, "tabela_resultados.csv")
    if os.path.exists(resultado_file):
        resultado_df = pd.read_csv(resultado_file)
        filter_depth(resultado_df, output_folder)
    else:
        raise FileNotFoundError(f"Arquivo {resultado_file} não encontrado!")

    resultado_filt_file = os.path.join(output_folder, "tabela_resultados_filt.csv")
    if os.path.exists(resultado_filt_file):
        resultado_df_filt = pd.read_csv(resultado_filt_file)
    else:
        raise FileNotFoundError(f"Arquivo {resultado_filt_file} não encontrado!")

    # Gerar arquivos auxiliares
    gerar_arquivo_fasta(records, metadata, resultado_df, output_folder)

    seq_file = os.path.join(output_folder, "seq_df.csv")
    if os.path.exists(seq_file):
        df_combine_sequence = pd.read_csv(seq_file)
        arquivo_epiarbo(config, metadata, df_combine_sequence, output_folder)
    else:
        raise FileNotFoundError(f"Arquivo {seq_file} não encontrado!")

    arbo_virus_name = os.path.join(output_folder, 'RNSG_REPORT/Planilha_de_Resultado.xlsx')
    if os.path.exists(arbo_virus_name):
        covv_virus_name = pd.read_excel(arbo_virus_name)
        planilha_resultado(covv_virus_name, resultado_df, output_folder)
    else:
        raise FileNotFoundError(f"Arquivo {arbo_virus_name} não encontrado!")



    Quality_monitor(coverage, reads, resultado_df, output_folder)

    # Limpar arquivos temporários e monitorar qualidade
    remover_csv(output_folder)

# Mantém a funcionalidade standalone
if __name__ == "__main__":
    output_folder = sys.argv[1]
    metadata_path = sys.argv[2]
    config_path = sys.argv[3]
    generate_report_denv(output_folder, metadata_path, config_path)