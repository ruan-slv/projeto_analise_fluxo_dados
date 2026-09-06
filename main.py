import numpy as np
import pandas as pd
from connection import database_connection as conn

# Criando dados com NumPy
dados_array = np.array([[10, 20], [30, 40]])

# Criando uma tabela (DataFrame) com Pandas
df = pd.DataFrame(dados_array, columns=["Coluna A", "Coluna B"])

print("--- Meu primeiro DataFrame com Pandas e NumPy ---")

if not df.empty:
  print(df)
else:
  print("Nenhum dado encontrado.")

# Método para estabelecer uma conexão com o postgresql
conn(
  host="http://localhost:5432/",
  database="data_analitics",
  user="_etl_user___",
  password="_etl_password___"
)

print(conn)