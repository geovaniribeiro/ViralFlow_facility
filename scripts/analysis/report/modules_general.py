#!/usr/bin/env python3
#Carregar todas as lib usadas ao longo de todo script
import pandas as pd
import numpy as np
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
    "Código_da_Amostra": [r"C[oó]digo[_ ]*Amostra", r"C[oó]digo[_ ]*(?:da[_ ])*Amostra", r"C[oó]digo\s*(?:da\s*)?Amostra"],
    "Requisição": [r"^(Requisiç[ãa]o)$", r"^(Requisicao)$", r"^(Requisiç[ãa]o[_ ]*GAL)$", r"^(Requisicao[_ ]*GAL)$"],
    "Municipio_do_Solicitante": [r"Munic[ií]pio\s*(?:do\s*)?(?:Requisitante|Solicitante)"],
    "Estado_do_Solicitante": [r"Estado\s*(?:do\s*)?(?:Requisitante|Solicitante)"],
    "CNES_Laboratório_responsável": [r"CNES\s*(?:do\s*)?Laboratório\s*[Rr]espons[aá]vel" , r"CNES[_ ]*Laboratorio[_ ]*Responsavel"]
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
        # Remove linhas onde a coluna "taxon" contém "_minor"
    if 'taxon' in coverage.columns:
        coverage = coverage[~coverage['taxon'].str.contains('_minor', na=False)]
    coverage['cod'] = coverage['cod'].replace(to_replace ='_.*', value = '', regex = True)
    #coverage = coverage[~coverage['taxon'].str.contains('_minor', na=False)]
    #coverage['cod'] = coverage['cod'].replace(to_replace ='_.*', value = '', regex = True)

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

    return reads, coverage, errors


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
        # A remoção recursiva está correta
        shutil.rmtree(output_path)
    
    # Cria a pasta 'RNSG_REPORT' e todos os diretórios pai necessários.
    os.makedirs(output_path, exist_ok=True)


#Função para criar um grafico com métricas gerais da corrida, para aferição de controle de qualidade
def Quality_monitor(coverage, reads, output_folder):

    #print("QualityCheck")
    coverage_local = coverage.copy()
    reads_local = reads.copy()

    coverage_local['coverage_breadth'] = coverage_local['coverage_breadth']*100

    #Criar os subplots e os seus respec. eixos x
    fig = plt.figure()
    #axs = axs.flatten()

    gs = fig.add_gridspec(2,2)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])
    #ax4 = fig.add_subplot(gs[2, :])


    # Depth of Coverage (X)
    sns.violinplot(y='mean_depth_coverage', data=coverage_local, 
               inner="points", ax=ax1, cut= 0)
    
    sns.swarmplot(y='mean_depth_coverage', data=coverage_local, ax=ax1,
                  color = 'black', size=3)

    # Pinte a linha com 'CN' de outra cor (neste caso, vermelho)
    linha_cn = coverage_local[coverage_local['cod'] == 'CN']

    if not linha_cn.empty:
            ax1.scatter(x=0, y=linha_cn['coverage_breadth'], color='red', 
                        marker='o', label='CN', s=20)

            ax2.scatter(x=0, y=linha_cn['mean_depth_coverage'], color='red', 
                        marker='o', label='CN', s=20)

    # Coverage (%)
    sns.violinplot(y='coverage_breadth', data=coverage_local, ax=ax2, cut= 0)
    

    sns.swarmplot(y='coverage_breadth', data=coverage_local, ax=ax2,
                  color = 'black', size=3)


    #Reads Mapeadas X reads unmapped
    #Calcular o numero de redas unmmapped
    reads_local['unmapped'] = reads_local['total_reads'] - reads_local['mepf_reads_aligned']

    #select reads columns
    reads_df = reads_local[['cod','mepf_reads_aligned','unmapped']]


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

