from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text, URL
from datetime import datetime

DATABASE_URL = URL.create(
    "postgresql+psycopg2",
    username="dw_admin",
    password="DataWarehouse@2026!",
    host="localhost",
    port=5432,
    database="dw_analise_fluxo"
)

PRIMARY_KEYS = {
    "ddate": "DateID",
    "dtime": "TimeID",
    "ddepartment": "DepartmentID",
    "demployee": "EmployeeID",
    "dshift": "ShiftID",
    "djob_candidate": "JobCandidateID",
    "dpay_history": "PayHistoryID",
    "fhuman_resources": "FHumanResources"
}

def upsert_table(df: pd.DataFrame, table: str, engine) -> None:
    pk = PRIMARY_KEYS[table]
    cols = list(df.columns)
    col_names = ", ".join(cols)
    placeholders = ", ".join([f":{c}" for c in cols])
    updates = ", ".join([f"{c} = EXCLUDED.{c}" for c in cols if c != pk])

    query = text(f"""
        INSERT INTO {table} ({col_names})
        VALUES ({placeholders})
        ON CONFLICT ({pk}) DO UPDATE
        SET {updates}
    """)

    records = df.to_dict(orient="records")
    clean_records = [
        {k: (None if pd.isna(v) else v) for k, v in r.items()}
        for r in records
    ]

    with engine.begin() as conn:
        conn.execute(query, clean_records)

        if table == "fhuman_resources":
            conn.execute(text("SELECT setval('fhuman_resources_fhumanresources_seq', COALESCE((SELECT MAX(fhumanresources) FROM fhuman_resources), 1))"))

        conn.execute(
            text("INSERT INTO dw_metadata (table_name, last_load_date, records_processed) VALUES (:table, :date, :records)"),
            {"table": table, "date": datetime.now(), "records": len(df)}
        )

    print(f"{len(df)} registros processados em {table}")

def read_and_convert(csv: str, table: str, engine) -> None:
    try:
        data_directory = Path(__file__).resolve().parent.parent / "data/transformado"
        print(f"Carregando {csv} em {table}...")
        df = pd.read_csv(data_directory / csv)
        if not df.empty:
            upsert_table(df, table, engine)
        else:
            print(f"Nenhum registro novo para {table}")
    except Exception as e:
        print(f"Houve um problema durante o carregamento de {csv} -> {e}")

def load_tables() -> None:
    engine = create_engine(DATABASE_URL)

    data_map = [
        ("ddate.csv", "ddate"),
        ("dtime.csv", "dtime"),
        ("ddepartment.csv", "ddepartment"),
        ("demployee.csv", "demployee"),
        ("dshift.csv", "dshift"),
        ("djob_candidate.csv", "djob_candidate"),
        ("dpay_history.csv", "dpay_history"),
        ("fhuman_resources.csv", "fhuman_resources")
    ]

    for csv, table in data_map:
        read_and_convert(csv, table, engine)

if __name__ == "__main__":
    load_tables()
    print("Carga incremental concluída com sucesso!")
