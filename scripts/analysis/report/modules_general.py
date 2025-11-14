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
import plotly.express as px
import plotly.graph_objects as go

'''
Este script contém diversas funções, afim de otimizar a manutenção e refatoração do código:
1) padronizar_colunas: Padroniza o nome das colunas que tem variações nos banco de dados regionais
2) load_config: Lê um arquivo de configuração .yaml (submission_info.yaml) e retorna seu conteúdo como um dicionário Python.
3) input_folder: Carrega e prepara os principais arquivos de entrada (metadados, sequencia, reads_count,
                short_summary, arquivos erros)
4) data_processing: Carrega e processa os arquivos reads_count.csv e short_summary.csv
5) process_and_combine_data: Combina os diferentes conjuntos de dados (metadata, reads, coverage, errors e opcionalmente lineage) 
                em uma única tabela consolidada
6) mod_pasta: Cria (ou recria) a subpasta RNSG_REPORT dentro da pasta de saída.
7) Quality_monitor: Gera um relatório gráfico de controle de qualidade das amostras
8) remover_csv: Remove arquivos intermediários gerados durante a execução do script
'''

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


def process_and_combine_data(metadata, reads, coverage, errors, output_folder, rename_columns,
                             lineage=None, pangolin_version=None, serotype=None):
    """
    Combina os dados de diferentes fontes (metadata, reads, coverage e lineage/pangolin_version)
    e processa os resultados para gerar um arquivo consolidado em formato CSV.
    """

    # --- Limpeza e formatação do metadata ---
    metadata['Material_Biológico'] = metadata['Material_Biológico'].replace(to_replace=' .*', value='', regex=True)
    metadata['Data_da_Coleta'] = pd.to_datetime(metadata['Data_da_Coleta'], dayfirst=True, errors='coerce').dt.strftime('%d-%m-%Y')

    metadata = metadata[['Código_da_Amostra', 'Requisição', 'Material_Biológico',
                         'Municipio_do_Solicitante', "Idade", "Tipo_Idade",
                         'Estado_do_Solicitante', 'Data_da_Coleta', 'Sexo']]

    coverage_update = coverage[['cod', 'coverage_breadth', 'mean_depth_coverage']]
    errors = errors[['cod']]

    # --- Criação base do combined_data ---
    combined_data = pd.merge(reads, coverage_update, on='cod', how='outer')

    # Adicionar lineage se fornecido
    if lineage is not None:
        lineage_cols = [c for c in lineage.columns if c in ['cod', 'lineage']]
        combined_data = pd.merge(combined_data, lineage[lineage_cols], on='cod', how='outer')


    # Adicionar pangolin_version se fornecido
    if pangolin_version is not None:
        pangolin_cols = ['cod', 'pangolin_version', 'lineage', 'scorpio_call']
        pangolin_version = pangolin_version[pangolin_cols].copy()

        # Se houver colunas duplicadas, renomeie-as
        pangolin_version = pangolin_version.rename(columns={
            'lineage': 'lineage_pango',
            'scorpio_call': 'scorpio_call_pango'
        })

        combined_data = pd.merge(combined_data, pangolin_version, on='cod', how='outer')
        # Sempre adicionar erros
        combined_data = pd.merge(combined_data, errors, on='cod', how='outer')

    if serotype is not None:
        combined_data = pd.merge(combined_data, serotype, on='cod', how='outer')

    combined_data = pd.merge(combined_data, errors, on='cod', how='outer')

    # --- Garantir tipos corretos para merge ---
    combined_data['cod'] = combined_data['cod'].astype(str)
    metadata = metadata.copy()
    metadata['Código_da_Amostra'] = metadata['Código_da_Amostra'].astype(str)
    metadata['Requisição'] = metadata['Requisição'].astype(str)

    # --- Merge final com metadados ---
    final_df = pd.merge(combined_data, metadata, left_on="cod", right_on="Código_da_Amostra")

    # --- Renomear e formatar ---
    final_df.rename(columns=rename_columns, inplace=True)

    # Ajustar valores de cobertura
    if 'Coverage' in final_df.columns:
        final_df['Coverage'] = final_df['Coverage'].astype(float).multiply(100).round(2)
    if 'Depth of Coverage' in final_df.columns:
        final_df['Depth of Coverage'] = final_df['Depth of Coverage'].astype(float).round(2)

    # Definir índice
    final_df.set_index('Requisição', inplace=True)

    # --- Salvar resultado ---
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

