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

# Verificar se o ambiente existe antes de tentar remover
if micromamba env list | grep -q "viralflow"; then
    yes | micromamba env remove -n viralflow --yes
else
    echo "Ambiente 'viralflow' não encontrado, ignorando remoção."
fi

#Acessamento a home usando o sudo
cd $HOME

# Remover pasta viralflow com sudo para evitar erros de permissão
if [ -d "ViralFlow" ]; then
    sudo rm -rf ViralFlow
else
    echo "Pasta 'ViralFlow' não encontrada, ignorando remoção."
fi

# Verificar se o comando anterior foi bem-sucedido (código de saída 0 significa sucesso)
if [ $? -eq 0 ]; then
    # Se não houver erro, exibe a mensagem de sucesso
    echo ""
    echo ""
    echo '##############################################################################';
    echo '########################## ViralFlow Removido! ##############################';
    echo '###############################################################################';
    echo ''
else
    # Se houver erro, exibe a mensagem de erro
    echo ""
    echo ""
    echo '##############################################################################';
    echo '########################## Erro na remoção do ViralFlow! #####################';
    echo '##############################################################################';
    echo ''
fi