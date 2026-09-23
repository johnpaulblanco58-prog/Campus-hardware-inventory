import os
import sqlite3
import psycopg

from logger import logger


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DB_PATH = os.path.join(
    BASE_DIR,
    "hardware_inventory.db"
)

DATABASE_URL = os.getenv("DATABASE_URL")


class DatabaseError(Exception):
    """Common database exception used by both SQLite and PostgreSQL."""


class _CompatCursor:
    """Small compatibility layer so the existing ? placeholders keep working."""

    def __init__(self, cursor, postgres=False):
        self._cursor = cursor
        self._postgres = postgres

    def execute(self, query, params=None):
        if self._postgres:
            query = query.replace("?", "%s")
        try:
            if params is None:
                return self._cursor.execute(query)
            return self._cursor.execute(query, params)
        except Exception as e:
            raise DatabaseError(str(e)) from e

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description


class _CompatConnection:
    """Connection wrapper exposing the small API used by this project."""

    def __init__(self, connection, postgres=False):
        self._connection = connection
        self._postgres = postgres

    def cursor(self):
        return _CompatCursor(
            self._connection.cursor(),
            postgres=self._postgres
        )

    def commit(self):
        try:
            return self._connection.commit()
        except Exception as e:
            raise DatabaseError(str(e)) from e

    def rollback(self):
        try:
            return self._connection.rollback()
        except Exception as e:
            raise DatabaseError(str(e)) from e

    def close(self):
        return self._connection.close()


def get_connection(db_name=DB_PATH):
    """Use Supabase PostgreSQL when DATABASE_URL is set; otherwise use SQLite."""
    try:
        if DATABASE_URL:
            return _CompatConnection(
                psycopg.connect(DATABASE_URL),
                postgres=True
            )

        conn = sqlite3.connect(db_name)
        conn.execute("PRAGMA foreign_keys = ON")
        return _CompatConnection(conn, postgres=False)

    except (sqlite3.Error, psycopg.Error) as e:
        raise DatabaseError(str(e)) from e


def add_column_if_missing(cursor, table, column, definition):
    """SQLite schema migration helper retained for the local database."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]

    if column not in columns:
        cursor.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def _init_sqlite(conn):
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            failed_attempts INTEGER DEFAULT 0,
            locked_until REAL DEFAULT 0,
            is_verified INTEGER DEFAULT 1,
            verification_code TEXT
        )
        """
    )

    add_column_if_missing(cursor, "users", "email", "TEXT")
    add_column_if_missing(cursor, "users", "role", "TEXT DEFAULT 'user'")
    add_column_if_missing(cursor, "users", "failed_attempts", "INTEGER DEFAULT 0")
    add_column_if_missing(cursor, "users", "locked_until", "REAL DEFAULT 0")
    add_column_if_missing(cursor, "users", "is_verified", "INTEGER DEFAULT 1")
    add_column_if_missing(cursor, "users", "verification_code", "TEXT")

    cursor.execute("""
        UPDATE users
        SET role = 'user'
        WHERE role IS NULL OR role = ''
    """)

    cursor.execute("""
        UPDATE users
        SET is_verified = 1
        WHERE is_verified IS NULL
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            new_password_hash TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    add_column_if_missing(cursor, "password_reset_requests", "user_id", "INTEGER")
    add_column_if_missing(cursor, "password_reset_requests", "email", "TEXT")
    add_column_if_missing(cursor, "password_reset_requests", "new_password_hash", "TEXT")
    add_column_if_missing(cursor, "password_reset_requests", "status", "TEXT DEFAULT 'Pending'")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hardware (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            asset_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            reservation_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            purpose TEXT NOT NULL,
            remarks TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(asset_id) REFERENCES hardware(item_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS borrowings (
            borrowing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER NOT NULL,
            borrow_date TEXT,
            expected_return TEXT,
            actual_return TEXT,
            condition_on_return TEXT,
            remarks TEXT,
            status TEXT DEFAULT 'Borrowed',
            FOREIGN KEY(reservation_id) REFERENCES reservations(reservation_id)
        )
    """)


def _init_postgres(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            failed_attempts INTEGER DEFAULT 0,
            locked_until DOUBLE PRECISION DEFAULT 0,
            is_verified INTEGER DEFAULT 1,
            verification_code TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_requests (
            id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id),
            email TEXT NOT NULL,
            new_password_hash TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hardware (
            item_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DOUBLE PRECISION NOT NULL,
            status TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id),
            asset_id BIGINT NOT NULL REFERENCES hardware(item_id),
            quantity INTEGER NOT NULL,
            reservation_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            purpose TEXT NOT NULL,
            remarks TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS borrowings (
            borrowing_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            reservation_id BIGINT NOT NULL REFERENCES reservations(reservation_id),
            borrow_date TEXT,
            expected_return TEXT,
            actual_return TEXT,
            condition_on_return TEXT,
            remarks TEXT,
            status TEXT DEFAULT 'Borrowed'
        )
    """)

    cursor.execute("""
        UPDATE users
        SET role = 'user'
        WHERE role IS NULL OR role = ''
    """)

    cursor.execute("""
        UPDATE users
        SET is_verified = 1
        WHERE is_verified IS NULL
    """)


def init_db(db_name=DB_PATH):
    try:
        conn = get_connection(db_name)

        if DATABASE_URL:
            _init_postgres(conn)
        else:
            _init_sqlite(conn)

        conn.commit()
        conn.close()

        logger.info("Database initialized successfully.")

    except (DatabaseError, sqlite3.Error, psycopg.Error) as e:
        logger.error(f"Database setup error: {e}")
        raise


if __name__ == "__main__":
    init_db()
