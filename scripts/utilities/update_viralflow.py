import subprocess
from PyQt5.QtWidgets import QMessageBox

def atualizar_viralflow():
    try:
        comando = """
        #DESINSTALAÇÃO
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
       
        # Verificar se o ambiente existe antes de tentar remover
        if micromamba env list | grep -q "viralflow"; then
            yes | micromamba env remove -n viralflow --yes
        else
            echo "Ambiente 'viralflow' não encontrado, ignorando remoção."
        fi

        # Remover pasta viralflow com sudo para evitar erros de permissão
        if [ -d "$HOME/ViralFlow" ]; then
            sudo rm -rf "$HOME/ViralFlow"
        else
            echo "Pasta 'ViralFlow' não encontrada, ignorando remoção."
        fi

        #INSTALAÇÃO
        cd $HOME

        # Clonar repositório do ViralFlow e configurar o ambiente
        git clone https://github.com/WallauBioinfo/ViralFlow
        cd ViralFlow/

        yes | micromamba env create -f envs/env.yml --yes
        micromamba activate viralflow

        # Instalar o ViralFlow no modo de desenvolvimento
        pip install -e .

        # Criar link simbólico para unsquashfs
        sudo ln -sf /usr/bin/unsquashfs /usr/local/bin/unsquashfs

        # Baixar imagem e construir os containers
        yes | viralflow -build_containers

        """

        subprocess.run(["bash", "-c", comando], check=True)
        
        QMessageBox.information(None, "Sucesso", "ViralFlow atualizado com sucesso!")
        
    except subprocess.CalledProcessError as e:
        QMessageBox.critical(None, "Erro", f"Falha ao atualizar o ViralFlow:\n{e}")
