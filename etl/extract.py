import pyodbc
import pandas as pd

# String de conexão configurada com os dados do seu comando bash
string_conexao = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost,1433;"
    "Database=AdventureWorks;"
    "UID=sa;"
    "PWD=AnaliseDados@2026!;"
    "TrustServerCertificate=yes;"
)

try:
    print("Conectando ao SQL Server...")
    # Estabelece a conexão com o banco
    conexao = pyodbc.connect(string_conexao)

    # Query de teste (pegando os 5 primeiros registros da tabela Person do AdventureWorks)
    query = "SELECT * FROM HumanResources.Department"

    print("Executando a consulta e carregando os dados no Pandas...")
    # O read_sql já faz a extração e transforma em DataFrame
    df = pd.read_sql(query, conexao)

    print("Extração concluída com sucesso!\n")
    print(df)

except Exception as e:
    print(f"Erro na conexão ou na extração: {e}")

finally:
    # Garante que a conexão seja fechada mesmo se houver erro
    if 'conexao' in locals():
        conexao.close()
