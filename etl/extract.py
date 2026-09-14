from pathlib import Path
import pandas as pd
import pyodbc
import psycopg2

STRING_CONEXAO = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost,1433;"
    "Database=AdventureWorks;"
    "UID=sa;"
    "PWD=AnaliseDados@2026!;"
    "TrustServerCertificate=yes;"
)

TABELAS = {
    "HumanResources.Department": (
        "department.csv",
        "select * from HumanResources.Department",
    ),
    "HumanResources.Employee": (
        "employee.csv",
        """
        select BusinessEntityID, NationalIDNumber, LoginID,
               OrganizationNode.ToString() AS OrganizationNode,
               OrganizationLevel, JobTitle, BirthDate, MaritalStatus,
               Gender, HireDate, SalariedFlag, VacationHours,
               SickLeaveHours, CurrentFlag, rowguid, ModifiedDate
        from HumanResources.Employee
        """,
    ),
    "HumanResources.EmployeeDepartmentHistory": (
        "employee_department_history.csv",
        "select * from HumanResources.EmployeeDepartmentHistory",
    ),
    "HumanResources.EmployeePayHistory": (
        "employee_pay_history.csv",
        "select * from HumanResources.EmployeePayHistory",
    ),
    "HumanResources.JobCandidate": (
        "job_candidate.csv",
        "select * from HumanResources.JobCandidate",
    ),
    "HumanResources.Shift": (
        "shift.csv",
        "select * from HumanResources.Shift",
    )
}

def obter_last_load_date(table_name: str):
    conn = psycopg2.connect(
        host="localhost",
        database="dw_analise_fluxo",
        port="5432",
        user="dw_admin",
        password="DataWarehouse@2026!"
    )
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(MAX(last_load_date), '2000-01-01'::timestamp) FROM dw_metadata WHERE table_name IN (%s, %s)",
        (table_name, f"d{table_name}")
    )
    last_date = cur.fetchone()[0]
    conn.close()
    return last_date

def extrair_tabelas() -> None:
    pasta_data = Path(__file__).resolve().parent.parent / "data/bruto"
    pasta_data.mkdir(exist_ok=True)

    print("Conectando ao SQL Server...")
    with pyodbc.connect(STRING_CONEXAO) as conexao:
        for tabela, (nome_arquivo, consulta) in TABELAS.items():
            print(f"Extraindo {tabela}...")

            if "ModifiedDate" in consulta:
                last_date = obter_last_load_date(nome_arquivo.replace(".csv", ""))
                consulta = consulta.strip() + f" WHERE ModifiedDate > '{last_date}'"

            df = pd.read_sql(consulta, conexao)
            caminho_saida = pasta_data / nome_arquivo
            df.to_csv(caminho_saida, index=False, encoding="utf-8")
            print(f"{len(df)} registros gravados em {caminho_saida}")

if __name__ == "__main__":
    try:
        extrair_tabelas()
        print("Extração incremental concluída com sucesso!")
    except Exception as erro:
        print(f"Erro na conexão ou na extração: {erro}")
        raise
