from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_CONNECTION = "postgresql+psycopg2://dw_admin:DataWarehouse@2026!@localhost:5432/dw_analise_fluxo"

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

    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(query, row.to_dict())
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
        print(f"Houve um problema durante o carregamento de {csv} → {e}")

def load_tables() -> None:
    engine = create_engine(DATABASE_CONNECTION)

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
