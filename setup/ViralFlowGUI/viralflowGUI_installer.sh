#!/bin/bash

echo ">>> INICIANDO INSTALAÇÃO DO VIRALFLOW_GUI!"

# Tenta capturar o diretório original onde o AppImage está
# O AppImage define a variável $OWD. Se não estiver definida, usa o PWD.
if [ -n "$OWD" ]; then
    INSTALL_DIR="$OWD"
else
    INSTALL_DIR="$(pwd)"
fi

echo "Diretório de instalação detectado (Host): $INSTALL_DIR"
read -p "Pressione ENTER para continuar..."

# Detecta caminho absoluto INTERNO do AppImage
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

# Verifica onde está o env.yml original
if [ -f "$code_path/usr/envs/env.yml" ]; then
    original_env_file="$code_path/usr/envs/env.yml"
elif [ -f "$code_path/../usr/envs/env.yml" ]; then
    original_env_file="$code_path/../usr/envs/env.yml"
elif [ -f "$code_path/../../setup/usr/envs/env.yml" ]; then
    original_env_file="$code_path/../../setup/usr/envs/env.yml"
else
    echo "Arquivo env.yml não encontrado!"
    exit 1
fi

echo "Arquivo de ambiente original: $original_env_file"

# Cria um arquivo temporário gravável para o env.yml
# Isso evita o erro de 'Read-only file system' ao processar dependências pip
temp_env_file=$(mktemp /tmp/viralflow_env_XXXXXX.yml)
cp "$original_env_file" "$temp_env_file"
echo "Usando cópia temporária em: $temp_env_file"

# Criar o ambiente usando o arquivo temporário
yes | micromamba env create -f "$temp_env_file" --yes

# Remove o arquivo temporário
rm "$temp_env_file"
# ---------------------

micromamba activate viralflow_gui

# Instalar dependências PyQt (interface gráfica)
sudo apt-get install -y \
    libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0 libegl1-mesa libxcb-cursor0


micromamba activate viralflow
#Baixar o banco snpEff para os virus custom
echo ""
echo ""
echo ""
echo "Instalando bancos snpEff..."
echo ""
echo ""
# Dicionário: ORG_NAME=GENOME_CODE
declare -A VIRUS_DB=(
  ["DENV1"]="NC_001477.1"
  ["DENV2"]="NC_001474.2"
  ["DENV3"]="NC_001475.2"
  ["DENV4"]="NC_002640.1"
  ["CHIKV"]="NC_004162.2"
  ["OROV_L"]="OL689334.1"
  ["OROV_S"]="OL689332.1"
  ["OROV_M"]="OL689333.1"
)

for VIRUS in "${!VIRUS_DB[@]}"; do
    GENOME="${VIRUS_DB[$VIRUS]}"
    echo "→ Instalando banco para: $VIRUS (genoma $GENOME)..."
    viralflow -add_entry_to_snpeff --org_name "$VIRUS" --genome_code "$GENOME"
done

<<<<<<< HEAD
echo ""
echo ""
echo "Instalação bancos snpEff Finalizado!"
echo ""
echo ""
micromamba activate viralflow_gui

# Ajuste de permissões para executáveis (tentativa, pode falhar se for read-only, ignorando erro)
# Nota: Num AppImage, chmod dentro do code_path não funciona e não é necessário
# pois o AppImage já deve ter permissões. O erro é suprimido.
=======
echo "Instalação bancos snpEff Finalizado!"

micromamba activate viralflow_gui
# Tornar arquivos executáveis
>>>>>>> develop
chmod +x "$code_path/../../viralflow_GUI" 2>/dev/null
chmod +x "$code_path/../viralflow_GUI" 2>/dev/null
chmod +x "$code_path/viralflow_GUI" 2>/dev/null
# Localizar o script para criar .desktop DENTRO do AppImage
if [ -f "$code_path/ViralFlowGUI/create_desktop_file.sh" ]; then
    desktop_script="$code_path/ViralFlowGUI/create_desktop_file.sh"
elif [ -f "$code_path/create_desktop_file.sh" ]; then
    desktop_script="$code_path/create_desktop_file.sh"
else
    echo "Script create_desktop_file.sh não encontrado dentro do pacote!"
    exit 1
fi

# Copiar script desktop para temp
temp_desktop_script=$(mktemp /tmp/create_desktop_XXXXXX.sh)
cp "$desktop_script" "$temp_desktop_script"
chmod +x "$temp_desktop_script"

echo "Executando configuração do atalho..."
# AQUI ESTÁ O PULO DO GATO: Passamos $INSTALL_DIR como argumento
sudo bash "$temp_desktop_script" "$INSTALL_DIR"

rm "$temp_desktop_script"

# Verificar sucesso
if [ $? -eq 0 ]; then
    echo ""
    echo '##############################################################################'
    echo '########################## ViralFlow GUI Instalado! ##########################'
    echo '##############################################################################'
else
    echo "Erro na criação do atalho."
fi