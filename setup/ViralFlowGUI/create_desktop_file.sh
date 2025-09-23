#!/bin/bash

echo ">>> INICIANDO CRIAÇÃO DO ARQUIVO .desktop PARA VIRALFLOW_GUI"

# Detecta caminho atual do script
code_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Tenta identificar onde está o executável viralflow_GUI
caminhos_possiveis=(
    "$code_path/../../viralflow_GUI"
    "$code_path/../viralflow_GUI"
    "$code_path/viralflow_GUI"
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
    echo "Erro: Arquivo viralflow_GUI não encontrado em nenhum dos caminhos esperados."
    exit 1
fi

# Caminhos para ícone
ICON_RELATIVE_PATH="/ViralFlow/docs/source/img/viralflow_logo.png"
ICON_FULL_PATH="$(getent passwd $SUDO_USER | cut -d: -f6)$ICON_RELATIVE_PATH"

# Verifica se o ícone existe
if [[ ! -f "$ICON_FULL_PATH" ]]; then
    echo "Aviso: Ícone não encontrado em $ICON_FULL_PATH. Usando ícone padrão do sistema."
    ICON_FULL_PATH=utilities/icons/default.png  # ou deixe em branco, se preferir
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
destino="$(getent passwd $SUDO_USER | cut -d: -f6)/.local/share/applications/"
mkdir -p "$destino"
cp "$DESKTOP_FILE" "$destino"

echo ""
echo "Arquivo .desktop criado e copiado com sucesso para:"
echo "$destino"
