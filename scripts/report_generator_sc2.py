#!/usr/bin/env python3

#Carregar todas as lib usadas ao longo de todo script
from locale import locale_encoding_alias
from xml.dom.minidom import TypeInfo
import pandas as pd
import numpy as np
import subprocess
from matplotlib import pyplot as plt
import matplotlib.pyplot as plt
from matplotlib.cm import viridis 
import matplotlib.image as mpimg
import geobr
from Bio import SeqIO
from Bio.SeqIO import FastaIO
import csv
from docxtpl import DocxTemplate
from docxtpl import InlineImage
import docx
from docx import Document
from docx.shared import Inches
from mpl_toolkits.axes_grid1 import make_axes_locatable
import openpyxl
from unidecode import unidecode
import os
import sys
import geopandas as gpd
import seaborn as sns
import colorcet as cc
import shutil
import yaml

## Função que carrega o arquivo yaml e armazena em um dicionario
def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

#faz algumas mudancas em alguns nomes (deixar apenas o codigo de amostra)
def input_folder(folder):

    print("input_folder")

    # Construct the file path for the CSV file
    metadata_path = os.path.join(sys.argv[2], "data.csv")

    # #OBS: VERIFICAR QUAL CAMPO SEPARADOR NO ARQUIVO GAL
    metadata = pd.read_csv(metadata_path, sep =';', encoding='latin-1', on_bad_lines='skip')
    
    # #Substituir espaços por '_' entre palavras da coluns
    metadata.columns = metadata.columns.str.replace(' ', '_')
    
    #Ler arquivo fasta
    #Certificar se o cabelho das sequencias possuem apenas o codigo da amostra.

    # Construct the file path for the CSV file
    sequence_path = os.path.join(folder, "seqbatch.fa")

    sequence = open(sequence_path)

    #converter fasta to dataframe
    ## Load the FASTA file into a list of SeqRecord objects
    records = list(SeqIO.parse(sequence_path, "fasta"))

    #Carregar os seguintes arquivos do ViralFlow

    # Construct the file path for the CSV file
    reads_path = os.path.join(folder, "reads_count.csv")

    reads = pd.read_csv(reads_path, sep =',')

    reads['cod'] = reads['cod'].replace(to_replace ='_.*', value = '', regex = True)

    #short_summary.csv
    #coverage = pd.read_csv('/content/short_summary.csv', sep =',')
    #coverage['cod'] = coverage['cod'].replace(to_replace ='_.*', value = '', regex = True)


    # Construct the file path for the CSV file
    lineage_path = os.path.join(folder, "major_summary.csv")

    lineage = pd.read_csv(lineage_path, sep =',')

    lineage['cod'] = lineage['cod'].replace(to_replace ='_.*', value = '', regex = True)

    #wgs
    # Construct the file path for the CSV file
    coverage_path = os.path.join(folder, 'wgs.csv')

    coverage = pd.read_csv(coverage_path, sep =',')
    coverage['cod'] = coverage['cod'].replace(to_replace ='_.*', value = '', regex = True)

    return metadata, sequence, records, reads, lineage, coverage



#Adiciona a pasta de RNSG_REPORT, a qual serao a adiciona os graficos, planilha, e outros
# Adiciona a pasta de output no caminho informado
def mod_pasta():
    # O caminho informado no argumento $1
    nome_pasta = sys.argv[1]

    # Verifica se a pasta 'RNSG_REPORT' já existe, se sim, a remove
    output_path = os.path.join(nome_pasta, 'RNSG_REPORT')
    
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    
    # Cria a pasta 'RNSG_REPORT' dentro de nome_pasta
    os.mkdir(output_path)
  
 
#Função 'planilha_results' cria um arquivo intermediário 'tabela_resultados.csv' que irá conter informações necessárias para as etapas seguintes, e realiza as seguintes tarefas:
##Altera nome de algumas colunas, 
##junto arquivo GAL aos arquivos saida VF
##O arquivo  csv resultante tem as segunites colunas: 
### Requisição, Código Amostra, CT,
### Tipo Amostra,	Município, Data Coleta, Sexo, Reads, Coverage, Depth of Coverage,
### Lineage
    
