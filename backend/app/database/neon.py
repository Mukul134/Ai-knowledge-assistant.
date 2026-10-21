import json
import os
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row


class QueryResult:
    def __init__(self, data: list[dict[str, Any]]):
        self.data = data


class TableQuery:
    def __init__(self, table: str):
        self.table = table
        self.operation = "select"
        self.payload: dict[str, Any] | list[dict[str, Any]] | None = None
        self.filters: list[tuple[str, Any]] = []
        self.ordering: tuple[str, bool] | None = None

    def select(self, _columns: str = "*"):
        self.operation = "select"
        return self

    def insert(self, payload):
        self.operation, self.payload = "insert", payload
        return self

    def update(self, payload):
        self.operation, self.payload = "update", payload
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, column: str, value: Any):
        self.filters.append((column, value))
        return self

    def order(self, column: str, desc: bool = False):
        self.ordering = (column, desc)
        return self

    def execute(self) -> QueryResult:
        params: list[Any] = []
        where = ""
        if self.filters:
            where = " WHERE " + " AND ".join(f'"{column}" = %s' for column, _ in self.filters)
            params.extend(value for _, value in self.filters)
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                if self.operation == "select":
                    order = ""
                    if self.ordering:
                        column, desc = self.ordering
                        order = f' ORDER BY "{column}" {"DESC" if desc else "ASC"}'
                    cursor.execute(f'SELECT * FROM "{self.table}"{where}{order}', params)
                    return QueryResult(list(cursor.fetchall()))
                if self.operation == "insert":
                    rows = self.payload if isinstance(self.payload, list) else [self.payload]
                    columns = list(rows[0])
                    values = [[row[column] for column in columns] for row in rows]
                    quoted = ", ".join(f'"{column}"' for column in columns)
                    placeholders = ", ".join(["%s"] * len(columns))
                    cursor.executemany(f'INSERT INTO "{self.table}" ({quoted}) VALUES ({placeholders})', values)
                    cursor.execute(f'SELECT * FROM "{self.table}" WHERE false')
                    connection.commit()
                    return QueryResult(rows)
                if self.operation == "update":
                    payload = self.payload or {}
                    assignments = ", ".join(f'"{column}" = %s' for column in payload)
                    cursor.execute(f'UPDATE "{self.table}" SET {assignments}{where} RETURNING *', list(payload.values()) + params)
                    rows = list(cursor.fetchall())
                    connection.commit()
                    return QueryResult(rows)
                cursor.execute(f'DELETE FROM "{self.table}"{where} RETURNING *', params)
                rows = list(cursor.fetchall())
                connection.commit()
                return QueryResult(rows)


class Storage:
    root = Path(os.getenv("DOCUMENT_STORAGE_PATH", "/tmp/ai-knowledge-documents"))

    def from_(self, _bucket: str):
        return self

    def upload(self, path: str, file: bytes, file_options: dict | None = None):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(file)

    def download(self, path: str) -> bytes:
        return (self.root / path).read_bytes()

    def remove(self, paths: list[str]):
        for path in paths:
            try:
                (self.root / path).unlink()
            except FileNotFoundError:
                pass

    def get_bucket(self, _name: str):
        return True

    def create_bucket(self, _name: str, options: dict | None = None):
        self.root.mkdir(parents=True, exist_ok=True)


class DatabaseClient:
    storage = Storage()

    def table(self, name: str):
        return TableQuery(name)

    def rpc(self, _function_name: str, _params: dict[str, Any]):
        raise RuntimeError("Database RPC search is not configured for Neon yet")


def get_connection():
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not url:
        raise RuntimeError("DATABASE_URL must be configured")
    return psycopg.connect(url, row_factory=dict_row)


def get_neon_client() -> DatabaseClient:
    return DatabaseClient()


def get_neon_user_client(_token: str) -> DatabaseClient:
    return get_neon_client()
