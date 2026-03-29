"""Database abstraction — uses Neon PostgreSQL if configured, SQLite locally."""
import os
import json
import sqlite3
from uuid import uuid4
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
USE_POSTGRES = bool(DATABASE_URL)
USE_SUPABASE = SUPABASE_URL and "placeholder" not in SUPABASE_URL

DB_PATH = os.path.join(os.path.dirname(__file__), "local.db")


def _get_conn():
    """Returns a database connection — PostgreSQL (Neon) or SQLite."""
    if USE_POSTGRES:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if using SQLite (Postgres tables created via migrations)."""
    if USE_POSTGRES or USE_SUPABASE:
        return
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS executivos (
            id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            cargo TEXT DEFAULT 'Executivo de Parcerias',
            regiao TEXT DEFAULT '',
            whatsapp TEXT DEFAULT '',
            email TEXT DEFAULT '',
            foto_url TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT (datetime('now')),
            atualizado_em TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS campanhas (
            id TEXT PRIMARY KEY,
            usuario_id TEXT,
            executivo_id TEXT,
            tipo TEXT NOT NULL,
            cliente TEXT NOT NULL,
            empreendimento TEXT DEFAULT '',
            status TEXT DEFAULT 'rascunho',
            briefing TEXT DEFAULT '{}',
            copy TEXT DEFAULT '{}',
            criada_em TEXT DEFAULT (datetime('now')),
            atualizada_em TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS pecas (
            id TEXT PRIMARY KEY,
            campanha_id TEXT,
            formato TEXT NOT NULL,
            versao INTEGER DEFAULT 1,
            html TEXT,
            arquivo_url TEXT DEFAULT '',
            is_atual INTEGER DEFAULT 1,
            criada_em TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS mensagens (
            id TEXT PRIMARY KEY,
            campanha_id TEXT,
            formato TEXT DEFAULT 'geral',
            role TEXT NOT NULL,
            conteudo TEXT NOT NULL,
            criada_em TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def _row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    # Convert SQLite integer booleans
    if "ativo" in d and isinstance(d["ativo"], int):
        d["ativo"] = bool(d["ativo"])
    if "is_atual" in d and isinstance(d["is_atual"], int):
        d["is_atual"] = bool(d["is_atual"])
    # Parse JSON fields (SQLite stores as string, Postgres as dict)
    for field in ("briefing", "copy"):
        if field in d and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                d[field] = {}
    # Convert UUID and datetime to strings for JSON serialization
    for k, v in d.items():
        if hasattr(v, "hex") and hasattr(v, "int"):  # UUID
            d[k] = str(v)
        elif hasattr(v, "isoformat"):  # datetime
            d[k] = v.isoformat()
    return d


class LocalDB:
    """SQLite-backed DB that mimics the Supabase client interface we use."""

    def table(self, name):
        return LocalTable(name)

    class storage:
        @staticmethod
        def from_(bucket):
            return LocalStorage(bucket)


class LocalTable:
    def __init__(self, name):
        self._name = name
        self._filters = []
        self._order_by = None
        self._order_desc = False
        self._is_single = False
        self._select_cols = "*"

    def select(self, cols="*"):
        self._select_cols = cols
        return self

    def eq(self, col, val):
        self._filters.append((col, "=", val))
        return self

    def order(self, col, desc=False):
        self._order_by = col
        self._order_desc = desc
        return self

    def single(self):
        self._is_single = True
        return self

    def execute(self):
        # Route to correct operation
        if hasattr(self, "_insert_row"):
            return self._do_insert()
        if hasattr(self, "_updates"):
            return self._execute_update()
        return self._do_select()

    def _do_select(self):
        conn = _get_conn()
        ph = "%s" if USE_POSTGRES else "?"
        where = ""
        params = []
        if self._filters:
            clauses = []
            for col, op, val in self._filters:
                clauses.append(f"{col} {op} {ph}")
                if not USE_POSTGRES and isinstance(val, bool):
                    params.append(int(val))
                else:
                    params.append(val)
            where = " WHERE " + " AND ".join(clauses)

        order = ""
        if self._order_by:
            order = f" ORDER BY {self._order_by} {'DESC' if self._order_desc else 'ASC'}"

        sql = f"SELECT * FROM {self._name}{where}{order}"
        if USE_POSTGRES:
            import psycopg2.extras
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()
        else:
            rows = conn.execute(sql, params).fetchall()
            conn.close()
        data = [_row_to_dict(r) for r in rows]

        if self._is_single:
            return _Result(data[0] if data else None)
        return _Result(data)

    def insert(self, row):
        self._insert_row = row
        return self

    def _do_insert(self):
        conn = _get_conn()
        ph = "%s" if USE_POSTGRES else "?"
        row_copy = dict(self._insert_row)
        for field in ("briefing", "copy"):
            if field in row_copy and not isinstance(row_copy[field], str):
                row_copy[field] = json.dumps(row_copy[field], ensure_ascii=False)
        if not USE_POSTGRES:
            for k, v in row_copy.items():
                if isinstance(v, bool):
                    row_copy[k] = int(v)

        cols = ", ".join(row_copy.keys())
        placeholders = ", ".join([ph] * len(row_copy))

        if USE_POSTGRES:
            import psycopg2.extras
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                f"INSERT INTO {self._name} ({cols}) VALUES ({placeholders}) RETURNING *",
                list(row_copy.values())
            )
            result = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            return _Result([_row_to_dict(result)] if result else [self._insert_row])
        else:
            conn.execute(f"INSERT INTO {self._name} ({cols}) VALUES ({placeholders})", list(row_copy.values()))
            conn.commit()
            row_id = self._insert_row.get("id")
            if row_id:
                result = conn.execute(f"SELECT * FROM {self._name} WHERE id = ?", [row_id]).fetchone()
                conn.close()
                return _Result([_row_to_dict(result)] if result else [self._insert_row])
            conn.close()
            return _Result([self._insert_row])

    def update(self, updates):
        self._updates = updates
        return self

    def _execute_update(self):
        conn = _get_conn()
        ph = "%s" if USE_POSTGRES else "?"
        updates = dict(self._updates)
        for field in ("briefing", "copy"):
            if field in updates and not isinstance(updates[field], str):
                updates[field] = json.dumps(updates[field], ensure_ascii=False)
        if not USE_POSTGRES:
            for k, v in updates.items():
                if isinstance(v, bool):
                    updates[k] = int(v)

        set_clause = ", ".join(f"{k} = {ph}" for k in updates.keys())
        params = list(updates.values())

        where_clauses = []
        for col, op, val in self._filters:
            where_clauses.append(f"{col} {op} {ph}")
            if not USE_POSTGRES and isinstance(val, bool):
                params.append(int(val))
            else:
                params.append(val)

        where = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        if USE_POSTGRES:
            import psycopg2.extras
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(f"UPDATE {self._name} SET {set_clause}{where} RETURNING *", params)
            rows = cur.fetchall()
            conn.commit()
            cur.close()
            conn.close()
        else:
            conn.execute(f"UPDATE {self._name} SET {set_clause}{where}", params)
            conn.commit()
            select_params = [int(v) if isinstance(v, bool) else v for _, _, v in self._filters]
            select_where = " WHERE " + " AND ".join(f"{c} {o} ?" for c, o, _ in self._filters) if self._filters else ""
            rows = conn.execute(f"SELECT * FROM {self._name}{select_where}", select_params).fetchall()
            conn.close()
        return _Result([_row_to_dict(r) for r in rows])



class LocalStorage:
    """Saves files locally instead of Supabase Storage."""
    STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")

    def __init__(self, bucket):
        self._bucket = bucket
        self._dir = os.path.join(self.STORAGE_DIR, bucket)
        os.makedirs(self._dir, exist_ok=True)

    def upload(self, path, data, options=None):
        full_path = os.path.join(self._dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        mode = "wb" if isinstance(data, bytes) else "w"
        with open(full_path, mode) as f:
            f.write(data)

    def get_public_url(self, path):
        return f"/storage/{self._bucket}/{path}"


class _Result:
    def __init__(self, data):
        self.data = data


def get_db():
    """Returns appropriate DB client."""
    if USE_SUPABASE:
        from supabase import create_client
        return create_client(SUPABASE_URL, os.getenv("SUPABASE_SERVICE_KEY", ""))
    return LocalDB()


# Initialize on import
init_db()