def planilha_results(metadata, reads, coverage, lineage):

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
    resultado_df_1 = pd.merge(pd.merge(reads, coverage_update, on='cod'), lineage, on='cod')
    resultado_df_1['cod'] = resultado_df_1['cod'].astype(str)
    metadata_GAL_update.loc[:,'Código_da_Amostra'] = metadata_GAL_update['Código_da_Amostra'].astype(str)
    metadata_GAL_update.loc[:,'Requisição'] = metadata_GAL_update['Requisição'].astype(str)

    resultado_df = pd.merge(resultado_df_1, metadata_GAL_update, left_on="cod", right_on="Código_da_Amostra")

    #print(metadata_GAL_update)

    # Mudar nomes da coluna
    resultado_df = resultado_df.rename(columns={'cod': 'Código Amostra', 'mepf_reads_aligned': 'Reads', 'PCT_10X': 'Coverage', 'MEAN_COVERAGE': 'Depth of Coverage', 'lineage': 'Lineage',
                                   'Requisição': 'Requisição', 'Material_Biológico': 'Tipo Amostra', 'Municipio_do_Solicitante': 'Município','Data_da_Coleta': 'Data Coleta',
                                   'Sexo': 'Sexo'})

    # Mudar ordem das colunas
    cols = ['Código Amostra', 'Requisição', 'CT', 'Tipo Amostra', 'Município', 'Data Coleta', 'Sexo', 'Reads', 'Coverage', 'Depth of Coverage', 'Lineage']
    resultado_df = resultado_df[cols]

    # Convert Column ID name to string
    resultado_df['Coverage'] = resultado_df['Coverage'].astype(float)

    # Converter valor de coverage para porcentagem
    resultado_df['Coverage'] = resultado_df['Coverage'].multiply(100).round(2)

    # Convert Column ID name to string
    resultado_df['Depth of Coverage'] = resultado_df['Depth of Coverage'].astype(float).round(2)

    resultado_df = resultado_df.set_index('Requisição')

    resultado_df.to_csv(os.path.join(sys.argv[1], "tabela_resultados.csv"))

    return resultado_df


#A função 'planilha_resultado' cria um arquivo chamado 'Planilha_de_Resultado.xlsx' que contem os resultados em formato de planilha xlsx.
##Contem as seguintes colunas: Barcode	N Barcode, Gal Sequenciamento, Código Amostra, Nome da Sequencia, CT, Tipo Amostra, Município,
    #Data Coleta, Sexo, Reads, Cobertura, Profundidade Média, Linhagem

def planilha_resultado(covv_virus_name, resultado_df):

    print("planilha_resultado")

    result_table = covv_virus_name[['id','covv_virus_name']]

    #Merge df
    result_table = pd.merge(result_table, resultado_df, left_on = 'id', right_on = 'Código Amostra', how='right')

    #drop team_name column
    result_table.drop('Código Amostra', axis=1, inplace=True)

    #Change order header
    result_table = result_table[[ 'Requisição','id','covv_virus_name', 'CT', 'Tipo Amostra', 'Município', 'Data Coleta', 'Sexo', 'Reads', 'Coverage', 'Depth of Coverage', 'Lineage']]

    # add an empty column named 'Barcode' at index 0
    result_table.insert(0, 'Barcode',None)

    # add an empty column named 'N Barcode' at index 1
    result_table.insert(1, 'N Barcode',None)

    #Mudar nomes da coluna
    result_table = result_table.rename(columns={'Requisição':'Gal Sequenciamento','id': 'Código Amostra', 'covv_virus_name': 'Nome da Sequencia', 'Coverage': 'Cobertura', 
                                                'Depth of Coverage': 'Profundidade Média'})

    # Salve o DataFrame resultante em um arquivo Excel
    result_table.to_excel(os.path.join(sys.argv[1], 'RNSG_REPORT/Planilha_de_Resultado.xlsx'), index=False)



