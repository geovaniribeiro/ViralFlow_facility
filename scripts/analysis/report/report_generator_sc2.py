#!/usr/bin/env python3

#Carregar todas as lib usadas ao longo de todo script
import pandas as pd
import csv
import os
import sys
from unidecode import unidecode
import seaborn as sns

from scripts.analysis.report.modules_general import load_config, mod_pasta, Quality_monitor, \
    remover_csv, input_folder, process_and_combine_data


def lineage_sc2(output_folder):

    # Construct the file path for the CSV file
    lineage_path = os.path.join(output_folder, "major_summary.csv")

    lineage = pd.read_csv(lineage_path, sep =',')

    lineage['cod'] = lineage['cod'].replace(to_replace ='_.*', value = '', regex = True)

    return lineage

#A função 'planilha_resultado' cria um arquivo chamado 'Planilha_de_Resultado.xlsx' que contem os resultados em formato de planilha xlsx.
##Contem as seguintes colunas: Gal Sequenciamento, Código Amostra, Nome da Sequencia, CT, Tipo Amostra, Município,
    #Data Coleta, Sexo, Reads, Cobertura, Profundidade Média, Linhagem

def planilha_resultado(covv_virus_name, final_df, output_folder):

    #print("planilha_resultado")

    result_table = covv_virus_name[['id','covv_virus_name']]

    #Merge df
    result_table = pd.merge(result_table, final_df, left_on = 'id', right_on = 'Código Amostra', how='right')

   # Adicionar a coluna colunas extras com valores vazios
    result_table["LACEN Executor"] = ""
    result_table["Unidade Federativa (UF)"] = ""
    result_table["Responsável envio dos dados"] = ""
    result_table["Data sequenciamento"] = ""
    result_table["Vírus"] = "SARS-CoV 2"
    result_table["CT"] = ""
    result_table["Software Montagem"] = "ViralFlow"
    result_table["Versão software"] = ""
    result_table["Versão primer"] = "Artic 5.3.2"
    result_table["Versão Pangolin"] = ""

    #Change order header
    result_table = result_table[["LACEN Executor", "Unidade Federativa (UF)", "Responsável envio dos dados", "Data sequenciamento",
                                 "Vírus", 'Código Amostra', 'Requisição', "CT", 'Município', 'Estado_do_Solicitante',
                                'Data Coleta', 'Tipo Amostra', 'Idade', "Tipo_Idade", 'Sexo', 'Software Montagem', 
                                "Versão software", "Versão primer", "Versão Pangolin", 'Reads','Depth of Coverage', 'Coverage', 
                                'Linhagem', 'covv_virus_name']]
    
    #Mudar nomes da coluna
    result_table = result_table.rename(columns={'Requisição':'Gal Sequenciamento',
                                                'covv_virus_name': 'Nome da Sequencia', 'Coverage': 'Cobertura', 
                                                'Depth of Coverage': 'Profundidade Média', 'Estado_do_Solicitante': 'UF município solicitante',
                                                'Tipo_Idade': 'Tipo Idade'})


    # Salve o DataFrame resultante em um arquivo Excel
    result_table.to_excel(os.path.join(output_folder, 'RNSG_REPORT/Planilha_de_Resultado.xlsx'), index=False)



#A função 'filter_depth' gera um arquivo intermediário 'tabela_resultados_filt.csv' com informações apenas das amostras com cobertua > 90%
def filter_depth(final_df, output_folder):

    final_df_filt = final_df.loc[final_df['Coverage'] >= 90]

    final_df_filt.to_csv(os.path.join(output_folder, "tabela_resultados_filt.csv"))

    return final_df_filt



