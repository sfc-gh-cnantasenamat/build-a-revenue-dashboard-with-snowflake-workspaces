"""Create demo objects and load synthetic CSVs into your account. Refuses other accounts."""

import json
from pathlib import Path

import snowflake.connector

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/demo.json").read_text())
FQ = f'{CONFIG["database"]}.{CONFIG["schema"]}'


def run_file(cursor, path):
    for statement in path.read_text().split(";\n"):
        if statement.strip():
            cursor.execute(statement)


def main():
    with snowflake.connector.connect(connection_name=CONFIG["connection"]) as connection:
        cursor = connection.cursor()
        org, account = cursor.execute("SELECT CURRENT_ORGANIZATION_NAME(), CURRENT_ACCOUNT_NAME()").fetchone()
        if (org, account) != (CONFIG["expected_organization"], CONFIG["expected_account"]):
            raise SystemExit(f"Refusing to deploy to {org}.{account}")
        cursor.execute(f'USE WAREHOUSE {CONFIG["warehouse"]}')
        run_file(cursor, ROOT / "sql/01_setup.sql")
        for table in ("CUSTOMERS", "PRODUCTS", "REVENUE_MONTHLY"):
            csv = ROOT / "data" / f"{table.lower()}.csv"
            cursor.execute(f"PUT 'file://{csv}' @{FQ}.LOAD_STAGE/{table.lower()}/ OVERWRITE=TRUE AUTO_COMPRESS=TRUE")
            columns = [row[0] for row in cursor.execute(f"DESCRIBE TABLE {FQ}.{table}").fetchall()]
            header = csv.read_text().splitlines()[0].upper().split(",")
            positions = ", ".join(f"${header.index(column) + 1}" for column in columns)
            cursor.execute(f"TRUNCATE TABLE {FQ}.{table}")
            cursor.execute(f"COPY INTO {FQ}.{table} FROM (SELECT {positions} FROM @{FQ}.LOAD_STAGE/{table.lower()}/) "
                           "FORCE = TRUE ON_ERROR = ABORT_STATEMENT")
            count = cursor.execute(f"SELECT COUNT(*) FROM {FQ}.{table}").fetchone()[0]
            print(f"{table}: {count:,} rows")
        run_file(cursor, ROOT / "sql/02_semantic_view.sql")
        print(f'Semantic view {FQ}.{CONFIG["semantic_view"]} created')


if __name__ == "__main__":
    main()
