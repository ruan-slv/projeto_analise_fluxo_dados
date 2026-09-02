# -*- coding: utf-8 -*-
"""
ETL INCREMENTAL — núcleo do pipeline (OLTP AdventureWorks -> DW PostgreSQL).

Estratégia incremental
----------------------
Cada tabela de origem (OLTP) possui a coluna `modifieddate`. O pipeline guarda,
para cada tabela, um *watermark* (o maior `modifieddate` já processado) na
tabela `dw.etl_watermark`. Na execução:

    1. Lê o watermark (0 na primeira vez -> carga inicial completa).
    2. Seleciona apenas as linhas com `modifieddate >= watermark`.
       (usa `>=` e não `>` porque existem *ties* no timestamp: várias linhas
        podem ter o MESMO modifieddate; com `>=` + UPSERT a carga fica
        IDEMPOTENTE e nenhuma alteração é perdida.)
    3. Grava as linhas no destino via UPSERT (INSERT ... ON CONFLICT DO UPDATE),
       garantindo que reprocessar o mesmo intervalo não crie duplicatas.
    4. Atualiza o watermark para o maior modifieddate encontrado.

Custo: em vez de ler N linhas a cada execução, lemos apenas o delta
(O(delta) vs O(N)), o que é o requisito obrigatório de ETL incremental.
"""
import time
import datetime as dt
import psycopg2
import psycopg2.extras
from psycopg2.extras import execute_values
from . import db

# ---------------------------------------------------------------------------
#  Watermarks
# ---------------------------------------------------------------------------
def get_watermark(cur, table_oltp: str):
    """Retorna o maior modifieddate já processado (ou epoch 0 se nunca)."""
    cur.execute(
        "SELECT last_modified FROM dw.etl_watermark WHERE tabela_oltp=%s",
        (table_oltp,),
    )
    row = cur.fetchone()
    if row is None:
        return dt.datetime(1900, 1, 1)
    return row["last_modified"]


def set_watermark(cur, table_oltp: str, last_modified, rows_loaded: int):
    """Insere/atualiza o watermark da tabela (idempotente)."""
    cur.execute(
        """
        INSERT INTO dw.etl_watermark (tabela_oltp, last_modified, last_run, rows_loaded)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (tabela_oltp) DO UPDATE
        SET last_modified = EXCLUDED.last_modified,
            last_run      = EXCLUDED.last_run,
            rows_loaded   = EXCLUDED.rows_loaded
        """,
        (table_oltp, last_modified, dt.datetime.now(), rows_loaded),
    )


# ---------------------------------------------------------------------------
#  UPSERT genérico
#  - `pk`  : coluna(s) de conflito (chave natural no destino)
#  - `cols`: lista de colunas do destino (mesma ordem dos valores)
# ---------------------------------------------------------------------------
def upsert(conn, table: str, pk: list, cols: list, rows: list, page_size: int = 2000):
    """
    UPSERT em lote (INSERT ... ON CONFLICT DO UPDATE).

    Performance: em vez de `executemany` (1 round-trip POR LINHA, O(n) queries),
    usa `execute_values` que monta UMA query com N tuplas por página
    (N/page_size round-trips). Para o fato (121k linhas) isso é ~100x mais
    rápido, mantendo a idempotência via ON CONFLICT.
    """
    if not rows:
        return 0
    col_list = ", ".join(cols)
    # atualiza TODAS as colunas exceto as de conflito (PK)
    update_cols = [c for c in cols if c not in pk]
    update_set = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
    sql = (
        f"INSERT INTO {table} ({col_list}) VALUES %s "
        f"ON CONFLICT ({', '.join(pk)}) DO UPDATE SET {update_set}"
    )
    cur = conn.cursor()
    execute_values(cur, sql, rows, page_size=page_size)
    conn.commit()
    return len(rows)


# ---------------------------------------------------------------------------
#  Seleção incremental da fonte
# ---------------------------------------------------------------------------
def fetch_delta(conn, query: str, watermark: dt.datetime, param_extra=None):
    """
    Executa `query` (que já contém o filtro `WHERE modifieddate >= %s`).
    Retorna (rows, max_modified). `rows` é lista de dicts.
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = [watermark]
    if param_extra:
        params = param_extra + [watermark]
    cur.execute(query, params)
    rows = cur.fetchall()
    return rows


def max_modified(rows, key="modifieddate"):
    """Maior modifieddate entre as linhas (para atualizar o watermark)."""
    vals = [r[key] for r in rows if r.get(key) is not None]
    return max(vals) if vals else None
