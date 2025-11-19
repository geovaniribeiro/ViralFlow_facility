#!/usr/bin/env python3

import pandas as pd
import os
import sys
import plotly.express as px
import numpy as np

# Acessa as funções gerais e EpiArbo
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.analysis.report.modules_general import load_config, mod_pasta, Quality_monitor, \
    Quality_monitor_interactive, remover_csv, input_folder, process_and_combine_data, validate_negative_control

# Funções auxiliares (serão importadas do report_generator_denv.py ou modules_EpiArbo.py)
# Assumimos que gerar_arquivo_fasta, arquivo_epiarbo, planilha_resultado, etc., estão disponíveis.
# Caso contrário, as funções abaixo falharão!

# Mapeamento de segmentos para os Accession/Recursos
SEGMENTS = [
    {"segment": "L", "accession": "OL689334.1"},
    {"segment": "M", "accession": "OL689333.1"},
    {"segment": "S", "accession": "OL689332.1"},
]

def load_and_compile_segment_qc(base_out_dir, segments_list):
    """
    Carrega short_summary.csv (coverage) e reads_count.csv (reads) de todas as pastas de segmento,
    adiciona a coluna 'Segmento' e concatena tudo em um DataFrame único.
    """
    all_coverage_data = []
    all_reads_data = []
    
    for info in segments_list:
        segment_name = info['segment']
        # Caminho da pasta de output do ViralFlow para o segmento
        segment_output_path = os.path.join(base_out_dir, f"OROV_{segment_name}", "COMPILED_OUTPUT")

        try:
            # 1. Carrega Coverage/Short Summary
            coverage_path = os.path.join(segment_output_path, 'short_summary.csv')
            coverage_df = pd.read_csv(coverage_path, sep=',')
            
            # 2. Carrega Reads Count
            reads_path = os.path.join(segment_output_path, 'reads_count.csv')
            reads_df = pd.read_csv(reads_path, sep=',')

            # 3. Limpeza e Marcação
            coverage_df['cod'] = coverage_df['cod'].replace(to_replace='_.*', value='', regex=True)
            #coverage_df = coverage_df[~coverage_df['taxon'].str.contains('_minor', na=False)]
            reads_df['cod'] = reads_df['cod'].replace(to_replace='_.*', value='', regex=True)

            # Adiciona a coluna chave para identificação
            coverage_df['Segmento'] = segment_name
            reads_df['Segmento'] = segment_name
            
            all_coverage_data.append(coverage_df)
            all_reads_data.append(reads_df)

        except FileNotFoundError:
            print(f"Aviso: Arquivos não encontrados para o segmento OROV_{segment_name}. Pulando.")
        except Exception as e:
            print(f"Erro ao processar dados do segmento OROV_{segment_name}: {e}")

    # Concatena todos os DataFrames em um único
    if all_coverage_data and all_reads_data:
        compiled_coverage = pd.concat(all_coverage_data, ignore_index=True)
        compiled_reads = pd.concat(all_reads_data, ignore_index=True)
        return compiled_coverage, compiled_reads
    
    return pd.DataFrame(), pd.DataFrame()


def generate_compiled_report_orov(base_out_dir, config_path):
    """
    Função principal que orquestra a compilação, geração do relatório de QC
    e criação da pasta RNSG_REPORT final.
    """
    print("Iniciando compilação de dados OROV (L, M, S)...")
    
    # Define o caminho de saída compilado (onde o HTML será salvo)
    COMPILED_DIR = os.path.join(base_out_dir, "OROV_COMPILED_OUT")
    
    # 1. Carrega e Agrega Dados de QC de todos os Segmentos
    compiled_coverage, compiled_reads = load_and_compile_segment_qc(base_out_dir, SEGMENTS)

    if compiled_coverage.empty:
        raise ValueError("Nenhum dado de cobertura válido encontrado para a compilação OROV.")

    # 2. Carregar o errors_detected (apenas para a validação do CN)
    # Assumimos que o errors_detected do ÚLTIMO SEGMENTO é suficiente para a validação do CN.
    last_segment_name = SEGMENTS[-1]['segment']
    errors_path = os.path.join(base_out_dir, f"OROV_{last_segment_name}", "COMPILED_OUTPUT", 'errors_detected.csv')
    
    if os.path.isfile(errors_path) and os.path.getsize(errors_path) > 0:
        errors = pd.read_csv(errors_path, sep=',')
        errors['cod'] = errors['cod'].replace(to_replace='_.*', value='', regex=True)
    else:
        errors = pd.DataFrame(columns=['cod'])

    # 3. Validação do CN (usa os dados COMPILADOS para calcular o desvio padrão)
    # A função validate_negative_control precisa ser adaptada para aceitar que o coverage_df
    # tem várias linhas por 'cod' (uma por segmento), mas a validação ainda deve funcionar.
    cn_message, compiled_positive_coverage = validate_negative_control(compiled_coverage, errors)

    # 4. Criação do Gráfico de Violino Compilado
    
    # Prepara o DataFrame para o Plotly: melt para Profundidade e Cobertura
    df_metrics = compiled_coverage[['cod', 'Segmento', 'mean_depth_coverage', 'coverage_breadth']]
    df_metrics['coverage_breadth'] = df_metrics['coverage_breadth'] * 100 # Converte para %
    df_metrics = df_metrics.melt(id_vars=['cod', 'Segmento'], var_name='Métrica', value_name='Valor')
    
    # Cria o gráfico facetado/separado por segmento
    fig_compiled_qc = px.box(
        df_metrics,
        x='Métrica', 
        y='Valor',
        color='Segmento', # Colore por segmento
        facet_col='Segmento', # Cria uma coluna para cada segmento (L, M, S)
        points='all', 
        hover_data=['cod', 'Segmento'],
        title='Distribuição de Métricas por Segmento OROV'
    )
    
    #fig_compiled_qc.update_traces(pointpos=0, jitter=0.4, spanmode='hard')
    fig_compiled_qc.update_traces(pointpos=0, jitter=0.4)
    fig_compiled_qc.for_each_xaxis(lambda axis: axis.update(title=''))
    fig_compiled_qc.update_yaxes(title_text='Valor da Métrica')

    
    # 5. Gerar a pasta e salvar o HTML
    mod_pasta(COMPILED_DIR) # Cria o RNSG_REPORT
    
    # Salva a figura compilada no diretório centralizado
    html_path = os.path.join(COMPILED_DIR, "RNSG_REPORT/Quality_check_compiled.html")

    with open(html_path, 'w', encoding='utf-8') as f:
        # Aqui você pode escrever a mensagem CN, a tabela compilada, e depois a figura compilada.
        f.write("<html><head><title>Relatório Compilado OROV</title></head><body>")
        f.write("<h1>Relatório de Qualidade Compilado OROV (L, M, S)</h1>")
        f.write("<h2>Validação do CN (Agregada)</h2>")
        f.write(cn_message)
        f.write("<h2>Gráfico de Distribuição por Segmento</h2>")
        f.write(fig_compiled_qc.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write("</body></html>")
    
    print(f"\nRelatório Compilado OROV gerado em: {html_path}")

    # RETORNAR DATAFRAMES COMPILADOS PARA USO FUTURO (FASTA/EXCEL)
    return compiled_coverage, compiled_reads


if __name__ == '__main__':
    # Exemplo de execução standalone para testes
    if len(sys.argv) > 1:
        generate_compiled_report_orov(sys.argv[1], sys.argv[2])
    else:
        print("Uso: python report_generator_orov.py <output_base_dir> <config_path>")