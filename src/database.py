import os
import sqlite3
from pathlib import Path
from typing import Any, List, Tuple

from dotenv import load_dotenv

# Load env variables
load_dotenv()

DEFAULT_DB_PATH = Path(os.getenv("DB_PATH", "data/db/nifty100.db"))


class DatabaseManager:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        # Ensure parent directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Returns a connection with foreign key support enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enforce foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize_schema(
        self,
        schema_sql_path: Path = (
            Path(__file__).resolve().parents[1] / "db" / "schema.sql"
        ),
    ) -> None:
        """Reads schema.sql and runs it against the database."""
        if not schema_sql_path.is_file():
            raise FileNotFoundError(f"Schema file not found at: {schema_sql_path}")

        with open(schema_sql_path, "r", encoding="utf-8") as f:
            schema_script = f.read()

        conn = self.get_connection()
        try:
            conn.executescript(schema_script)
            conn.commit()
        finally:
            conn.close()

    def run_fk_check(self) -> List[Tuple[Any, ...]]:
        """Runs the foreign key constraint check.

        Returns a list of foreign key violations. If list is empty,
        FK constraints are clean (0).
        """
        conn = self.get_connection()
        try:
            # PRAGMA returns (table, rowid, parent_table, fkid) for violations
            cursor = conn.execute("PRAGMA foreign_key_check;")
            violations = cursor.fetchall()
            return [tuple(row) for row in violations]
        finally:
            conn.close()

    def execute_query(
        self, query: str, params: Tuple[Any, ...] = ()
    ) -> List[sqlite3.Row]:
        """Runs a SELECT query and returns Rows."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def execute_update(self, query: str, params: Tuple[Any, ...] = ()) -> int:
        """Runs an INSERT, UPDATE, or DELETE query and returns rowcount."""
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def execute_many(self, query: str, param_list: List[Tuple[Any, ...]]) -> int:
        """Runs an executemany query and commits transaction."""
        conn = self.get_connection()
        try:
            cursor = conn.executemany(query, param_list)
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
