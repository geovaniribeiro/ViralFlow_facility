#!/bin/bash

# Atualizar e instalar pacotes necessários
sudo apt update -y && \
sudo apt upgrade -y && \
sudo apt install curl git python3-pip uidmap -y

code_path=$(pwd)

#Acessamento a home usando o sudo
#cd $(getent passwd $SUDO_USER | cut -d: -f6)

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

# Clonar repositório do ViralFlow e configurar o ambiente
git clone https://github.com/WallauBioinfo/ViralFlow
cd ViralFlow/

yes | micromamba env create -f envs/env.yml --yes
micromamba activate viralflow

# Instalar o ViralFlow no modo de desenvolvimento
pip install -e .

# Criar link simbólico para unsquashfs
sudo ln -sf /usr/bin/unsquashfs /usr/local/bin/unsquashfs

#instalar Singularity manualmente
yes | micromamba install -c wallaulab singularityce --yes

# Baixar imagem e construir os containers
yes | viralflow -build_containers

#Desativar ambiente do viralflow
micromamba deactivate viralflow

echo ""
echo ""
echo '##########################################################################'
echo '########################## ViralFlow Instalado! ##########################'
echo '##########################################################################'
echo ''
