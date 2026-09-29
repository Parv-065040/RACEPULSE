"""
Simple migration runner - Parv's ownership (database/migrations/).

Applies any .sql file in this folder that hasn't been applied yet,
in filename order (hence the 001_, 002_, 003_ prefixes), and records
each one in a schema_migrations table so re-running this script is
safe and only applies what's new.

This replaces manually re-running the whole schema.sql dump every
time a table is added - each change is now a small, named, ordered file.

Run with: python -m database.migrations.run_migrations
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from database.connection import get_connection  # noqa: E402

MIGRATIONS_DIR = os.path.dirname(os.path.abspath(__file__))


def _ensure_migrations_table(conn) -> None:
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def _already_applied(conn) -> set[str]:
    with conn.cursor() as cursor:
        cursor.execute("SELECT filename FROM schema_migrations")
        return {row[0] for row in cursor.fetchall()}


def _apply_migration(conn, filename: str) -> None:
    path = os.path.join(MIGRATIONS_DIR, filename)
    with open(path, "r", encoding="utf-8-sig") as f:
        sql = f.read()

    with conn.cursor() as cursor:
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        cursor.execute("INSERT INTO schema_migrations (filename) VALUES (%s)", (filename,))
    print(f"Applied: {filename}")


def run_migrations() -> None:
    conn = get_connection()
    _ensure_migrations_table(conn)
    applied = _already_applied(conn)

    migration_files = sorted(
        f for f in os.listdir(MIGRATIONS_DIR)
        if f.endswith(".sql")
    )

    pending = [f for f in migration_files if f not in applied]

    if not pending:
        print("No pending migrations - schema is up to date.")
        return

    for filename in pending:
        _apply_migration(conn, filename)

    print(f"Applied {len(pending)} migration(s).")


if __name__ == "__main__":
    run_migrations()
