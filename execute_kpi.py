import sys
import re
from pathlib import Path
from sqlalchemy import create_engine, text, URL
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

DATABASE_URL = URL.create(
    "postgresql+psycopg2",
    username="dw_admin",
    password="DataWarehouse@2026!",
    host="localhost",
    port=5432,
    database="dw_analise_fluxo"
)

ARQUIVO_KPIS = Path(__file__).resolve().parent / "MapeamentoAdventureWorks" / "kpis.sql"

def carregar_kpis():
    """Carrega dinamicamente os KPIs do arquivo kpis.sql."""
    if not ARQUIVO_KPIS.exists():
        print(f"{RED}[ERRO] Arquivo não encontrado: {ARQUIVO_KPIS}{RESET}")
        sys.exit(1)

    conteudo = ARQUIVO_KPIS.read_text(encoding="utf-8")
    padrao = re.compile(
        r"--\s*KPI\s*(\d+):\s*(.+?)\n"
        r"--\s*Objetivo:\s*(.+?)\n"
        r"--\s*M[eé]trica:\s*(.+?)\n"
        r".*?\n"
        r"(SELECT[\s\S]*?;)",
        re.IGNORECASE
    )

    matches = padrao.findall(conteudo)
    kpis = {}
    for numero, titulo, objetivo, metrica, consulta in matches:
        num = int(numero)
        kpis[num] = {
            "numero": num,
            "titulo": titulo.strip(),
            "objetivo": objetivo.strip(),
            "metrica": metrica.strip(),
            "sql": consulta.strip()
        }
    return kpis


def get_engine():
    """Cria e testa a conexão SQLAlchemy com o banco de dados PostgreSQL."""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            pass
        return engine
    except Exception as e:
        print(f"\n{RED}[ERRO DE CONEXÃO] Não foi possível conectar ao Data Warehouse PostgreSQL:{RESET}")
        print(f"Host: localhost:5432 | Banco: dw_analise_fluxo")
        print(f"Detalhes: {e}")
        print(f"{YELLOW}Dica: Verifique se os contêineres Docker estão em execução (`python start_database.py`).{RESET}\n")
        return None


def executar_kpi(kpi_info, engine):
    """Executa e exibe o resultado de um KPI no terminal."""
    print(f"\n{CYAN}{'=' * 85}{RESET}")
    print(f"{BOLD}{GREEN}KPI {kpi_info['numero']}: {kpi_info['titulo']}{RESET}")
    print(f"{CYAN}{'=' * 85}{RESET}")
    print(f"{BOLD}🎯 Objetivo:{RESET} {kpi_info['objetivo']}")
    print(f"{BOLD}📊 Métrica:{RESET}  {kpi_info['metrica']}")
    print(f"{BLUE}--- Consulta SQL ---{RESET}")
    print(kpi_info['sql'])
    print(f"{CYAN}{'-' * 85}{RESET}")

    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(kpi_info['sql']), conn)

        print(f"\n{BOLD}📋 Resultado ({len(df)} registro(s)):{RESET}\n")
        
        if df.empty:
            print(f"{YELLOW}Nenhum registro retornado.{RESET}")
        else:
            with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", 1000):
                print(df.to_string(index=False))
    except Exception as e:
        print(f"{RED}[ERRO NA EXECUÇÃO]: {e}{RESET}")

    print(f"{CYAN}{'=' * 85}\n{RESET}")


def exibir_menu(kpis):
    """Exibe o menu de opções no terminal."""
    print(f"\n{BOLD}{CYAN}======================================================{RESET}")
    print(f"{BOLD}{GREEN}      PAINEL DE INDICADORES DE NEGÓCIO (KPIS)        {RESET}")
    print(f"{BOLD}{CYAN}======================================================{RESET}")
    for num in sorted(kpis.keys()):
        print(f"  {BOLD}{num:2d}{RESET} - {kpis[num]['titulo']}")
    print(f"  {BOLD}11{RESET} - {YELLOW}Executar TODOS os KPIs em sequência{RESET}")
    print(f"   {BOLD}0{RESET} - {RED}Sair{RESET}")
    print(f"{CYAN}------------------------------------------------------{RESET}")


def main():
    kpis = carregar_kpis()

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower().strip()
        engine = get_engine()
        if not engine:
            sys.exit(1)

        if arg in ("all", "11"):
            for num in sorted(kpis.keys()):
                executar_kpi(kpis[num], engine)
        elif arg.isdigit() and int(arg) in kpis:
            executar_kpi(kpis[int(arg)], engine)
        else:
            print(f"{RED}Opção inválida: {arg}. Escolha um número entre 1 e 10, ou 'all'.{RESET}")
        return

    engine = get_engine()
    if not engine:
        sys.exit(1)

    try:
        while True:
            exibir_menu(kpis)
            opcao = input(f"{BOLD}Escolha o KPI desejado (0-11): {RESET}").strip()

            if opcao == "0":
                print(f"\n{GREEN}Encerrando painel de KPIs. Até logo!{RESET}\n")
                break
            elif opcao == "11":
                for num in sorted(kpis.keys()):
                    executar_kpi(kpis[num], engine)
                input(f"{YELLOW}Pressione Enter para voltar ao menu...{RESET}")
            elif opcao.isdigit() and int(opcao) in kpis:
                executar_kpi(kpis[int(opcao)], engine)
                input(f"{YELLOW}Pressione Enter para voltar ao menu...{RESET}")
            else:
                print(f"\n{RED}[!] Opção inválida. Por favor, escolha um número de 0 a 11.{RESET}")
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n{YELLOW}Execução interrompida pelo usuário.{RESET}\n")


if __name__ == "__main__":
    main()
