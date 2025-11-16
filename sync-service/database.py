# ===================================================
# Autor: Moisés Silva de Azevedo
#
# Universidade Federal do Mato Grosso do Sul,
# Câmpus de Três Lagoas (UFMS/CPTL),
# Sistemas de Informaçao,
# Computaçao Distribuída,
# Novembro de 2025
# ===================================================
import sqlite3


def get_db():
    conn = sqlite3.connect("sync_database.db")
    conn.row_factory = sqlite3.Row

    try:
        yield conn
    finally:
        conn.close()


def start_database():
    conn = sqlite3.connect("sync_database.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscriber (
            id TEXT PRIMARY KEY,
            branch_url TEXT NOT NULL UNIQUE,
            subscribed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            publisher_id TEXT,
            subscriber_id TEXT,
            published_at TEXT DEFAULT CURRENT_TIMESTAMP,
            consumed_at TEXT NULL,
            operation TEXT,
            sub INTEGER,
            initial_balance INTEGER,
            current_balance INTEGER,
            delta INTEGER,
            FOREIGN KEY (publisher_id) REFERENCES subscriber(id),
            FOREIGN KEY (subscriber_id) REFERENCES subscriber(id)
        )
        """)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            locked_at TEXT DEFAULT CURRENT_TIMESTAMP,
            released_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()
