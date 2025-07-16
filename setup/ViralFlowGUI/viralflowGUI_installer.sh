#!/bin/bash

echo ">>> INICIANDO INSTALAÇÃO DO VIRALFLOW_GUI!"

read -p "Pressione ENTER para continuar..."

# Detecta caminho absoluto deste script
code_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Caminho detectado: $code_path"

# Adiciona micromamba ao PATH explicitamente
export PATH="$HOME/bin:$PATH"

# Inicializa o shell para micromamba
eval "$(micromamba shell hook --shell bash)"

# Configuração do micromamba
export MAMBA_EXE="$HOME/bin/micromamba"
export MAMBA_ROOT_PREFIX="$HOME/micromamba"
__mamba_setup="$("$MAMBA_EXE" shell hook --shell bash --root-prefix "$MAMBA_ROOT_PREFIX" 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias micromamba="$MAMBA_EXE"
fi
unset __mamba_setup

micromamba activate

# Verifica onde está o env.yml
if [ -f "$code_path/usr/envs/env.yml" ]; then
    env_file="$code_path/usr/envs/env.yml"
elif [ -f "$code_path/../usr/envs/env.yml" ]; then
    env_file="$code_path/../usr/envs/env.yml"
elif [ -f "$code_path/../../setup/usr/envs/env.yml" ]; then
    env_file="$code_path/../../setup/usr/envs/env.yml"
else
    echo "Arquivo env.yml não encontrado!"
    exit 1
fi

echo "Usando env.yml em: $env_file"

# Criar o ambiente
yes | micromamba env create -f "$env_file" --yes
micromamba activate viralflow_gui

# Instalar dependências PyQt (interface gráfica)
sudo apt-get install -y \
    libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0 libegl1-mesa

# Tornar arquivos executáveis
chmod +x "$code_path/../../viralflow_GUI" 2>/dev/null
chmod +x "$code_path/../viralflow_GUI" 2>/dev/null
chmod +x "$code_path/viralflow_GUI" 2>/dev/null

# Localizar o script para criar .desktop
if [ -f "$code_path/ViralFlowGUI/create_desktop_file.sh" ]; then
    desktop_script="$code_path/ViralFlowGUI/create_desktop_file.sh"
elif [ -f "$code_path/create_desktop_file.sh" ]; then
    desktop_script="$code_path/create_desktop_file.sh"
elif [ -f "$code_path/../ViralFlowGUI/create_desktop_file.sh" ]; then
    desktop_script="$code_path/../ViralFlowGUI/create_desktop_file.sh"
else
    echo "Script create_desktop_file.sh não encontrado!"
    exit 1
fi

# Executar criação do .desktop
sudo bash "$desktop_script"

# Verificar sucesso
if [ $? -eq 0 ]; then
    echo ""
    echo '##############################################################################'
    echo '########################## ViralFlow GUI Instalado! ##########################'
    echo '##############################################################################'
    echo ''
else
    echo ""
    echo '##############################################################################'
    echo '##################### Erro na instalação do ViralFlow GUI! ###################'
    echo '##############################################################################'
    echo ''
fi
