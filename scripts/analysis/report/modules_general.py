#!/usr/bin/env python3

#Carregar todas as lib usadas ao longo de todo script
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.pyplot as plt
from Bio import SeqIO
import csv
import re
import os
import shutil
import yaml
from unidecode import unidecode
import seaborn as sns

colunas_mapeadas = {
    "Código_da_Amostra": [r"C[oó]digo\s*(?:da\s*)?Amostra"],
    "Municipio_do_Solicitante": [r"Munic[ií]pio\s*(?:do\s*)?(?:Requisitante|Solicitante)"],
    "Estado_do_Solicitante": [r"Estado\s*(?:do\s*)?(?:Requisitante|Solicitante)"],
    "CNES_Laboratório_responsável": [r"CNES\s*(?:do\s*)?Laboratório\s*[Rr]espons[aá]vel"]
}

# Função para padronizar os nomes das colunas usando regex
def padronizar_colunas(df, mapeamento):
    novo_nomes = {}
    for padrao_padronizado, regex_variacoes in mapeamento.items():
        for regex in regex_variacoes:
            for coluna in df.columns:
                if pd.Series(coluna).str.contains(regex, regex=True, case=False).any():
                    novo_nomes[coluna] = padrao_padronizado  # Mapeia para o nome padronizado
    df.rename(columns=novo_nomes, inplace=True)


## Função que carrega o arquivo yaml e armazena em um dicionario
def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


#faz algumas mudancas em alguns nomes (deixar apenas o codigo de amostra)
def input_folder(output_folder, metadata_path):


    # Detecta o delimitador do arquivo
    with open(metadata_path, 'r', encoding='latin-1') as file:
        sample = file.read(1024)  # Lê uma amostra do arquivo
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter  # Detecta o delimitador


    # Carrega o arquivo usando o delimitador detectado
    metadata = pd.read_csv(metadata_path, sep=delimiter, encoding='latin-1', on_bad_lines='skip')

    # Padroniza os nomes das colunas
    padronizar_colunas(metadata, colunas_mapeadas)

    # Substitui espaços por '_' nos nomes das colunas
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

    #wgs
    # Construct the file path for the CSV file
    coverage_path = os.path.join(output_folder, 'short_summary.csv')

    coverage = pd.read_csv(coverage_path, sep =',')

    # Remove linhas onde a coluna "taxon" contém "_minor"
    if 'taxon' in coverage.columns:
        coverage = coverage[~coverage['taxon'].str.contains('_minor', na=False)]
    coverage['cod'] = coverage['cod'].replace(to_replace ='_.*', value = '', regex = True)

    # Carregar errors_detected.csv somente se não estiver vazio
    errors_path = os.path.join(output_folder, 'errors_detected.csv')
    # Verifica se o arquivo existe e não está vazio
    if os.path.isfile(errors_path) and os.path.getsize(errors_path) > 0:
        try:
            errors = pd.read_csv(errors_path, sep=',')
            errors['cod'] = errors['cod'].replace(to_replace='_.*', value='', regex=True)
        except pd.errors.EmptyDataError:
            errors = pd.DataFrame(columns=['cod'])  # Cria DataFrame vazio com coluna esperada
    else:
        errors = pd.DataFrame(columns=['cod'])  # Cria DataFrame vazio se arquivo não existe ou está vazio

    return metadata, sequence, records, reads, coverage, errors


def data_processing(output_folder):
    #Function to get sample ID

    # Construct the file path for the CSV file
    reads_path = os.path.join(output_folder, "reads_count.csv")

    reads = pd.read_csv(reads_path, sep =',')

    reads['cod'] = reads['cod'].replace(to_replace ='_.*', value = '', regex = True)

    #wgs
    # Construct the file path for the CSV file
    coverage_path = os.path.join(output_folder, 'short_summary.csv')

    coverage = pd.read_csv(coverage_path, sep =',')
    # Remove linhas onde a coluna "taxon" contém "_minor"
    coverage = coverage[~coverage['taxon'].str.contains('_minor', na=False)]
    coverage['cod'] = coverage['cod'].replace(to_replace ='_.*', value = '', regex = True)

    return reads, coverage


