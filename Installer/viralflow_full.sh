#!/bin/bash

# Atualizar e instalar pacotes necessários
#sudo apt update -y && \
#sudo apt upgrade -y && \
sudo apt install curl git python3-pip uidmap -y

code_path=$(pwd)

# Download e configuração do Micromamba
cd $HOME
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/1.5.7 | tar -xvj bin/micromamba
./bin/micromamba shell init -s bash -p ~/micromamba
source ~/.bashrc

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

# Remover instalação anterior do ViralFlow
sudo rm -rf ViralFlow/

# Clonar repositório do ViralFlow e configurar o ambiente
git clone -b develop https://github.com/WallauBioinfo/ViralFlow
cd ViralFlow/
yes | micromamba env create -f envs/env.yml --yes
micromamba activate viralflow

# Instalar o ViralFlow no modo de desenvolvimento
pip install -e .

# Criar link simbólico para unsquashfs
sudo ln -sf /usr/bin/unsquashfs /usr/local/bin/unsquashfs

# Baixar imagem e construir os containers
yes | viralflow -build_containers

# Instalar bibliotecas adicionais para relatórios
cd $code_path

pip install -r $code_path/../envs/env.yml

#Transform to executables files
chmod +x ../viral_GUI
chmod +x create_desktop_file.sh

# Criar arquivo .desktop
$code_path/create_desktop_file.sh

#Install PyQt plugins requirements
sudo apt-get install libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0 libegl1-mesa


echo ""
echo ""
echo '##########################################################################'
echo '########################## ViralFlow Instalado! ##########################'
echo '##################### Esse terminal pode ser fechado #####################'
echo '##########################################################################'
