# -*- coding: utf-8 -*-
"""
Conexão com o PostgreSQL (fonte OLTP + destino DW).

Como o ambiente pode apontar para instâncias diferentes (a fonte AdventureWorks
e o DW), usamos DSNs configuráveis por variável de ambiente:
    AW_DSN  -> fonte OLTP  (AdventureWorks)
    DW_DSN  -> destino DW  (dw_adventureworks)
    (ou um único PG_DSN para as duas, caso sejam o mesmo servidor)

Formato esperado: host=... port=... user=... dbname=...
Ex.: host=127.0.0.1 port=5433 user=postgres dbname=adventureworks
"""
import os
import psycopg2
import psycopg2.extras

# DSN padrão: a instância local criada para o projeto (trust, porta 5433).
_DEFAULT = "host=127.0.0.1 port=5433 user=postgres dbname=postgres"


def _load_env():
    """Carrega o arquivo .env (raiz do projeto) se existir. Sem dependências:
    apenas KEY=VALUE por linha (variáveis já definidas no ambiente têm prioridade)."""
    env_path = os.path.join(os.path.dirname(__file__), os.pardir, ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_env()


def _dsn(env_key: str, fallback_db: str) -> str:
    raw = os.environ.get(env_key)
    if raw:
        return raw
    # usa o servidor padrão, trocando apenas o dbname
    return _DEFAULT.replace("dbname=postgres", f"dbname={fallback_db}")

def connect_source():
    """Conecta na fonte OLTP (AdventureWorks)."""
    return psycopg2.connect(_dsn("AW_DSN", "adventureworks"))

def connect_dw():
    """Conecta no destino DW (dw_adventureworks)."""
    return psycopg2.connect(_dsn("DW_DSN", "dw_adventureworks"))

def connect(dsn: str):
    return psycopg2.connect(dsn)

# Cursor nomeado (rows como dict) — facilita o ETL.
def named_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
