import subprocess
import time
import sys

# Configurações de cores para o terminal (funciona no Windows, Linux e Mac)
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
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
    run_command("docker build -t sql-analise-fluxo .", "Passo 1: Construindo a imagem Docker (sql-analise-fluxo)")

    # Passo 2: Limpar container antigo (ignora erros se o container não existir)
    print(f"{GREEN}==> Passo 2: Limpando container antigo (se houver)...{NC}")
    subprocess.run("docker rm -f db_fluxo", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Passo 3: Subir o novo container
    run_command(
        'docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=AnaliseDados@2026!" -p 1433:1433 --name db_fluxo -d sql-analise-fluxo',
        "Passo 3: Subindo o novo container (db_fluxo)"
    )

    # Passo 4: Aguardar o SQL Server inicializar
    print(f"{YELLOW}==> Passo 4: Aguardando o motor do SQL Server inicializar (25 segundos)...{NC}")
    time.sleep(25)

    # Passo 5: Restaurar o banco de dados (Query formatada em uma linha para evitar problemas de escape)
    restore_query = (
        "RESTORE DATABASE AdventureWorksDW FROM DISK = '/var/opt/mssql/backup/AdventureWorksDW2025.bak' "
        "WITH REPLACE, "
        "MOVE 'AdventureWorksDW' TO '/var/opt/mssql/data/AdventureWorksDW.mdf', "
        "MOVE 'AdventureWorksDW_log' TO '/var/opt/mssql/data/AdventureWorksDW_log.ldf'"
    )

    restore_command = f'docker exec -i db_fluxo /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "AnaliseDados@2026!" -C -Q "{restore_query}"'

    run_command(restore_command, "Passo 5: Restaurando o banco de dados AdventureWorks")

    print(f"{GREEN}==> Automação finalizada! O banco está pronto e seguro para conexões em localhost:1433.{NC}")

if __name__ == "__main__":
    main()
