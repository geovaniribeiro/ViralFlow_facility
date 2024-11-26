#!/bin/bash

# Update and install necessary packages
sudo apt update -y && \
sudo apt upgrade -y && \
sudo apt install curl git python3-pip uidmap -y

# Download and set up Micromamba
cd $HOME
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/1.5.7 | tar -xvj bin/micromamba
./bin/micromamba shell init -s bash -p ~/micromamba
source ~/.bashrc
micromamba activate

# Clone ViralFlow repository and set up the environment
git clone https://github.com/WallauBioinfo/ViralFlow
cd ViralFlow/
micromamba env create -f envs/env.yml
micromamba activate viralflow
pip install -e .

# Create symbolic link for unsquashfs
sudo ln -s /usr/bin/unsquashfs /usr/local/bin/unsquashfs

# Build containers
viralflow -build_containers
