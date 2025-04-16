#!/bin/bash

echo ">>> INSTALAÇÃO DO VIRALFLOW_GUI INICIANDO!"

read -p "Pressione ENTER para continuar..."

code_path=$(pwd)

# Adiciona o micromamba ao PATH explicitamente
export PATH="$HOME/bin:$PATH"

# Inicializa o shell para micromamba
eval "$(micromamba shell hook --shell bash)"

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

yes | micromamba env create -f "$code_path/usr/envs/env.yml" --yes

micromamba activate viralflow_gui

###################

#Install PyQt plugins requirements
sudo apt-get install libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0 libegl1-mesa

#Transform to executables files
chmod +x $code_path/../viralflow_GUI
chmod +x $code_path/ViralFlowGUI/create_desktop_file.sh

# Criar arquivo .desktop
sudo $code_path/ViralFlowGUI/create_desktop_file.sh

# Verificar se o comando anterior foi bem-sucedido (código de saída 0 significa sucesso)
if [ $? -eq 0 ]; then
    # Se não houver erro, exibe a mensagem de sucesso
    echo ""
    echo ""
    echo '##############################################################################';
    echo '########################## ViralFlow GUI Instalado! ##########################';
    echo '##############################################################################';
    echo ''
else
    # Se houver erro, exibe a mensagem de erro
    echo ""
    echo ""
    echo '##############################################################################';
    echo '########################## Erro na instalação do ViralFlow GUI! ##############';
    echo '##############################################################################';
    echo ''
fi