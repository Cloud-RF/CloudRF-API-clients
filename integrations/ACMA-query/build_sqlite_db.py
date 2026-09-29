#!/usr/bin/env python3
"""
Build an SQLite database from the ACMA "Spectra RRL" CSV extract, using the
table/column definitions in DOC/cr_tables_oracle.sql (translated from Oracle
DDL to SQLite) as the schema.

Usage:
    python3 build_sqlite_db.py [--out spectra_rrl.db] [--chunk-size 20000]

Run from anywhere — paths below are resolved relative to this script, not
the current working directory. This script lives in map_app/ (so its
default output, spectra_rrl.db, lands right next to the Flask app that
reads it — see search.py), but its *source* data (the raw CSVs and
DOC/cr_tables_oracle.sql) lives one level up in ../spectra_rrl/, as
distributed by ACMA.

The script:
  1. Parses DOC/cr_tables_oracle.sql to get table names + column names/types.
  2. Translates Oracle types (VARCHAR2/NUMBER/DATE/CLOB/CHAR) to SQLite
     type affinities (TEXT/NUMERIC).
  3. Creates the tables in a fresh SQLite database.
  4. Bulk-loads each <table>.csv (header row gives column order; empty
     fields become NULL) into its matching table.
  5. Adds a handful of indexes on common id/key columns to make the
     resulting database practical to query.
"""
import argparse
import csv
import re
import sqlite3
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = SCRIPT_DIR.parent / "spectra_rrl"  # raw ACMA CSVs + DOC/, as distributed
SQL_SCHEMA_PATH = SOURCE_DIR / "DOC" / "cr_tables_oracle.sql"

# The source DDL is missing a comma between BSL_NO and AWL_TYPE in the
# `licence` table (confirmed against licence.csv, which has 16 columns).
# Patch it before parsing so every column is picked up correctly.
KNOWN_DDL_FIXES = [
    (
        " BSL_NO                 VARCHAR2(31)\n AWL_TYPE",
        " BSL_NO                 VARCHAR2(31),\n AWL_TYPE",
    ),
]

# csv row fields are all read as text; empty string -> NULL for every column,
# regardless of declared type (that's how the Oracle export represents NULLs).


def oracle_type_to_sqlite(oracle_type: str) -> str:
    t = oracle_type.strip().upper()
    if t.startswith("NUMBER"):
        return "NUMERIC"
    if t.startswith("VARCHAR2") or t.startswith("CHAR"):
        return "TEXT"
    if t.startswith("DATE"):
        return "TEXT"  # ISO 'YYYY-MM-DD' strings in the CSVs
    if t.startswith("CLOB"):
        return "TEXT"
    return "TEXT"


def split_top_level(body: str):
    """Split a comma-separated column-def list, ignoring commas inside parens."""
    parts = []
    depth = 0
    current = []
    for ch in body:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def parse_schema(sql_text: str):
    """Return an ordered list of (table_name, [(col_name, sqlite_type), ...])."""
    for old, new in KNOWN_DDL_FIXES:
        if old not in sql_text:
            raise RuntimeError(
                "Expected DDL text to patch was not found — schema file may "
                "have changed; check KNOWN_DDL_FIXES."
            )
        sql_text = sql_text.replace(old, new)

    tables = []
    pattern = re.compile(r"create table\s+(\w+)\s*\((.*?)\)\s*;", re.IGNORECASE | re.DOTALL)
    for match in pattern.finditer(sql_text):
        table_name = match.group(1).lower()
        body = match.group(2)
        columns = []
        for col_def in split_top_level(body):
            tokens = col_def.split(None, 1)
            if len(tokens) != 2:
                raise RuntimeError(f"Could not parse column definition: {col_def!r}")
            col_name, col_type = tokens
            columns.append((col_name.lower(), oracle_type_to_sqlite(col_type)))
        tables.append((table_name, columns))
    return tables


# Non-unique indexes on common id/key columns, to make the database
# practical to query/join without assuming primary-key uniqueness (the
# source DDL declares none, and the CSV export may contain duplicates).
INDEXES = {
    "licence": ["licence_no", "client_no", "bsl_no"],
    "client": ["client_no"],
    "site": ["site_id"],
    "antenna": ["antenna_id"],
    "antenna_pattern": ["antenna_id"],
    "device_details": ["licence_no", "site_id", "antenna_id", "sa_id"],
    "auth_spectrum_area": ["licence_no"],
    "auth_spectrum_freq": ["licence_no"],
    "applic_text_block": ["licence_no"],
    "bsl": ["bsl_no"],
    "bsl_area": ["area_code"],
    "access_area": ["area_id", "area_code"],
    "satellite": ["sa_id"],
}


def build_database(out_path: Path, chunk_size: int):
    sql_text = SQL_SCHEMA_PATH.read_text(encoding="utf-8")
    tables = parse_schema(sql_text)

    if out_path.exists():
        out_path.unlink()

    conn = sqlite3.connect(out_path)
    conn.execute("PRAGMA journal_mode = MEMORY")
    conn.execute("PRAGMA synchronous = OFF")
    cur = conn.cursor()

    print(f"Schema: {len(tables)} tables parsed from {SQL_SCHEMA_PATH.name}")

    for table_name, columns in tables:
        col_defs = ", ".join(f'"{name}" {sqltype}' for name, sqltype in columns)
        cur.execute(f'CREATE TABLE "{table_name}" ({col_defs})')
    conn.commit()

    total_rows = 0
    t0 = time.time()
    for table_name, columns in tables:
        csv_path = SOURCE_DIR / f"{table_name}.csv"
        if not csv_path.exists():
            print(f"  [skip] {table_name}: no CSV file found at {csv_path.name}")
            continue

        schema_cols = {name for name, _ in columns}

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = [h.strip().lower() for h in next(reader)]

            unknown = [h for h in header if h not in schema_cols]
            if unknown:
                raise RuntimeError(
                    f"{csv_path.name}: CSV has columns not in schema: {unknown}"
                )

            placeholders = ", ".join("?" for _ in header)
            col_list = ", ".join(f'"{h}"' for h in header)
            insert_sql = f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})'

            row_count = 0
            chunk = []
            cur.execute("BEGIN")
            for row in reader:
                chunk.append([v if v != "" else None for v in row])
                if len(chunk) >= chunk_size:
                    cur.executemany(insert_sql, chunk)
                    row_count += len(chunk)
                    chunk = []
            if chunk:
                cur.executemany(insert_sql, chunk)
                row_count += len(chunk)
            conn.commit()

        total_rows += row_count
        print(f"  [ok]   {table_name}: {row_count:,} rows")

    elapsed = time.time() - t0
    print(f"Inserted {total_rows:,} rows total in {elapsed:.1f}s")

    print("Building indexes...")
    t1 = time.time()
    for table_name, cols in INDEXES.items():
        for col in cols:
            idx_name = f"idx_{table_name}_{col}"
            cur.execute(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{table_name}" ("{col}")')
    conn.commit()
    print(f"Indexes built in {time.time() - t1:.1f}s")

    cur.execute("PRAGMA optimize")
    conn.execute("VACUUM")
    conn.close()
    print(f"Done -> {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", default=str(SCRIPT_DIR / "spectra_rrl.db"),
        help="Output SQLite file path (default: spectra_rrl.db next to this script)",
    )
    parser.add_argument(
        "--chunk-size", type=int, default=20000,
        help="Rows per executemany batch (default: 20000)",
    )
    args = parser.parse_args()
    build_database(Path(args.out), args.chunk_size)


if __name__ == "__main__":
    sys.exit(main())
