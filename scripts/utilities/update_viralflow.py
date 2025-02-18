import subprocess
from PyQt5.QtWidgets import QMessageBox

def atualizar_viralflow():
    try:
        comando = """
        cd $HOME/ViralFlow
        
        export MAMBA_EXE="$HOME/bin/micromamba"
        export MAMBA_ROOT_PREFIX="$HOME/micromamba"
        __mamba_setup="$($MAMBA_EXE shell hook --shell bash --root-prefix "$MAMBA_ROOT_PREFIX" 2> /dev/null)"
        if [ $? -eq 0 ]; then
            eval "$__mamba_setup"
        else
            alias micromamba="$MAMBA_EXE"
        fi
        unset __mamba_setup
        
        git checkout main
        git pull
        
        pip install -e .
    
        """

        subprocess.run(["bash", "-c", comando], check=True)
        
        QMessageBox.information(None, "Sucesso", "ViralFlow atualizado com sucesso!")
        
    except subprocess.CalledProcessError as e:
        QMessageBox.critical(None, "Erro", f"Falha ao atualizar o ViralFlow:\n{e}")
