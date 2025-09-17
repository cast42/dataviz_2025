from pathlib import Path

import duckdb


def _quote_identifier(name: str) -> str:
    """Return a DuckDB-safe identifier."""
    return f'"{name.replace('"', '""')}"'


def _quote_literal(value: str) -> str:
    """Return a DuckDB-safe string literal."""
    return f"'{value.replace("'", "''")}'"


def main() -> None:
    project_root = Path(__file__).resolve().parent
    parquet_path = project_root / "data" / "sales_stores_hierarchy_merged.parquet"

    if not parquet_path.exists():
        msg = f"Expected parquet file at {parquet_path}, but it was not found."
        raise FileNotFoundError(msg)

    connection = duckdb.connect()

    table_name = parquet_path.stem
    connection.execute(
        f"CREATE OR REPLACE TEMP VIEW {_quote_identifier(table_name)} AS "
        f"SELECT * FROM read_parquet({_quote_literal(str(parquet_path))})"
    )

    tables = [row[0] for row in connection.execute("SHOW TABLES").fetchall()]

    if not tables:
        print("No tables found in the DuckDB connection.")
        return

    print("Tables:")
    for table in tables:
        print(f"- {table}")
        description = connection.execute(
            f"DESCRIBE {_quote_identifier(table)}"
        ).fetchall()
        for column_name, column_type, *_ in description:
            print(f"    {column_name}: {column_type}")


if __name__ == "__main__":
    main()
