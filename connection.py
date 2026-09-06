# Responsáveis pelos dados brutos 
import psycopg2

# Método para criar uma conexão com o banco de dados postgresql
def database_connection(host: str, database: str, user: str, password: str) -> bool:

  connection = psycopg2.connect(
    host      = host,
    database  = database,
    user      = user,
    password  = password
  )

  return connection