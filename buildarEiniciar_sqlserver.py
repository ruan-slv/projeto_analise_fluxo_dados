import subprocess
import sys

# Configurações de cores para o terminal (funciona no Windows, Linux e Mac)
GREEN = "\033[0;32m"
NC = "\033[0m"

def run_command(command, description):
    """Executa um comando no terminal e exibe o status."""
    print(f"{GREEN}==> {description}...{NC}")
    try:
        # shell=True garante que o comando rode no shell padrão do sistema operacional
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\033[0;31mErro ao executar: {command}\n{e}{NC}")
        sys.exit(1)

def main():
    # Passo 1: Construir a imagem Docker
    run_command("docker build -t sql-analise-fluxo .", "Construindo a imagem Docker (sql-analise-fluxo)")

    print(f"{GREEN}==> Imagem buildada com sucesso! Pronto para ser usada pelo Docker Compose.{NC}")

if __name__ == "__main__":
    main()