#Função para gerar o arquivo fasta para ser submetido ao Gisaid
def gerar_arquivo_fasta(records, metadata, final_df, output_folder, cnes_codes='cnes_lacen.csv'):

    #print("gerar_arquivo_fasta")

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

    # Caminho do diretório onde o script está
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cnes_path = os.path.join(script_dir, cnes_codes)

    # Carrega o CSV
    cnes_codes = pd.read_csv(cnes_path, dtype={'CNES': str, 'SIGLA': str})

    # Garantir que a coluna no metadata também seja string
    metadata['CNES_Laboratório_responsável'] = metadata['CNES_Laboratório_responsável'].astype(str)
    cnes_codes['CNES'] = cnes_codes['CNES'].astype(str)

    # Merge para adicionar a SIGLA com base no CNES
    metadata = metadata.merge(
        cnes_codes,
        how='left',
        left_on='CNES_Laboratório_responsável',
        right_on='CNES'
    )

    # Substituir a coluna original pelo valor da sigla
    metadata['CNES_Laboratório_responsável'] = metadata['SIGLA']

    # Limpar colunas auxiliares
    metadata.drop(columns=['CNES', 'SIGLA'], inplace=True)

    # Extract the sequence and ID from each record and store in a dictionary
    data = {'id': [r.id for r in records], 'sequence': [str(r.seq) for r in records]}

    # Convert the dictionary to a pandas DataFrame
    df_sequence = pd.DataFrame(data)

    #Remover campos apos o ID
    df_sequence = df_sequence[['id','sequence']].replace(to_replace ='_.*', value = '', regex = True)

    ##Combinte the both subset based on ID sequence name
    df_combine_sequence = pd.merge(df_sequence, metadata, left_on="id", right_on="Código_da_Amostra", suffixes=('', '_dup'))

    #Controle de qualidade (cobertura)
    final_df = final_df.loc[final_df['Coverage'] >= 90]

    final_df = final_df.astype(str)

    df_combine_sequence = pd.merge(df_combine_sequence, final_df, left_on="id", right_on="Código Amostra", suffixes=('', '_dup'))

    #Extract yerar collect date
    df_combine_sequence['Data_da_Coleta'] = pd.to_datetime(df_combine_sequence['Data_da_Coleta'], dayfirst=True, errors='coerce')

    df_combine_sequence['ANO_SEMANA_EPIDEMIOLOGICA'] = df_combine_sequence['Data_da_Coleta'].dt.strftime('%Y')

    #Cria um arquivo chamado 'seq_df.csv' para ser usado na geração do fasta
    df_combine_sequence.to_csv(os.path.join(output_folder, 'seq_df.csv'), sep = ',')

    # Convert DataFrame df_combine_sequence to a fasta file with the required header format
    with open(os.path.join(output_folder, 'seq_df.csv')) as csvfile, open(os.path.join(output_folder,'RNSG_REPORT/LACEN_seq.fasta'), 'w') as outfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            seq_id = f">hCoV-19/Brazil/{row['Estado_do_Solicitante']}-LACEN{row['CNES_Laboratório_responsável']}-{row['id']}/{row['ANO_SEMANA_EPIDEMIOLOGICA']}"
            seq = row['sequence']
            outfile.write(f"{seq_id}\n{seq}\n")
    
    return df_combine_sequence