def validate_negative_control(coverage_df, errors_df):
    """
    Valida o(s) Controle(s) Negativo(s) (CN) com base nas regras da RNSG.
    
    (Versão corrigida que identifica CNs de 'coverage_df' E 'errors_df')
    """
    
    # 1. Identificar CNs e Amostras de AMBOS os arquivos
    cods_from_coverage = set(coverage_df['cod'])
    cods_from_errors = set(errors_df['cod'])
    all_cods = cods_from_coverage.union(cods_from_errors)
    
    all_cn_cods = sorted([c for c in all_cods if not c[0].isdigit()])
    
    if not all_cn_cods:
        msg = "<p style='padding: 10px; border: 1px solid #f0ad4e; background-color: #fcf8e3; color: #8a6d3b; border-radius: 5px;'>"
        msg += "<strong>Atenção:</strong> Nenhum Controle Negativo (CN) foi identificado. "
        msg += "A validação da corrida não pôde ser realizada.</p>"
        # Retorna o coverage_df completo, pois não há positivos para filtrar
        return msg, coverage_df 

    # Amostras positivas são aquelas em 'coverage_df' que NÃO são CNs
    positive_samples_df = coverage_df[~coverage_df['cod'].isin(all_cn_cods)]

    # 2. Calcular Limiares de Validação (usando apenas amostras positivas)
    valid_depths = positive_samples_df[positive_samples_df['mean_depth_coverage'] != np.inf]['mean_depth_coverage'].dropna()
    
    if not valid_depths.empty:
        std_dev_positives = valid_depths.std()
        depth_threshold = std_dev_positives - 50
    else:
        std_dev_positives = 0
        depth_threshold = -50 
        
    coverage_threshold = 0.05  # 5% (coverage_breadth é 0-1)

    # 3. Validar cada CN da lista combinada
    validation_passed = True
    messages = []
    
    for cn_cod in all_cn_cods:
        cn_messages_list = []
        cn_has_error = cn_cod in cods_from_errors
        cn_in_coverage = cn_cod in cods_from_coverage
        
        if cn_in_coverage:
            # Cenário 1: CN está no short_summary.csv (gerou consenso)
            # Devemos validar as métricas
            try:
                cn_row = coverage_df[coverage_df['cod'] == cn_cod].iloc[0]
                cn_coverage = cn_row['coverage_breadth']
                cn_depth = cn_row['mean_depth_coverage']
                cn_lineage = cn_row.get('lineage') 

                # Regra 1: Linhagem
                if pd.notna(cn_lineage) and cn_lineage != '':
                    validation_passed = False
                    cn_messages_list.append(f"<b>Falha:</b> Possui linhagem classificada ({cn_lineage}).")
                
                # Regra 2: Cobertura
                if cn_coverage >= coverage_threshold:
                    validation_passed = False
                    cn_messages_list.append(f"<b>Falha:</b> Cobertura >= 5% (Valor: {cn_coverage:.2f}%).")
                
                # Regra 3: Profundidade
                if cn_depth >= depth_threshold:
                    validation_passed = False
                    cn_messages_list.append(f"<b>Falha:</b> Profundidade >= {depth_threshold:.2f} (Valor: {cn_depth:.2f}).")
                
                if cn_has_error:
                    cn_messages_list.append("<b>Info:</b> Também detectado no 'errors_detected.csv'.")
                
                if not cn_messages_list:
                    messages.append(f"<li><b>{cn_cod}:</b> Aprovado (Gerou consenso, mas métricas estão abaixo dos limiares).</li>")
                else:
                    messages.append(f"<li><b>{cn_cod}:</b><ul><li>{'</li><li>'.join(cn_messages_list)}</li></ul></li>")

            except Exception as e:
                messages.append(f"<li><b>{cn_cod}:</b> Erro inesperado na validação (short_summary): {e}.</li>")
                validation_passed = False
        
        elif cn_has_error:
            # Cenário 2: CN está APENAS no errors_detected.csv (falhou)
            # Este é o resultado ideal para um CN.
            messages.append(f"<li><b>{cn_cod}:</b> Aprovado (Detectado no 'errors_detected.csv' e não gerou consenso).</li>")
        
        else:
            # Cenário 3: Impossível (mas seguro verificar)
            messages.append(f"<li><b>{cn_cod}:</b> Erro - CN não encontrado em 'short_summary' ou 'errors_detected'.</li>")
            validation_passed = False


    # 4. Montar Mensagem Final
    if validation_passed:
        msg = "<p style='padding: 10px; border: 1px solid #5cb85c; background-color: #dff0d8; color: #3c763d; border-radius: 5px;'>"
        msg += "<strong>Controle Negativo (CN) Validado:</strong> A corrida parece estar livre de contaminação."
        msg += f"<ul>{''.join(messages)}</ul></p>"
    else:
        msg = "<p style='padding: 10px; border: 1px solid #d9534f; background-color: #f2dede; color: #a94442; border-radius: 5px;'>"
        msg += "<strong>Atenção - Controle Negativo (CN) REPROVADO:</strong> A corrida pode estar contaminada."
        msg += f"<ul>{''.join(messages)}</ul></p>"

    # Retorna a mensagem e o DataFrame APENAS com as amostras positivas
    return msg, positive_samples_df


