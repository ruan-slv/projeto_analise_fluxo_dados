# Importa Path para manipular caminhos de arquivos de forma independente do sistema operacional.
from pathlib import Path

# Importa o Pandas para executar consultas e salvar os resultados em CSV.
import pandas as pd
# Importa o pyodbc para conectar ao SQL Server por meio do driver ODBC.
import pyodbc


# Armazena os parâmetros usados para conectar ao banco AdventureWorks.
STRING_CONEXAO = (
    # Informa o driver ODBC utilizado pelo SQL Server.
    "Driver={ODBC Driver 18 for SQL Server};"
    # Define o servidor e a porta onde o SQL Server está disponível.
    "Server=localhost,1433;"
    # Define o nome do banco de dados de origem.
    "Database=AdventureWorks;"
    # Define o usuário usado na autenticação do banco.
    "UID=sa;"
    # Define a senha usada na autenticação do banco.
    "PWD=AnaliseDados@2026!;"
    # Permite a conexão mesmo quando o certificado do servidor não é validado.
    "TrustServerCertificate=yes;"
)

# Relaciona cada tabela de origem ao nome do CSV e à consulta que será executada.
TABELAS = {
    # Extrai a tabela de departamentos para department.csv.
    "HumanResources.Department": (
        "department.csv",
        "select * from HumanResources.Department",
    ),
    # Extrai os funcionários para employee.csv.
    "HumanResources.Employee": (
        "employee.csv",
        # Converte hierarchyid para texto, pois o pyodbc não lê esse tipo diretamente.
        """
        select BusinessEntityID, NationalIDNumber, LoginID,
               OrganizationNode.ToString() AS OrganizationNode,
               OrganizationLevel, JobTitle, BirthDate, MaritalStatus,
               Gender, HireDate, SalariedFlag, VacationHours,
               SickLeaveHours, CurrentFlag, rowguid, ModifiedDate
        from HumanResources.Employee
        """,
    ),
    # Extrai o histórico de departamentos dos funcionários.
    "HumanResources.EmployeeDepartmentHistory": (
        "employee_department_history.csv",
        "select * from HumanResources.EmployeeDepartmentHistory",
    ),
    # Extrai o histórico de pagamentos dos funcionários.
    "HumanResources.EmployeePayHistory": (
        "employee_pay_history.csv",
        "select * from HumanResources.EmployeePayHistory",
    ),
    # Extrai os candidatos às vagas.
    "HumanResources.JobCandidate": (
        "job_candidate.csv",
        "select * from HumanResources.JobCandidate",
    ),
    # Extrai os turnos de trabalho.
    "HumanResources.Shift": (
        "shift.csv",
        "select * from HumanResources.Shift",
    )
}


# Define a função responsável por extrair todas as tabelas configuradas.
def extrair_tabelas() -> None:
    # Calcula o caminho da pasta data a partir da localização deste script.
    pasta_data = Path(__file__).resolve().parent.parent / "data"
    # Cria a pasta data caso ela ainda não exista.
    pasta_data.mkdir(exist_ok=True)

    # Informa no terminal que a conexão será iniciada.
    print("Conectando ao SQL Server...")
    # Abre a conexão e garante seu fechamento ao final do bloco.
    with pyodbc.connect(STRING_CONEXAO) as conexao:
        # Percorre o nome, o arquivo de saída e a consulta de cada tabela.
        for tabela, (nome_arquivo, consulta) in TABELAS.items():
            # Informa qual tabela está sendo processada.
            print(f"Extraindo {tabela}...")
            # Executa a consulta e armazena o resultado em um DataFrame.
            df = pd.read_sql(consulta, conexao)
            # Monta o caminho completo do arquivo CSV de saída.
            caminho_saida = pasta_data / nome_arquivo
            # Grava o DataFrame no CSV sem incluir o índice do Pandas.
            df.to_csv(caminho_saida, index=False, encoding="utf-8")
            # Informa quantos registros foram gravados e onde o arquivo está.
            print(f"{len(df)} registros gravados em {caminho_saida}")


# Verifica se este arquivo foi executado diretamente, e não importado por outro módulo.
if __name__ == "__main__":
    try:
        # Executa a extração das tabelas.
        extrair_tabelas()
        # Informa que todas as extrações terminaram com sucesso.
        print("Extração concluída com sucesso!")
    except Exception as erro:
        # Exibe a mensagem do erro ocorrido durante a conexão ou extração.
        print(f"Erro na conexão ou na extração: {erro}")
        # Relança o erro para preservar o código de falha da execução.
        raise