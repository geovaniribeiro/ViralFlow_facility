#!/bin/bash
#Esse script executa o desintalador e instalador do viralflow, e
#instala a interface gráfica ViralFlow GUI

code_path=$(pwd)

#remove versão anterior viralflow
cd $code_path
chmod +x viralflow_uninstaller.sh
sudo $code_path/viralflow_uninstaller.sh

#Instalação viralflow diretamento do repositorio
cd $code_path
chmod +x viralflow_installer.sh
sudo $code_path/viralflow_installer.sh

#Instalar a versão GUI do viralflow
cd $code_path
chmod +x viralflow_GUI_setup.sh
sudo $code_path/viralflow_GUI_setup.sh