#A função 'filter_depth' gera um arquivo intermediário 'tabela_resultados_filt.csv' com informações apenas das amostras com cobertua > 80%
def filter_depth(resultado_df):

    resultado_df_filt = resultado_df.loc[resultado_df['Coverage'] >= 80]

    resultado_df_filt.to_csv(os.path.join(sys.argv[1], "tabela_resultados_filt.csv"))

    return resultado_df_filt


#Função para criar um gráfico de barras com o numero total de cada linhagem identificada
def freq_graph(resultado_df_filt):

    print("freq_graph")

    df_combine = resultado_df_filt

    df_combine['Lineage'].value_counts().plot(kind="bar")

    #plt.title("Mince Pie Consumption Study Results")
    plt.xlabel("Linhagens encontradas")
    plt.ylabel("Números de genomas")

    #Export figure para pasta
    plt.tight_layout()
    plt.savefig(os.path.join(sys.argv[1], "RNSG_REPORT/Grafico_frequencia_linhagem.png"), format='png', dpi=200)


#Função para criar um grafico de barras agrupados indicando a proporção de cada linhagem por mês
def grafico_bar_agrupado(resultado_df_filt):

    print("grafico_bar_agrupado")

    df_combine = resultado_df_filt

    df_combine.rename(columns = {'Data Coleta':'Data'}, inplace = True)

    #convert colum to date format
    df_combine['Data'] = pd.to_datetime(df_combine['Data'], format="%d-%m-%Y")

    #Ordernar as linhas pela ordem da data
    df_combine = df_combine.sort_values(by='Data')

    #Converter a data para o padrão mes/ano
    df_combine['Data'] = pd.to_datetime(df_combine['Data']).dt.strftime('%m-%Y')

    #Create a list of timeserie orderd
    df_combine_list = df_combine['Data'].unique()

    series = pd.Series(df_combine_list)
    lst = series.to_list()

    # Create cross-tabulation tables
    cross_tab = pd.crosstab(df_combine.Data, df_combine.Lineage).reindex(lst)
    cross_tab_prop = pd.crosstab(df_combine.Data, df_combine.Lineage, normalize="index").reindex(lst)

    # Create subplots
    fig, axs = plt.subplots(2, 1)
    axs = axs.flatten()

    # Define a color palette using Seaborn
    colors = sns.color_palette("tab20c", 20)

    # Create stacked bar plots
    cross_tab.plot(kind='bar', stacked=True, ax=axs[0], color = colors)
    cross_tab_prop.plot(kind='bar', stacked=True, ax=axs[1], color = colors)

    # Set ylabels
    axs[0].set_ylabel('Genomas (n)', fontsize=14)
    axs[1].set_ylabel('Genomas (%)', fontsize=14)

    # Set x-axis font size
    plt.xticks(fontsize=10)

    # Set y-axis font size
    axs[0].tick_params(axis='y', labelsize=10)
    axs[1].tick_params(axis='y', labelsize=10)

    # Set xlabels
    axs[0].set(xlabel=None)
    axs[0].get_xaxis().set_visible(False)
    axs[1].set_xlabel('Data de coleta (Mês-Ano)', fontsize=14)

    # Set legend location
    axs[0].get_legend().remove()
    #axs[1].legend(bbox_to_anchor=(1, 1), fontsize="10")
    axs[1].legend(bbox_to_anchor=(1, 1))

    # Export figure to the specified output file
    plt.tight_layout()
    plt.savefig(os.path.join(sys.argv[1],"RNSG_REPORT/Freq_lineage.png"), format='png', dpi=200)
    
    pass