# Em modules_general.py

def Quality_monitor_interactive(coverage, reads, errors, output_folder, 
                                lineage_data=None, 
                                custom_fig=None,
                                eligibility_threshold=60,
                                report_title=None):
    """
    Gera um relatório HTML interativo de controle de qualidade usando Plotly.
    Agora inclui validação de CN, uma tabela de resumo e um resumo estatístico.
    """
    
    coverage_work = coverage.copy() 
    reads_work = reads.copy()
    
    #print("Gerando relatório de qualidade...")
    
    # --- 1. Validação do Controle Negativo (CN) ---
    cn_validation_message, positive_samples_df = validate_negative_control(coverage_work, errors)

    # --- 2. Preparação dos Dados para Gráficos ---
    
    # Tabela Resumo (Req 1)
    summary_df = pd.merge(coverage_work, reads_work[['cod', 'mepf_reads_aligned']], on='cod', how='left')
    summary_df['coverage_breadth'] = summary_df['coverage_breadth'] * 100 # Converte para %
    
    eligibility_col_name = f'Elegível para Depósito (>={eligibility_threshold}%)'

    summary_df[eligibility_col_name] = summary_df['coverage_breadth'].apply(
        lambda x: 'Sim' if x >= eligibility_threshold else 'Não'
    )
    
    summary_df = summary_df[['cod', 'mepf_reads_aligned', 'coverage_breadth', 'mean_depth_coverage', eligibility_col_name]]
    summary_df.columns = ['Amostra (cod)', 'Reads Mapeadas', 'Cobertura (%)', 'Profundidade Média', eligibility_col_name]
    
    summary_df['Cobertura (%)'] = summary_df['Cobertura (%)'].round(2)
    summary_df['Profundidade Média'] = summary_df['Profundidade Média'].round(0)
    
    summary_table_html = summary_df.to_html(index=False, classes='dataframe table table-striped table-hover', border=0, justify='center')
    
    # 1) Gerar estatísticas de resumo da tabela
    total_samples = len(summary_df)
    eligible_col = summary_df.columns[-1] # Pega a coluna de elegibilidade dinamicamente
    eligible_samples = (summary_df[eligible_col] == 'Sim').sum()
    
    if total_samples > 0:
        percentage = (eligible_samples / total_samples) * 100
        summary_stats_html = (
            f"<p style='text-align: left; font-size: 16px; margin-top: 10px; margin-bottom: 20px; margin-left: 5%;'>"
            f"&bull; <strong>{eligible_samples} de {total_samples}</strong> " # Usei &bull; para um bullet HTML
            f"({percentage:.1f}%) das amostras estão elegíveis para depósito."
            f"</p>"
        )
    else:
        summary_stats_html = "<p style='text-align: center; font-size: 16px; margin-top: 10px; margin-bottom: 20px;'>Nenhuma amostra processada.</p>"
    
    
    # Dados para Violinos (usa apenas amostras positivas)
    positive_samples_df = positive_samples_df.copy() 
    positive_samples_df['Status'] = 'Amostra'
    
    # Dados para Gráfico de Barras (usa 'reads' completo)
    reads_df = reads_work.copy()
    reads_df['unmapped'] = reads_df['total_reads'] - reads_df['mepf_reads_aligned']

    # --- 3. Criação dos Gráficos ---
    color_discrete_map = {'Amostra': '#1f77b4'} # CN já foi filtrado, então só precisamos da cor 'Amostra'

    # Gráfico 1: Violino da Profundidade Média (APENAS AMOSTRAS POSITIVAS)
    fig_violin_depth = px.violin(
        positive_samples_df, y='mean_depth_coverage', 
        box=True, points='all', hover_data=['cod'], 
        color='Status', color_discrete_map=color_discrete_map,
        title='Distribuição da Profundidade Média (Amostras Positivas)'
    )
    fig_violin_depth.update_traces(pointpos=0, jitter=0.4, spanmode='hard')
    fig_violin_depth.update_yaxes(title_text='Profundidade Média')

    # Gráfico 2: Violino da Cobertura Horizontal (APENAS AMOSTRAS POSITIVAS)
    
    # Multiplicando por 100 para exibir em porcentagem (ex: 90.5) e não em decimal (ex: 0.905)
    positive_samples_df['coverage_breadth'] = positive_samples_df['coverage_breadth'] * 100
    
    fig_violin_coverage = px.violin(
        positive_samples_df, y='coverage_breadth', 
        box=True, points='all', hover_data=['cod'], 
        color='Status', color_discrete_map=color_discrete_map,
        title='Distribuição da Cobertura Horizontal (Amostras Positivas)'
    )
    fig_violin_coverage.update_traces(pointpos=0, jitter=0.4, spanmode='hard')
    fig_violin_coverage.update_yaxes(title_text='Cobertura (%)')

    # Gráfico 3: Hierarquia (Barra ou Sunburst)
    fig_extra = None
    pie_title = "Proporção de Linhagens/Genótipos"
    
    if custom_fig is not None:
        fig_extra = custom_fig
        if hasattr(custom_fig.layout, 'title') and custom_fig.layout.title.text:
             pie_title = custom_fig.layout.title.text
    
    elif lineage_data is not None:
        try:
            if not lineage_data.empty:
                total_count = lineage_data['count'].sum()
                lineage_data['percent'] = (lineage_data['count'] / total_count)
                lineage_data['percent_str'] = lineage_data['percent'].map(lambda p: f"{p:.1%}") 
                lineage_data = lineage_data.sort_values(by='count', ascending=False)
                names_col = lineage_data.columns[0] 
                fig_extra = px.bar(
                    lineage_data, x=names_col, y='count',
                    title=pie_title, text='percent_str'
                )
                fig_extra.update_traces(
                    texttemplate='%{text}', textposition='outside',
                    hovertemplate="<b>%{x}</b><br>Contagem: %{y}<br>Porcentagem: %{text}<extra></extra>"
                )
                fig_extra.update_yaxes(title_text='Contagem (Absoluto)')
                fig_extra.update_xaxes(title_text='Linhagem / Genótipo')
        except Exception as e:
            print(f"Aviso: Não foi possível construir o gráfico de barras. Erro: {e}")
    #else:
     #   print("Aviso: Nenhum dado de linhagem fornecido. Gráfico pulado.")

    # Gráfico 4: Gráfico de Barras (Leituras Mapeadas - TODAS AMOSTRAS)
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
        f.write("<html><head><title>Relatório de Qualidade</title>")
        # (CSS permanece o mesmo)
        f.write("""
        <style>
            body { font-family: sans-serif; margin: 20px; }
            h1 { text-align: center; }
            h2 { border-bottom: 2px solid #eee; padding-bottom: 5px; margin-top: 40px; }
            .dataframe {
                border-collapse: collapse;
                width: 90%;
                margin: 20px auto;
                font-size: 14px;
                text-align: left;
            }
            .dataframe th, .dataframe td {
                padding: 10px 12px;
                border: 1px solid #ddd;
            }
            .dataframe th {
                background-color: #f2f2f2;
            }
            .dataframe tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .dataframe tr:hover {
                background-color: #f1f1f1;
            }
        </style>
        """)
        f.write("</head><body>\n")
        report_display_title = report_title if report_title else "Relatório de Qualidade"
        f.write(f"<h1 style='text-align: center;'>{report_display_title}</h1>\n")
        
        # 1. Mensagem de Validação do CN
        f.write("<h2>Validação do Controle Negativo (CN)</h2>\n")
        f.write(cn_validation_message)

        # 2. Tabela Resumo e Novo Resumo Estatístico
        f.write("<h2>Resumo da Corrida</h2>\n")
        f.write(summary_table_html)
        f.write(summary_stats_html) # <-- ADICIONADO AQUI
        
        # 3. Gráficos de Violino
        f.write("<h2>Métricas de Qualidade (Amostras Positivas)</h2>\n")
        f.write(fig_violin_depth.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(fig_violin_coverage.to_html(full_html=False, include_plotlyjs=False))


        # 4. Gráfico de Leituras (Respeitando sua nova ordem)
        f.write("<h2>Contagem de Leituras (Todas as Amostras)</h2>\n")
        f.write(fig_reads.to_html(full_html=False, include_plotlyjs=False))

        # 5. Gráfico de Linhagem/Genótipo (Respeitando sua nova ordem)
        if fig_extra:
            f.write(f"<h2>{pie_title}</h2>\n")
            f.write(fig_extra.to_html(full_html=False, include_plotlyjs=False))

        
        f.write("</body></html>\n")

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