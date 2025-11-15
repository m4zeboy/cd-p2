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
            publisher TEXT,
            published_at TEXT DEFAULT CURRENT_TIMESTAMP,
            operation TEXT,
            sub INTEGER,
            initial_balance INTEGER,
            current_balance INTEGER,
            delta INTEGER,
            FOREIGN KEY (publisher) REFERENCES publisher(id)
        )
        """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS event_consumer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id TEXT,
            event_id INTEGER NOT NULL,
            received_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            consumed_at TEXT NULLABLE,
            FOREIGN KEY (event_id) REFERENCES event(id)
            FOREIGN KEY (subscriber_id) REFERENCES subscriber(id)
        )
        """)
    conn.commit()
    conn.close()