#Função para cria um mapa de calor com o numero de genomas sequenciados (>80% cobertura) por município SOLICITANTE
def mapa(metadata, resultado_df_filt):
    
    print("mapa")

    # Sigla do LACEN
    SIGLA_LACEN = metadata[['Estado_do_Solicitante']].iloc[1,:].to_string(header=False, index=False)

    # Lista de Municipios do estado
    state = geobr.read_municipality(code_muni=SIGLA_LACEN, year=2019)

    # Remove accents from words in the 'name_muni' column
    state['name_muni'] = state['name_muni'].apply(unidecode)

    counts = resultado_df_filt['Município'].value_counts()

    # create new dataframe with row names and counts
    municipio_genoma = counts.reset_index()
    municipio_genoma.columns = ['Município', 'Genomas']

    def capitalize_two_words(name):
        split_name = name.split(' ')
        capitalized_words = [word.capitalize() for word in split_name]
        return ' '.join(capitalized_words)

    municipio_genoma['Município'] = municipio_genoma['Município'].apply(capitalize_two_words)

    municipio_genoma_state = state.merge(municipio_genoma, right_on="Município", left_on="name_muni", how='outer')

    municipio_genoma_state['Genomas'] = municipio_genoma_state['Genomas'].fillna(0)

    fig, ax = plt.subplots(figsize=(5, 5), dpi=200)

    ax.axis("off")

    divider = make_axes_locatable(ax)

    # create `cax` for the colorbar
    cax = divider.append_axes("bottom", size="3%", pad=0.01, alpha=0.1)

    # Plots 'No Data' layer
    municipio_genoma_state.plot(ax=ax, color='#DEDEDE', edgecolor='#ECECEC', label='No Data',
                                legend_kwds={"shrink": 0.1})

    # Plots data layer
    municipio_genoma_state.dropna().plot(ax=ax, column='Genomas', cmap='viridis', legend=True, cax=cax, alpha=0.6,
                                         legend_kwds={"label": "Número de Genomas", "orientation": "horizontal",
                                                      "shrink": 0.3})

    # Plotar nome dos municipios
    municipio_genoma_state.dropna().apply(lambda x: ax.annotate(text=x.name_muni, xy=x.geometry.centroid.coords[0],
                                                               ha='left', color="black"), axis=1)

    # Export figure para pasta
    plt.tight_layout()
    plt.savefig(os.path.join(sys.argv[1], "RNSG_REPORT/Mapa_genomas.png"), format='png', dpi=200)

    pass

    #plt.show()


#Função para gerar o arquivo fasta para ser submetido ao Gisaid
def gerar_arquivo_fasta(metadata, resultado_df):

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

    # Extract the sequence and ID from each record and store in a dictionary
    data = {'id': [r.id for r in records], 'sequence': [str(r.seq) for r in records]}

    # Convert the dictionary to a pandas DataFrame
    df_sequence = pd.DataFrame(data)

    #Remover campos apos o ID
    df_sequence = df_sequence[['id','sequence']].replace(to_replace ='_.*', value = '', regex = True)

    ##Combinte the both subset based on ID sequence name
    df_combine_sequence = pd.merge(df_sequence, metadata, left_on="id", right_on="Código_da_Amostra")

    #Controle de qualidade (cobertura)
    resultado_df = resultado_df.loc[resultado_df['Coverage'] >= 80]

    resultado_df = resultado_df.astype(str)

    df_combine_sequence = pd.merge(df_combine_sequence, resultado_df, left_on="id", right_on="Código Amostra")

    #Extract yerar collect date
    df_combine_sequence['Data_da_Coleta'] = pd.to_datetime(df_combine_sequence['Data_da_Coleta'], format="%d-%m-%Y")
    df_combine_sequence['ANO_SEMANA_EPIDEMIOLOGICA'] = df_combine_sequence['Data_da_Coleta'].dt.strftime('%Y')
        
    #Cria um arquivo chamado 'seq_df.csv' para ser usado na geração do fasta
    df_combine_sequence.to_csv(os.path.join(sys.argv[1], 'seq_df.csv'), sep = ',')

    # Convert DataFrame df_combine_sequence to a fasta file with the required header format
    with open(os.path.join(sys.argv[1], 'seq_df.csv')) as csvfile, open(os.path.join(sys.argv[1],'RNSG_REPORT/LACEN_seq.fasta'), 'w') as outfile:
        reader = csv.reader(csvfile, delimiter=',')
        first_line = csvfile.readline()
        for row in reader:
            seq_id = f">hCoV-19/Brazil/{row[12]}-LACEN{row[12]}-{row[1]}/{row[119]}"
            seq = row[2]
            outfile.write(f"{seq_id}\n{seq}\n")
    
    return df_combine_sequence


