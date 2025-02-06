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

micromamba activate viralflow_gui

###################
#Install PyQt plugins requirements
sudo apt-get install libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0 libegl1-mesa

#Instalar bibliotecas adicionais para gerar os arquivos e relatorios
pip install -r $code_path/../envs/vf_gui.yml

#Transform to executables files
chmod +x ../viral_GUI
chmod +x create_desktop_file.sh

# Criar arquivo .desktop
$code_path/create_desktop_file.sh

echo ""
echo ""
echo '##############################################################################';
echo '########################## ViralFlow GUI Instalado! ##########################';
echo '##################### Esse terminal pode ser fechado #########################';
echo '##############################################################################';