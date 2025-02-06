#!/bin/bash

# Caminhos relativos
SCRIPT_SH="../viralflow_GUI"
ICON_PATH="$HOME/ViralFlow/docs/source/img/viralflow_logo.png"

# Resolver caminhos absolutos
SCRIPT_SH_PATH=$(realpath "$SCRIPT_SH")
ICON_FULL_PATH=$(realpath "$ICON_PATH")

# Verificar se os arquivos existem
if [[ ! -f "$SCRIPT_SH_PATH" ]]; then
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
cp "$DESKTOP_FILE" ~/.local/share/applications/
echo "Desktop file criado com sucesso e copiado para ~/.local/share/applications"
