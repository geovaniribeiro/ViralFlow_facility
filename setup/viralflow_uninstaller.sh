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

if micromamba env list | grep -q "viralflow_gui"; then
    yes | micromamba env remove -n viralflow_gui --yes
else
    echo "Ambiente 'viralflow_gui' não encontrado, ignorando remoção."
fi

# Remover pasta viralflow com sudo para evitar erros de permissão
if [ -d "$HOME/ViralFlow" ]; then
    sudo rm -rf "$HOME/ViralFlow"
else
    echo "Pasta 'ViralFlow' não encontrada, ignorando remoção."
fi

echo ""
echo ""
echo '###############################################################################'
echo '#################### ViralFlow Removido com Sucesso! ##########################'
echo '###################### Esse terminal pode ser fechado #########################'
echo '###############################################################################'
