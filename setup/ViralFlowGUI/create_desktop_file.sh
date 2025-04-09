#!/bin/bash

code_path=$(pwd)

# Caminhos relativos
SCRIPT_SH="$code_path/../viralflow_GUI"
ICON_RELATIVE_PATH="/ViralFlow/docs/source/img/viralflow_logo.png"

# Resolver caminhos absolutos
SCRIPT_SH_PATH=$(realpath "$SCRIPT_SH")
ICON_FULL_PATH="$(getent passwd $SUDO_USER | cut -d: -f6)$ICON_RELATIVE_PATH"

if [[ ! -f "$SCRIPT_SH_PATH" ]]; then
# Verificar se os arquivos existem
    echo "Erro: Arquivo viralflow_GUI não encontrado em $SCRIPT_SH_PATH"
    exit 1
fi

# Criar o arquivo .desktop
DESKTOP_FILE="../viralflow_GUI.desktop"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=ViralFlow GUI
Comment=Execute the ViralFlow pipeline
Exec=$SCRIPT_SH_PATH
Icon=$ICON_FULL_PATH
Terminal=true
Categories=Science;Biology;
EOF

# Copiar para o diretório de aplicações
cp "$DESKTOP_FILE" $(getent passwd $SUDO_USER | cut -d: -f6)/.local/share/applications/
echo "Desktop file criado com sucesso e copiado para ~/.local/share/applications"
