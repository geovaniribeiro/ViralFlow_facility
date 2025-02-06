#!/usr/bin/env python3

#Carregar todas as lib usadas ao longo de todo script
import os
from unidecode import unidecode
import seaborn as sns
import re

#A função 'filter_depth' gera um arquivo intermediário 'tabela_resultados_filt.csv' com informações apenas das amostras com cobertua > 60%
def filter_depth(resultado_df, output_folder):

    resultado_df_filt = resultado_df.loc[resultado_df['Coverage'] >= 60]

    resultado_df_filt.to_csv(os.path.join(output_folder, "tabela_resultados_filt.csv"))

    return resultado_df_filt


# Função para formatar nomes de vírus no padrão
def format_virus_name(s):
    return re.sub(
        r'(DENV|CHIKV|ZIKV)',  # Padrões que deseja substituir
        lambda x: x.group(0)[0].upper() + x.group(0)[1:-1].lower() + x.group(0)[-1].upper(),
        s
    )
