#!/bin/bash

code_path=$(pwd)

# Carregar manualmente as alterações feitas no ~/.bashrc no ambiente atual
export MAMBA_EXE="$HOME/bin/micromamba"
export MAMBA_ROOT_PREFIX="$HOME/micromamba"
__mamba_setup="$("$MAMBA_EXE" shell hook --shell bash --root-prefix "$MAMBA_ROOT_PREFIX" 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias micromamba="$MAMBA_EXE"  # Fallback para ativar manualmente, se necessário
fi
unset __mamba_setup

micromamba activate

micromamba activate viralflow

###################
#Instalar bibliotecas adicionais para gerar os arquivos e relatorios

cd $code_path

pip install -r $code_path/../envs/env.yml

#Create .desktop file
$code_path/create_desktop_file.sh

echo ""
echo ""
echo '##############################################################################';
echo '########################## ViralFlow GUI Instalado! ##########################';
echo '##################### Esse terminal pode ser fechado #########################';
echo '##############################################################################';