import subprocess
import os
import shutil
import sys
from PySide6.QtWidgets import QMessageBox

def atualizar_GUI():
    try:
        # Repositório GitHub
        repo_url = "https://github.com/geovaniribeiro/ViralFlow_facility"
        branch = "main"

        # Caminho do diretório do script atual (scripts/utilities/)
        script_exec_dir = os.path.dirname(os.path.abspath(__file__))

        # Caminho para a raiz do projeto (dois níveis acima de scripts/utilities/)
        dir_atual = os.path.abspath(os.path.join(script_exec_dir, os.pardir, os.pardir))

        # O script_dir e script_instalacao devem apontar para a localização
        # dentro do 'dir_atual' (raiz do projeto)
        script_dir = os.path.join(dir_atual, "setup", "ViralFlowGUI")
        script_instalacao = os.path.join(script_dir, "viralflowGUI_installer.sh")

        # Diretório temporário para clonar
        dir_clone = os.path.join(dir_atual, "__atualizacao_git__")

        # Remove se já existir
        if os.path.exists(dir_clone):
            shutil.rmtree(dir_clone)

        # Clona o repositório
        subprocess.run(["git", "clone", "--branch", branch, repo_url, dir_clone], check=True)
        
        # Copia os arquivos do clone para a pasta atual (raiz do projeto)
        for item in os.listdir(dir_clone):
            s = os.path.join(dir_clone, item)
            d = os.path.join(dir_atual, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # Remove a pasta temporária
        shutil.rmtree(dir_clone)

        # Reafirma o caminho do script de instalação após a cópia,
        # garantindo que está apontando para o novo local na raiz
        script_instalacao = os.path.join(dir_atual, "setup", "ViralFlowGUI", "viralflowGUI_installer.sh")
        if not os.path.exists(script_instalacao):
            raise FileNotFoundError(f"Script de instalação não encontrado: {script_instalacao}")

        # Executa o script de instalação com o cwd correto
        subprocess.run(["bash", script_instalacao], check=True, cwd=script_dir)

        # Mensagem final e reinício
        QMessageBox.information(None, "Atualização", "Atualização concluída! O app será reiniciado.")
        reiniciar_app()

    except subprocess.CalledProcessError as e:
        QMessageBox.critical(None, "Erro", f"Erro de subprocesso:\n{e}")
    except Exception as e:
        QMessageBox.critical(None, "Erro", f"Erro inesperado:\n{str(e)}")

def reiniciar_app():
    python = sys.executable
    os.execl(python, python, *sys.argv)