#Função para gerar o arquivo EpiCov para ser submetido ao Gisaid
def arquivo_epicov(metadata, df_combine_sequence):
    
    print("arquivo_epicov")
    
    #Columnas que serão inseridas manualmente
    #Nickname do submitter no gisaid
    submitter = config['user_info']['submitter']

    #Lista de autores CGLAB + LACEN
    covv_authors = config['user_info']['authors']

    covv_orig_lab = " "

    covv_orig_lab_addr = " "

    covv_subm_lab = config['user_info']['subm_lab']

    covv_subm_lab_addr = config['user_info']['subm_lab_addr']


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

    #Insert covv_patient_age column
    ##Extrair campos de intersse
    covv_patient_age = df_combine_sequence[['id','Data_de_Nascimento','Data_da_Coleta']]

    ##Remover campo extrar (hora)
    covv_patient_age = covv_patient_age.copy()  # Garante que estamos trabalhando em uma cópia segura
    covv_patient_age['Data_de_Nascimento'] = covv_patient_age['Data_de_Nascimento'].replace(to_replace =' .*', value = '', regex = True)

    ##Conveter colunas para Data
    covv_patient_age['Data_de_Nascimento'] = pd.to_datetime(covv_patient_age['Data_de_Nascimento'], errors='coerce', dayfirst=True)
    covv_patient_age['Data_da_Coleta'] = pd.to_datetime(covv_patient_age['Data_da_Coleta'], errors='coerce')

     # Garante que estamos trabalhando em uma cópia segura
    covv_patient_age = covv_patient_age.copy()  
    # Certifique-se de que as colunas estão no formato datetime
    covv_patient_age['Data_da_Coleta'] = pd.to_datetime(covv_patient_age['Data_da_Coleta'], errors='coerce')
    covv_patient_age['Data_de_Nascimento'] = pd.to_datetime(covv_patient_age['Data_de_Nascimento'], errors='coerce')
    #Subtrair a data da coleta e data de nascimento
    covv_patient_age.loc[:, 'covv_patient_age'] = (covv_patient_age['Data_da_Coleta'] - covv_patient_age['Data_de_Nascimento'])
    covv_patient_age = covv_patient_age[['id','covv_patient_age']]


    #Virus name
    covv_virus_name = df_combine_sequence[['Estado_do_Solicitante','id','ANO_SEMANA_EPIDEMIOLOGICA']].astype(str)
    covv_virus_name['covv_virus_name'] = "hCoV-19/Brazil/" + covv_virus_name['Estado_do_Solicitante'] + "-LACEN" + covv_virus_name['Estado_do_Solicitante'] + "-" + covv_virus_name['id'] + "/" + covv_virus_name['ANO_SEMANA_EPIDEMIOLOGICA']
    covv_virus_name = covv_virus_name[['id','covv_virus_name']]


    #Insert submitter column
    covv_virus_name.insert(0, 'submitter','')
    covv_virus_name.loc[:, 'submitter'] = submitter


    #Insert fn (fasta file name) column
    covv_virus_name.insert(1, 'fn', '')
    #covv_virus_name = covv_virus_name.copy 
    covv_virus_name.loc[:, 'fn'] = 'LACEN_seq.fasta'


    #Insert covv_type column
    covv_virus_name.insert(4, 'covv_type', '')
    covv_virus_name.loc[:, 'covv_type'] = 'betacoronavirus'

    #Insert covv_passage column
    covv_virus_name.insert(5, 'covv_passage', '')

    covv_virus_name.loc[:, 'covv_passage'] = 'Original'

    covv_virus_name.to_excel(os.path.join(sys.argv[1],'RNSG_REPORT/Planilha_de_Resultado.xlsx'), index=False)

    #Collection date
    covv_collection_date = df_combine_sequence[['id','Data_da_Coleta']]
    #covv_collection_date['Data_da_Coleta'] = pd.to_datetime(covv_collection_date['Data_da_Coleta'], format="mixed")
    covv_collection_date.loc[:,'Data_da_Coleta'] = pd.to_datetime(covv_collection_date['Data_da_Coleta']).dt.strftime('%Y-%m-%d')
    covv_collection_date = covv_collection_date.rename(columns={'Data_da_Coleta': 'covv_collection_date'})

    covv_collection_date = covv_collection_date.astype(str)

    gisaid_temp = pd.merge(covv_virus_name,covv_collection_date,on='id')

   #Location
    ##Continent / Country / State / Municipality
    covv_location = df_combine_sequence[['id','Estado_do_Solicitante','Municipio_do_Solicitante']]

    ##Mudar as linhas da SIGLA para NOME
    covv_location.loc[:,'Estado_do_Solicitante'] = covv_location.loc[:,'Estado_do_Solicitante'].replace(states)

    #Deixar apenas primeira letra maiuscula, pois no GAL geralmente vem tudo maiúsculo, e remove acentos (Municío solicitante e estados)
    covv_location.loc[:,'Municipio_do_Solicitante'] = covv_location.loc[:,'Municipio_do_Solicitante'].apply(str.capitalize).apply(unidecode)
    covv_location.loc[:,'Estado_do_Solicitante'] = covv_location.loc[:,'Estado_do_Solicitante'].apply(str.capitalize).apply(unidecode)

    #Cria a coluna de location no EpiCov
    covv_location = covv_location.copy()  # Garante que estamos trabalhando em uma cópia segura
    covv_location.loc[:,'covv_location'] = "South America / Brazil / " + covv_location.loc[:,'Estado_do_Solicitante'] + " / " + covv_location.loc[:,'Municipio_do_Solicitante']
    covv_location = covv_location[['id','covv_location']]

    covv_location = covv_location.astype(str)

    gisaid_temp = pd.merge(gisaid_temp,covv_location,on='id')

    #Insert covv_add_location column
    gisaid_temp.insert(8, 'covv_add_location', '')


    #Insert covv_host column
    gisaid_temp.insert(9, 'covv_host', '')
    gisaid_temp.loc[:, 'covv_host'] = 'Human'



    #Insert covv_add_host_info column
    gisaid_temp.insert(10, 'covv_add_host_info', '')


    #Insert covv_sampling_strategy column
    gisaid_temp.insert(11, 'covv_sampling_strategy', '')


    #Gender (Male / Female)
    covv_gender = df_combine_sequence[['id','Sexo_x']]

    gender = {
        'Masculino':'Male',
        'Feminino':'Female'
    }



    covv_gender.loc[:,'Sexo_x'] = covv_gender.loc[:,'Sexo_x'].replace(gender)

    covv_gender = covv_gender.rename(columns={'Sexo_x': 'covv_gender'})

    covv_gender = covv_gender.astype(str)

    gisaid_temp = pd.merge(gisaid_temp,covv_gender,on='id')


    #Insert covv_patient_age column
    ##Extrair campos de intersse
    covv_patient_age = df_combine_sequence[['id','Data_de_Nascimento','Data_da_Coleta']]

    ##Remover campo extrar (hora)
    covv_patient_age.loc[:,'Data_de_Nascimento'] = covv_patient_age.loc[:,'Data_de_Nascimento'].replace(to_replace =' .*', value = '', regex = True)

    ##Conveter colunas para Data
    covv_patient_age.loc[:,'Data_de_Nascimento'] = pd.to_datetime(covv_patient_age['Data_de_Nascimento'], errors='coerce', dayfirst= True)
    covv_patient_age.loc[:,'Data_da_Coleta'] = pd.to_datetime(covv_patient_age['Data_da_Coleta'], errors='coerce')

    # Garante que estamos trabalhando em uma cópia segura
    covv_patient_age = covv_patient_age.copy() 
    # Certifique-se de que as colunas estão no formato datetime
    covv_patient_age['Data_da_Coleta'] = pd.to_datetime(covv_patient_age['Data_da_Coleta'], errors='coerce')
    covv_patient_age['Data_de_Nascimento'] = pd.to_datetime(covv_patient_age['Data_de_Nascimento'], errors='coerce')
    ##Subtrair a data da coleta e data de nascimento (em dias), converter para ano (dividindo por 365.25), e aredendar (remove decimal)
    covv_patient_age['covv_patient_age'] = ((covv_patient_age['Data_da_Coleta'] - covv_patient_age['Data_de_Nascimento']).dt.days / 365.25).round().astype(int)
    covv_patient_age = covv_patient_age[['id','covv_patient_age']]

    covv_patient_age = covv_patient_age.astype(str)

    gisaid_temp = pd.merge(gisaid_temp,covv_patient_age,on='id')


    #Insert covv_patient_status column
    gisaid_temp.insert(14, 'covv_patient_status','')
    gisaid_temp.loc[:, 'covv_patient_status'] = 'Unknown'


    #Insert covv_specimen column
    gisaid_temp.insert(15, 'covv_specimen','')


    #Insert covv_outbreak column
    gisaid_temp.insert(16, 'covv_outbreak','')


    #Insert covv_last_vaccinated column
    gisaid_temp.insert(17, 'covv_last_vaccinated','')


    #Insert covv_treatment column
    gisaid_temp.insert(18, 'covv_treatment','')

    #Insert covv_seq_technology column
    gisaid_temp.insert(19, 'covv_seq_technology','')
    gisaid_temp.loc[:, 'covv_seq_technology'] = 'Illumina MiSeq'

    #Insert covv_assembly_method column
    gisaid_temp.insert(20, 'covv_assembly_method','')
    gisaid_temp.loc[:, 'covv_assembly_method'] = 'Viralflow'


    #Insert covv_coverage column
    ##Extrair campos de intersse
    covv_coverage = df_combine_sequence[['id','Depth of Coverage']]

    covv_coverage = covv_coverage.rename(columns={'Depth of Coverage': 'covv_coverage'})

    covv_coverage = covv_coverage.astype(str)

    gisaid_temp = pd.merge(gisaid_temp,covv_coverage,on='id')


    #Insert covv_orig_lab column
    gisaid_temp.insert(22, 'covv_orig_lab','')
    gisaid_temp.loc[:, 'covv_orig_lab'] = covv_orig_lab


    #Insert covv_orig_lab_addr column
    gisaid_temp.insert(23, 'covv_orig_lab_addr','')
    gisaid_temp.loc[:, 'covv_orig_lab_addr'] = covv_orig_lab_addr


    #Insert covv_provider_sample_id column
    gisaid_temp.insert(24, 'covv_provider_sample_id','')


    #Insert covv_subm_lab column
    gisaid_temp.insert(25, 'covv_subm_lab','')
    gisaid_temp.loc[:, 'covv_subm_lab'] = covv_subm_lab


    #Insert covv_subm_lab_addr column
    gisaid_temp.insert(26, 'covv_subm_lab_addr','')
    gisaid_temp.loc[:, 'covv_subm_lab_addr'] = covv_subm_lab_addr


    #Insert covv_subm_sample_id column
    gisaid_temp.insert(27, 'covv_subm_sample_id','')


    #Insert covv_subm_sample_id column
    gisaid_temp.insert(28, 'covv_consortium','')
    gisaid_temp.loc[:, 'covv_consortium'] = 'Rede Nacional de Sequenciamento Genetico'


    #Insert covv_authors column
    gisaid_temp.insert(29, 'covv_authors','')
    gisaid_temp.loc[:, 'covv_authors'] = covv_authors

    df_insumos = gisaid_temp

    gisaid_temp = gisaid_temp.drop('id', axis=1)

    # # Define column names
    columns = ['Submitter', 'FASTA filename', 'Virus name', 'Type', 'Passage details/history', 'Collection date',
            'Location', 'Additional location information', 'Host', 'Additional host information', 'Sampling Strategy',
            'Gender', 'Patient age', 'Patient status', 'Specimen source', 'Outbreak', 'Last vaccinated', 'Treatment',
            'Sequencing technology', 'Assembly method', 'Coverage', 'Originating lab', 'Address',
            'Sample ID given by originating laboratory', 'Submitting lab', 'Address',
            'Sample ID given by the submitting laboratory', 'Sequencing consortium', 'Authors']


    # Crie um novo DataFrame com as colunas desejadas
    new_row = pd.DataFrame([columns], columns=gisaid_temp.columns)

    # Concatene o novo DataFrame com o DataFrame original e redefina o índice
    gisaid_temp = pd.concat([new_row, gisaid_temp], ignore_index=True)

    gisaid_temp = gisaid_temp.set_index('submitter')

    gisaid_temp.to_csv(os.path.join(sys.argv[1], 'RNSG_REPORT/EpiCov.csv'))

    pass


