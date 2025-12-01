#!/bin/bash

# Recebe o caminho original (OWD) como primeiro argumento
REAL_SETUP_PATH="$1"

echo ">>> INICIANDO CRIAÇÃO DO ARQUIVO .desktop PARA VIRALFLOW_GUI"
echo "Caminho base recebido: $REAL_SETUP_PATH"

# Se não foi passado argumento, tenta adivinhar (fallback), mas provavelmente falhará no AppImage
if [[ -z "$REAL_SETUP_PATH" ]]; then
    REAL_SETUP_PATH="$(pwd)"
fi

# Tenta identificar onde está o executável viralflow_GUI
# Baseado na sua estrutura: o AppImage está em 'setup', e o executável está um nível acima
caminhos_possiveis=(
    "$REAL_SETUP_PATH/../viralflow_GUI"      # Caminho mais provável: ../ a partir do setup
    "$REAL_SETUP_PATH/viralflow_GUI"         # Caso esteja na mesma pasta
    "$REAL_SETUP_PATH/../../viralflow_GUI"
)

SCRIPT_SH_PATH=""
for path in "${caminhos_possiveis[@]}"; do
    if [[ -f "$path" ]]; then
        SCRIPT_SH_PATH=$(realpath "$path")
        break
    fi
done

# Verifica se encontrou o executável
if [[ -z "$SCRIPT_SH_PATH" ]]; then
    echo "Erro: Arquivo viralflow_GUI não encontrado."
    echo "Procurado em: ${caminhos_possiveis[*]}"
    exit 1
fi

echo "Executável encontrado em: $SCRIPT_SH_PATH"

# Caminhos para ícone (Tenta achar relativo ao executável encontrado)
PROJECT_ROOT="$(dirname "$SCRIPT_SH_PATH")"
ICON_FULL_PATH="$PROJECT_ROOT/viralflow_logo.png"

# Verifica se o ícone existe, se não, tenta outros locais
if [[ ! -f "$ICON_FULL_PATH" ]]; then
     # Tenta o caminho relativo original que você usava
     ICON_FULL_PATH="$(getent passwd $SUDO_USER | cut -d: -f6)/ViralFlow/docs/source/img/viralflow_logo.png"
fi

if [[ ! -f "$ICON_FULL_PATH" ]]; then
    echo "Aviso: Ícone não encontrado. Usando genérico."
    ICON_FULL_PATH="utilities-terminal" 
fi

# Criar o arquivo .desktop temporário
DESKTOP_FILE="/tmp/viralflow_GUI.desktop"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=ViralFlow GUI
Comment=Execute the ViralFlow pipeline
Exec=$SCRIPT_SH_PATH
Icon=$ICON_FULL_PATH
Terminal=false
Categories=Science;Biology;
StartupWMClass=ViralFlowGUI
EOF

# Copiar para a pasta do usuário
USER_HOME=$(getent passwd $SUDO_USER | cut -d: -f6)
destino="$USER_HOME/.local/share/applications/"
mkdir -p "$destino"
cp "$DESKTOP_FILE" "$destino"
chmod +x "$destino/viralflow_GUI.desktop"

echo ""
echo "Arquivo .desktop criado e copiado com sucesso para:"
echo "$destino"