#Função para gerar o arquivo EpiCov para ser submetido ao Gisaid
def arquivo_epicov(config, metadata, df_combine_sequence, output_folder):
    
    #print("arquivo_epicov")
    
    #Columnas que serão inseridas manualmente
    #Nickname do submitter no gisaid
    submitter = config['user_info']['submitter']

    #Lista de autores CGLAB + LACEN
    covv_authors = config['user_info']['authors']

    covv_orig_lab = config['user_info']['subm_lab']

    covv_orig_lab_addr = config['user_info']['subm_lab_addr']

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
    covv_virus_name = df_combine_sequence[['Estado_do_Solicitante','CNES_Laboratório_responsável','id','ANO_SEMANA_EPIDEMIOLOGICA']].astype(str)
    covv_virus_name['covv_virus_name'] = "hCoV-19/Brazil/" + covv_virus_name['Estado_do_Solicitante'] + "-LACEN" + covv_virus_name['CNES_Laboratório_responsável'] + "-" + covv_virus_name['id'] + "/" + covv_virus_name['ANO_SEMANA_EPIDEMIOLOGICA']
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

    covv_virus_name.to_excel(os.path.join(output_folder,'RNSG_REPORT/Planilha_de_Resultado.xlsx'), index=False)

    #Collection date
    covv_collection_date = df_combine_sequence[['id','Data_da_Coleta']]
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

    # Gender (Male / Female)
    covv_gender = df_combine_sequence[['id', 'Sexo']].copy()

    # Dicionário de substituição correto
    gender = {
        'MASCULINO': 'Male', 'FEMININO': 'Female',
        'Masculino': 'Male', 'Feminino': 'Female',
        'masculino': 'Male', 'feminino': 'Female',
        'M': 'Male', 'F': 'Female'
    }

    # Substituir os valores de Sexo
    covv_gender['Sexo'] = covv_gender['Sexo'].replace(gender)

    # Renomear coluna
    covv_gender = covv_gender.rename(columns={'Sexo': 'covv_gender'})

    # Garantir que tudo seja string
    covv_gender = covv_gender.astype(str)

    # Merge com tabela final
    gisaid_temp = pd.merge(gisaid_temp, covv_gender, on='id')

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
    covv_specimen = df_combine_sequence[['id', 'Material_Biológico']].copy()
    
    #Traduzir para ingles
    bio_material_translation = {
    "Aspirado": "Aspirate",
    "Aspirado bronquico": "Bronchial aspirate",
    "Aspirado de nasofaringe": "Nasopharyngeal aspirate",
    "Aspirado Traqueal": "Tracheal aspirate",
    "Coriza": "Nasal discharge",
    "Escarro": "Sputum",
    "Exsudato de lesao cutanea": "Exudate from skin lesion",
    "Exsudato de nasofaringe": "Nasopharyngeal exudate",
    "Fragmentos de pulmao": "Lung tissue fragments",
    "Lavado bronquico": "Bronchial lavage",
    "Lavado bronquico alveolar": "Bronchoalveolar lavage",
    "Liquor": "Cerebrospinal fluid (CSF)",
    "Secrecao": "Secretion",
    "Secrecao bronquica": "Bronchial secretion",
    "Secrecao de abscessos": "Abscess secretion",
    "Secrecao nasofaringea": "Nasopharyngeal secretion",
    "Secrecao orofaringea": "Oropharyngeal secretion",
    "Secrecao orofaringe e nasofaringe": "Oropharyngeal and nasopharyngeal secretion",
    "Secrecao traqueal": "Tracheal secretion",
    "Soro": "Serum",
    "Swab": "Swab",
    "Swab Anal": "Anal swab",
    "Swab da secrecao de mucosas oral": "Oral mucosal secretion swab",
    "Swab da secrecao de Naso/orofaringe": "Naso/oropharyngeal secretion swab",
    "Swab de abscesso": "Abscess swab",
    "Swab de orofaringe": "Oropharyngeal swab",
    "Swab fecal": "Fecal swab",
    "Swab nasal": "Nasal swab",
    "Swab Nasofaringe": "Nasopharyngeal swab",
    "Swab naso-orofaringeo": "Naso-oropharyngeal swab",
    "Fragmento": "Fragment",
    "Fragmento de Placenta": "Placental fragment",
    "Fragmentos de baco": "Spleen tissue fragments",
    "Fragmentos de figado": "Liver tissue fragments",
    "Liquido pericardico": "Pericardial fluid",
    "Liquido pleural": "Pleural fluid",
    "Plasma": "Plasma",
    "Sangue": "Blood",
    "Sangue com EDTA": "EDTA blood",
    "Urina": "Urine"
}
    # Aplica a tradução
    covv_specimen['covv_specimen'] = covv_specimen['Material_Biológico'].map(bio_material_translation)
    covv_specimen = covv_specimen[['id', 'covv_specimen']].astype(str)
    gisaid_temp = pd.merge(gisaid_temp,covv_specimen,on='id')


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

    #Insert covv_authors column
    gisaid_temp.insert(28, 'covv_authors','')
    gisaid_temp.loc[:, 'covv_authors'] = covv_authors

    df_insumos = gisaid_temp

    gisaid_temp = gisaid_temp.drop('id', axis=1)

    # # Define column names
    columns = ['Submitter', 'FASTA filename', 'Virus name', 'Type', 'Passage details/history', 'Collection date',
            'Location', 'Additional location information', 'Host', 'Additional host information', 'Sampling Strategy',
            'Gender', 'Patient age', 'Patient status', 'Specimen source', 'Outbreak', 'Last vaccinated', 'Treatment',
            'Sequencing technology', 'Assembly method', 'Coverage', 'Originating lab', 'Address',
            'Sample ID given by originating laboratory', 'Submitting lab', 'Address',
            'Sample ID given by the submitting laboratory', 'Authors']


    # Crie um novo DataFrame com as colunas desejadas
    new_row = pd.DataFrame([columns], columns=gisaid_temp.columns)

    # Concatene o novo DataFrame com o DataFrame original e redefina o índice
    gisaid_temp = pd.concat([new_row, gisaid_temp], ignore_index=True)

    gisaid_temp = gisaid_temp.set_index('submitter')

    gisaid_temp.to_csv(os.path.join(output_folder, 'RNSG_REPORT/EpiCov.csv'))

    pass