#Função para criar um grafico com métricas gerais da corrida, para aferição de controle de qualidade
def Quality_monitor(folder):

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
    plt.savefig(os.path.join(sys.argv[1], "RNSG_REPORT/Quality_ckeck.png"), format='png', dpi = 300)


#Função para remover os arquivos intermediários
def remover_csv():
    # Caminho informado ao executar o script ($1)
    caminho = sys.argv[1]

    # Arquivos específicos que queremos remover
    arquivos_para_remover = ['seq_df.csv', 'tabela_resultados.csv', 'tabela_resultados_filt.csv']

    # Lista os arquivos no caminho informado
    arquivos_no_caminho = os.listdir(caminho)

    # Verifica e remove os arquivos específicos
    for arquivo in arquivos_para_remover:
        arquivo_path = os.path.join(caminho, arquivo)
        if arquivo in arquivos_no_caminho:
            os.remove(arquivo_path)



if __name__ == "__main__":
    #if len(sys.argv) != 2:
     #   print("Usage: python3 script.py <config_path>")
      #  sys.exit(1)

    mod_pasta()

    # Caminho do arquivo de configuração (YAML)
    config_path = sys.argv[3]
    
    # Carregar configurações do YAML
    config = load_config(config_path)
    
    metadata, sequence, records, reads, lineage, coverage = input_folder(sys.argv[1])
    
    df_combine_sequence = planilha_results(metadata, reads, coverage, lineage)

    resultado_df = pd.read_csv(os.path.join(sys.argv[1], "tabela_resultados.csv"))
    
    filter_depth(resultado_df)

    resultado_df_filt = pd.read_csv(os.path.join(sys.argv[1], "tabela_resultados_filt.csv"))

    freq_graph(resultado_df_filt)

    grafico_bar_agrupado(resultado_df_filt)

    mapa(metadata, resultado_df_filt)

  #  gerar_relatorio(input_folder_path, metadata, resultado_df)

    gerar_arquivo_fasta(metadata, resultado_df)

    df_combine_sequence = pd.read_csv(os.path.join(sys.argv[1], "seq_df.csv"))
    arquivo_epicov(metadata, df_combine_sequence)

    covv_virus_name = pd.read_excel(os.path.join(sys.argv[1], 'RNSG_REPORT/Planilha_de_Resultado.xlsx'))

    planilha_resultado(covv_virus_name, resultado_df)

    remover_csv()

    Quality_monitor(resultado_df)