def process_and_combine_data(metadata, reads, coverage, errors, output_folder, rename_columns, lineage = None):
    """
    Combina os dados de diferentes fontes (metadata, reads, coverage e lineage) e processa os resultados
    para gerar um arquivo consolidado em formato CSV.

    Parâmetros:
    - metadata (DataFrame): Dados de metadados do GAL.
    - reads (DataFrame): Dados de leituras de sequência.
    - coverage (DataFrame): Dados de cobertura de sequência.
    - lineage (DataFrame): Dados de linhagens ou sorotipos.
    - output_folder (str): Caminho para salvar o arquivo de resultados.
    - rename_columns (dict): Dicionário de mapeamento de nomes de colunas para renomeação.
    - result_cols (list): Lista com a ordem final das colunas do DataFrame.
    """

    # Remover redundância no nome do tipo de amostra
    metadata['Material_Biológico'] = metadata['Material_Biológico'].replace(to_replace=' .*', value='', regex=True)

    # Formatar as datas corretamente
    metadata['Data_da_Coleta'] = pd.to_datetime(metadata['Data_da_Coleta'], dayfirst=True, errors='coerce').dt.strftime('%d-%m-%Y')

    # Selecionar e renomear colunas do metadata
    metadata = metadata[['Código_da_Amostra', 'Requisição', 'Material_Biológico',
                         'Municipio_do_Solicitante', "Idade", "Tipo_Idade",'Estado_do_Solicitante', 'Data_da_Coleta', 'Sexo']]

    # Atualizar dados de coverage
    coverage_update = coverage[['cod', 'coverage_breadth', 'mean_depth_coverage']]

    #Atualizar erros
    errors = errors[['cod']]

    # Juntar dados: reads, coverage e lineage se lineage foi fornecido, adicionar na junção
    if lineage is not None:
        combined_data = pd.merge(reads, coverage_update, on='cod', how='outer')
        combined_data = pd.merge(combined_data, lineage, on='cod', how='outer')
        combined_data = pd.merge(combined_data, errors, on='cod', how='outer') 
    elif lineage is None:
        combined_data = pd.merge(reads, coverage_update, on='cod', how='outer')
        combined_data = pd.merge(combined_data, errors, on='cod', how='outer')

    combined_data['cod'] = combined_data['cod'].astype(str)
    # Garantir que não há warnings
    metadata = metadata.copy()  # Faça isso apenas se necessário
    metadata.loc[:, 'Código_da_Amostra'] = metadata['Código_da_Amostra'].astype(str)
    metadata['Código_da_Amostra'] = metadata['Código_da_Amostra'].astype(str)
    
    metadata.loc[:, 'Requisição'] = metadata['Requisição'].astype(str)
    metadata['Requisição'] = metadata['Requisição'].astype(str)

    # Juntar com metadata
    final_df = pd.merge(combined_data, metadata, left_on="cod", right_on="Código_da_Amostra")

    # Renomear colunas
    final_df.rename(columns=rename_columns, inplace=True)
 
    # Reordenar colunas
    #final_df = final_df[result_cols]

    # Ajustar valores de Coverage para porcentagem e arredondar Depth of Coverage
    final_df['Coverage'] = final_df['Coverage'].astype(float).multiply(100).round(2)
    final_df['Depth of Coverage'] = final_df['Depth of Coverage'].astype(float).round(2)

    # Configurar a coluna de índice
    final_df.set_index('Requisição', inplace=True)

    # Salvar arquivo final
    final_df.to_csv(os.path.join(output_folder, "tabela_resultados.csv"))

    return final_df


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


#Função para criar um grafico com métricas gerais da corrida, para aferição de controle de qualidade
def Quality_monitor(coverage, reads, output_folder):

    #print("QualityCheck")

    coverage['coverage_breadth'] = coverage['coverage_breadth']*100

    #Criar os subplots e os seus respec. eixos x
    fig = plt.figure()
    #axs = axs.flatten()

    gs = fig.add_gridspec(2,2)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])
    #ax4 = fig.add_subplot(gs[2, :])


    # Depth of Coverage (X)
    sns.violinplot(y='mean_depth_coverage', data=coverage, 
               inner="points", ax=ax1, cut= 0)
    
    sns.swarmplot(y='mean_depth_coverage', data=coverage, ax=ax1,
                  color = 'black', size=3)

    # Pinte a linha com 'CN' de outra cor (neste caso, vermelho)
    linha_cn = coverage[coverage['cod'] == 'CN']

    if not linha_cn.empty:
            ax1.scatter(x=0, y=linha_cn['coverage_breadth'], color='red', 
                        marker='o', label='CN', s=20)

            ax2.scatter(x=0, y=linha_cn['mean_depth_coverage'], color='red', 
                        marker='o', label='CN', s=20)

    # Coverage (%)
    sns.violinplot(y='coverage_breadth', data=coverage, ax=ax2, cut= 0)
    

    sns.swarmplot(y='coverage_breadth', data=coverage, ax=ax2,
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
    plt.savefig(os.path.join(output_folder, "RNSG_REPORT/Quality_check.png"), format='png', dpi = 300)


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