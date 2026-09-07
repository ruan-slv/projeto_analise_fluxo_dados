import subprocess

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"

def main():
    print(f"{GREEN}==> Verificando e iniciando o ambiente de dados...{NC}")

    # Tentamos dar o 'up -d'.
    # Se os containers já existirem e estiverem parados, ele só liga (sem apagar dados).
    # Se eles não existirem (após reiniciar a máquina/primeira vez), ele cria do zero.
    # O '--build' garante que o SQL Server vai ler o seu Dockerfile se você mudá-lo.
    try:
        subprocess.run("docker compose up -d --build", shell=True, check=True)
        print(f"\n{GREEN}==> Ambiente online e atualizado!{NC}")
        print("    - OLTP (SQL Server) ativo na porta 1433 (Aguarde o restore terminar em ~25s)")
        print("    - OLAP (Postgres DW) ativo na porta 5432")
    except subprocess.CalledProcessError as e:
        print(f"\033[0;31m[ERRO] Falha ao iniciar o Docker Compose: {e}{NC}")

if __name__ == "__main__":
    main()
