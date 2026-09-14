# Responsáveis pelos dados brutos 
import psycopg2

def database_connection(host: str, database: str, user: str, password: str) -> bool:

  connection = psycopg2.connect(
    host      = host,
    database  = database,
    user      = user,
    password  = password
  )

  return connection