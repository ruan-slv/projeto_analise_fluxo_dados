#!/usr/bin/env bash
# ============================================================================
#  setup.sh — reproduz o ambiente do projeto (fonte OLTP + DW + ETL)
#
#  O que faz:
#    1. Garante uma instância PostgreSQL (usa a local em ~/pgsql-local, porta 5433).
#    2. Restaura a fonte AdventureWorks 2016 (dump PostgreSQL).
#    3. Cria o banco do DW e aplica o schema estrela + dim_data.
#    4. Roda o pipeline ETL (carga inicial) e o teste incremental.
#
#  Uso:  ./setup.sh
#  Obs.: se você já tem um PostgreSQL com a AdventureWorks, pule o passo 1/2
#        e ajuste o .env (AW_DSN/DW_DSN) para o seu servidor.
# ============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PG="${PG:-$HOME/pgsql-local/usr/lib/postgresql/17}"
PORT="${PORT:-5433}"
SOCK="/tmp"
PY="./.venv/bin/python"

echo "==> [1/4] Instância PostgreSQL"
if [ ! -x "$PG/bin/pg_ctl" ]; then
  echo "    Baixando e extraindo PostgreSQL 17 (Debian .deb) em ~/pgsql-local ..."
  mkdir -p /tmp/pgdeb ~/pgsql-local
  cd /tmp/pgdeb
  apt-get download postgresql-17 postgresql-client-17 >/dev/null 2>&1 || {
    echo "    Falha no apt-get download. Instale: sudo apt-get install postgresql-17"; exit 1; }
  dpkg-deb -x postgresql-17*.deb ~/pgsql-local
  dpkg-deb -x postgresql-client-17*.deb ~/pgsql-local
  cd - >/dev/null
fi
# sobe a instância se não estiver no ar
if ! "$PG/bin/pg_ctl" -D ~/pgsql-data status >/dev/null 2>&1; then
  [ -d ~/pgsql-data ] || "$PG/bin/initdb" -D ~/pgsql-data -U postgres --auth=trust -E UTF8 --locale=C.UTF-8
  "$PG/bin/pg_ctl" -D ~/pgsql-data -l /tmp/pg.log -o "-p $PORT -k $SOCK" start
  sleep 1
fi
echo "    PostgreSQL no ar (porta $PORT)."

PSQL="$PG/bin/psql -h $SOCK -p $PORT -U postgres"

echo "==> [2/4] Fonte AdventureWorks 2016 (dump PostgreSQL)"
if ! $PSQL -d adventureworks -tAc "SELECT 1" >/dev/null 2>&1; then
  [ -f /tmp/AdventureWorksPG.gz ] || curl -sL -o /tmp/AdventureWorksPG.gz \
    https://github.com/timchapman/postgresql-adventureworks/raw/main/AdventureWorksPG.gz
  $PSQL -c "CREATE DATABASE adventureworks;"
  $PSQL -d adventureworks -c 'CREATE EXTENSION IF NOT EXISTS tablefunc;' \
                    -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
  $PG/bin/pg_restore -h $SOCK -p $PORT -U postgres -d adventureworks --no-owner /tmp/AdventureWorksPG.gz 2>/dev/null || true
  echo "    Fonte restaurada."
else
  echo "    Fonte já existe."
fi

echo "==> [3/4] Data Warehouse (schema estrela + dim_data)"
$PSQL -tAc "SELECT 1 FROM pg_database WHERE datname='dw_adventureworks'" | grep -q 1 || \
  $PSQL -c "CREATE DATABASE dw_adventureworks;"
$PSQL -d dw_adventureworks -v ON_ERROR_STOP=1 -f etl/schema_dw.sql >/dev/null
$PSQL -d dw_adventureworks -v ON_ERROR_STOP=1 -f etl/seed_dim_data.sql >/dev/null
echo "    Schema DW aplicado."

echo "==> [4/4] Pipeline ETL (carga inicial) + teste incremental"
$PY -m etl.pipeline --reset
$PY -m etl.test_incremental

echo ""
echo "✅ Setup concluído."
echo "   KPIs:  $PG/bin/psql -h $SOCK -p $PORT -U postgres -d dw_adventureworks -f kpis.sql"
