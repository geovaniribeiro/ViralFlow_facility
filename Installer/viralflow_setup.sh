#!/bin/bash

# Update and install necessary packages
#sudo apt update -y && \
#sudo apt upgrade -y && \
sudo apt install curl git python3-pip uidmap -y

code_path=$(pwd)

# Download and set up Micromamba
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

#Remove previous viraflow instalation
#sudo rm -r ViralFlow/

# Clone ViralFlow repository and set up the environment
git clone -b develop_fixMicromambaOnPangolin https://github.com/WallauBioinfo/ViralFlow
cd ViralFlow/
micromamba env create -f envs/env.yml
micromamba activate viralflow

#Instalar os 
pip install -e .

# Create symbolic link for unsquashfs
sudo ln -s /usr/bin/unsquashfs /usr/local/bin/unsquashfs

# Download image and Build containers
viralflow -build_containers

###################
#Instalar bibliotecas adicionais para gerar os arquivos e relatorios

cd $code_path

pip install -r $code_path/../envs/env.yml

#Create .desktop file
$code_path/create_desktop_file.sh

echo ""
echo ""
echo '##########################################################################';
echo '########################## ViralFlow Instalado! ##########################';
echo '##################### Esse terminal pode ser fechado #####################';
echo '##########################################################################';