#!/usr/bin/env python3

#Carregar todas as lib usadas ao longo de todo script
import pandas as pd
import csv
import os
import sys
from unidecode import unidecode
import seaborn as sns

from scripts.analysis.report.modules_general import load_config, mod_pasta, Quality_monitor, \
    remover_csv, input_folder,process_and_combine_data
from scripts.analysis.report.modules_EpiArbo import filter_depth, format_virus_name 
from scripts.analysis.report.report_generator_denv import gerar_arquivo_fasta, arquivo_epiarbo

def planilha_resultado(arbo_virus_name, final_df, output_folder):

    print("planilha_resultado")

    result_table = arbo_virus_name[['id','arbo_virus_name']]

    #Merge df
    result_table = pd.merge(result_table, final_df, left_on = 'id', right_on = 'Código Amostra', how='right')

    #drop team_name column
    result_table.drop('Código Amostra', axis=1, inplace=True)

    # Adicionar a coluna colunas extras com valores vazios
    result_table["LACEN Executor"] = ""
    result_table["Unidade Federativa (UF)"] = ""
    result_table["Responsável envio dos dados"] = ""
    result_table["Genótipo"] = ""
    result_table["Data sequenciamento"] = ""
    result_table["Vírus"] = "CHIKV"
    result_table["CT"] = ""
    result_table["Software Montagem"] = "ViralFlow"
    result_table["Versão software"] = "1.3"
    result_table["Versão primer"] = "ZDC_CADDE 1.0"

    #Change order header
    result_table = result_table[["LACEN Executor", "Unidade Federativa (UF)", "Responsável envio dos dados", "Data sequenciamento",
                                 "Vírus", 'id', 'Requisição', "CT", 'Município', 'Estado_do_Solicitante',
                                 'Data Coleta', 'Tipo Amostra', 'Idade', "Tipo_Idade", 'Sexo', 'Software Montagem',
                                 "Versão software", "Versão primer", 'Reads','Depth of Coverage', 'Coverage',
                                 'Genótipo', 'arbo_virus_name']]
    
    #Mudar nomes da coluna
    result_table = result_table.rename(columns={'Requisição':'Gal Sequenciamento','id': 'Código Amostra',
                                                'arbo_virus_name': 'Nome da Sequencia', 'Coverage': 'Cobertura', 
                                                'Depth of Coverage': 'Profundidade Média', 
                                                'Estado_do_Solicitante': 'UF município solicitante',
                                                'Tipo_Idade': 'Tipo Idade'})

    # Salve o DataFrame resultante em um arquivo Excel
    result_table.to_excel(os.path.join(output_folder, 'RNSG_REPORT/Planilha_de_Resultado.xlsx'), index=False)

#Define as colunas do dataframe a serem renomeadas
rename_columns = {'cod': 'Código Amostra',
                  'mepf_reads_aligned': 'Reads',
                  'PCT_10X': 'Coverage',
                  'MEAN_COVERAGE': 'Depth of Coverage',
                  'Requisição': 'Requisição',
                  'Material_Biológico': 'Tipo Amostra',
                  'Municipio_do_Solicitante': 'Município',
                  'Data_da_Coleta': 'Data Coleta',
                  'Sexo': 'Sexo'}

def generate_report_chikv(metadata_path, config_path, output_folder):

    # Carregar configurações
    config = load_config(config_path)
    
    mod_pasta(output_folder)
    
    # Processar os arquivos na pasta de entrada
    metadata, sequence, records, reads, coverage = input_folder(output_folder, metadata_path)

    df_combine_sequence = process_and_combine_data(metadata, reads, coverage, output_folder, rename_columns)

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
    gerar_arquivo_fasta(records, metadata, final_df, output_folder, seq_id_fixed="ChikV")

    seq_file = os.path.join(output_folder, "seq_df.csv")
    if os.path.exists(seq_file):
        df_combine_sequence = pd.read_csv(seq_file)
        # Chama a função usando o arquivo atualizado
        arquivo_epiarbo(config, metadata, df_combine_sequence, output_folder, 
                        arbo_virus_name_value = "Chikungunya virus", seq_id_fixed= "ChikV")

        epi_arbo_file = os.path.join(output_folder, 'RNSG_REPORT', 'EpiArbo.csv')
        #Removendo as colunas "arbo_subtype" e "arbo_last_vaccination_date" que estão no EpiArbo (DENV) mas não estão no EpiArbo (CHIKV)
        colunas_remover = ['arbo_subtype', 'arbo_last_vaccination_date']
        df_epi_arbo = pd.read_csv(epi_arbo_file)
        df_epi_arbo = df_epi_arbo.drop(columns=colunas_remover, errors='ignore')
        df_epi_arbo.to_csv(epi_arbo_file, index=False)

    else:
        raise FileNotFoundError(f"Arquivo {seq_file} não encontrado!")
    

    arbo_virus_name = os.path.join(output_folder, 'RNSG_REPORT/Planilha_de_Resultado.xlsx')
    if os.path.exists(arbo_virus_name):
        covv_virus_name = pd.read_excel(arbo_virus_name)
        planilha_resultado(covv_virus_name, final_df, output_folder)
    else:
        raise FileNotFoundError(f"Arquivo {arbo_virus_name} não encontrado!")

    Quality_monitor(coverage, reads, output_folder)

    # Limpar arquivos temporários e monitorar qualidade
    remover_csv(output_folder)

# Mantém a funcionalidade standalone
if __name__ == "__main__":
    output_folder = sys.argv[1]
    metadata_path = sys.argv[2]
    config_path = sys.argv[3]
    generate_report_chikv(output_folder, metadata_path, config_path)