#Define as colunas do dataframe a serem renomeadas
rename_columns = {
        'cod': 'Código Amostra',
        'mepf_reads_aligned': 'Reads',
        'coverage_breadth': 'Coverage',
        'mean_depth_coverage_x': 'Depth of Coverage',
        'lineage': 'Linhagem',
        'Requisição': 'Requisição',
        'Material_Biológico': 'Tipo Amostra',
        'Municipio_do_Solicitante': 'Município',
        'Data_da_Coleta': 'Data Coleta',
        'Sexo': 'Sexo'
    }

def generate_report(metadata_path, config_path, output_folder):

    # Carregar configurações
    config = load_config(config_path)
    
    mod_pasta(output_folder)
    
    # Processar os arquivos na pasta de entrada
    metadata, sequence, records, reads, coverage, errors = input_folder(output_folder, metadata_path)
    lineage = lineage_sc2(output_folder)
    df_combine_sequence = process_and_combine_data(metadata, reads, coverage, errors,
                                                   output_folder, rename_columns, lineage)

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
    gerar_arquivo_fasta(records, metadata, final_df, output_folder, cnes_codes='cnes_lacen.csv')

    seq_file = os.path.join(output_folder, "seq_df.csv")
    if os.path.exists(seq_file):
        df_combine_sequence = pd.read_csv(seq_file)
        arquivo_epicov(config, metadata, df_combine_sequence, output_folder)
    else:
        raise FileNotFoundError(f"Arquivo {seq_file} não encontrado!")

    covv_virus_name_file = os.path.join(output_folder, 'RNSG_REPORT/Planilha_de_Resultado.xlsx')
    if os.path.exists(covv_virus_name_file):
        covv_virus_name = pd.read_excel(covv_virus_name_file)
        planilha_resultado(covv_virus_name, final_df, output_folder)
    else:
        raise FileNotFoundError(f"Arquivo {covv_virus_name_file} não encontrado!")

    Quality_monitor(coverage, reads, output_folder)

    # Limpar arquivos temporários e monitorar qualidade
    remover_csv(output_folder)

# Mantém a funcionalidade standalone
if __name__ == "__main__":
    output_folder = sys.argv[1]
    metadata_path = sys.argv[2]
    config_path = sys.argv[3]
    generate_report(output_folder, metadata_path, config_path)