def Quality_monitor_interactive(coverage, reads, output_folder, 
                                lineage_data=None, 
                                custom_fig=None):
    """
    Gera um relatório HTML interativo de controle de qualidade usando Plotly.

    Não lê mais arquivos de linhagem. Em vez disso:
    - Se 'custom_fig' for fornecido (DENV), ele será exibido.
    - Se 'lineage_data' (um DataFrame) for fornecido (SC2, CHIKV),
      ele será usado para criar um gráfico de barras.
    """
    print("Gerando relatório de qualidade interativo...")
    
    # --- 1. Preparação dos Dados (Violino e Barras) ---
    coverage['coverage_breadth'] = coverage['coverage_breadth'] * 100
    coverage['Status'] = coverage['cod'].apply(
        lambda x: 'Controle Negativo (CN)' if x == 'CN' else 'Amostra'
    )
    reads['unmapped'] = reads['total_reads'] - reads['mepf_reads_aligned']

    # --- 2. Criação dos Gráficos (Violinos e Barras) ---
    color_discrete_map = {'Controle Negativo (CN)': 'red', 'Amostra': '#1f77b4'}

    # Gráfico 1: Violino da Profundidade Média
    fig_violin_depth = px.violin(
        coverage, y='mean_depth_coverage', 
        box=True, points='all', hover_data=['cod'], 
        color='Status', color_discrete_map=color_discrete_map,
        title='Distribuição da Profundidade Média (mean_depth_coverage)'
    )
    fig_violin_depth.update_traces(pointpos=0, jitter=0.4, spanmode='hard')
    fig_violin_depth.update_yaxes(title_text='Profundidade Média')

    # Gráfico 2: Violino da Cobertura Horizontal
    fig_violin_coverage = px.violin(
        coverage, y='coverage_breadth', 
        box=True, points='all', hover_data=['cod'], 
        color='Status', color_discrete_map=color_discrete_map,
        title='Distribuição da Cobertura Horizontal (coverage_breadth)'
    )
    fig_violin_coverage.update_traces(pointpos=0, jitter=0.4, spanmode='hard')
    fig_violin_coverage.update_yaxes(title_text='Cobertura (%)')

    # Gráfico 3: Hierarquia (Barra ou Sunburst)
    fig_extra = None
    pie_title = "Proporção de Linhagens/Genótipos" # Título padrão
    
    if custom_fig is not None:
        # Lógica para DENV: usa a figura Sunburst pré-criada
        fig_extra = custom_fig
        if hasattr(custom_fig.layout, 'title') and custom_fig.layout.title.text:
             pie_title = custom_fig.layout.title.text # Usa o título da figura
    
    elif lineage_data is not None:
        # Lógica para SC2 e CHIKV: constrói o gráfico de barras
        try:
            if not lineage_data.empty:
                # 1. Calcular porcentagem
                total_count = lineage_data['count'].sum()
                lineage_data['percent'] = (lineage_data['count'] / total_count)
                lineage_data['percent_str'] = lineage_data['percent'].map(lambda p: f"{p:.1%}") 
                
                # 2. Ordenar o dataframe
                lineage_data = lineage_data.sort_values(by='count', ascending=False)
                
                # Detecta a coluna de nomes (deve ser a primeira)
                names_col = lineage_data.columns[0] 

                # 3. Criar o Bar Chart
                fig_extra = px.bar(
                    lineage_data,
                    x=names_col,
                    y='count',
                    title=pie_title,
                    text='percent_str'
                )
                
                # 4. Ajustar layout e hover
                fig_extra.update_traces(
                    texttemplate='%{text}',
                    textposition='outside',
                    hovertemplate="<b>%{x}</b><br>Contagem: %{y}<br>Porcentagem: %{text}<extra></extra>"
                )
                fig_extra.update_yaxes(title_text='Contagem (Absoluto)')
                fig_extra.update_xaxes(title_text='Linhagem / Genótipo')
        except Exception as e:
            print(f"Aviso: Não foi possível construir o gráfico de barras. Erro: {e}")
    else:
        print("Aviso: Nenhum dado de linhagem ou figura customizada fornecida. Gráfico pulado.")


    # Gráfico 4: Gráfico de Barras (Leituras Mapeadas)
    # (Código do 'fig_reads' permanece o mesmo)
    reads_df = reads[['cod','mepf_reads_aligned','unmapped']]
    df_tidy_reads = reads_df.melt(id_vars=['cod'], var_name='Tipo de Leitura', value_name='Contagem')
    df_tidy_reads['Tipo de Leitura'] = df_tidy_reads['Tipo de Leitura'].map({
        'mepf_reads_aligned': 'Leituras Mapeadas',
        'unmapped': 'Leituras Não Mapeadas'
    })
    fig_reads = px.bar(
        df_tidy_reads, x='cod', y='Contagem', color='Tipo de Leitura',
        title='Leituras Mapeadas vs. Não Mapeadas por Amostra',
        barmode='stack', hover_data=['cod', 'Tipo de Leitura', 'Contagem']
    )
    fig_reads.update_layout(xaxis_title="Amostra", yaxis_title="Número de Leituras")


    # --- 4. Salvar como um único arquivo HTML ---
    html_path = os.path.join(output_folder, "RNSG_REPORT/Quality_check.html")

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write("<html><head><title>Relatório de Qualidade</title></head>")
        f.write("<body style='font-family: sans-serif;'>\n")
        f.write("<h1 style='text-align: center;'>Relatório de Qualidade</h1>\n")
        
        f.write("<h2>Métricas de Cobertura e Profundidade</h2>\n")
        f.write(fig_violin_depth.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(fig_violin_coverage.to_html(full_html=False, include_plotlyjs=False))

        f.write("<h2>Contagem de Leituras</h2>\n")
        f.write(fig_reads.to_html(full_html=False, include_plotlyjs=False))
        f.write("</body></html>\n")


        # Escreve o gráfico extra (Barra ou Sunburst)
        if fig_extra:
            f.write(f"<h2>{pie_title}</h2>\n")
            f.write(fig_extra.to_html(full_html=False, include_plotlyjs=False))

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