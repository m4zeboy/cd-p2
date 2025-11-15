import sqlite3


def get_db():
    conn = sqlite3.connect("product_database.db")
    conn.row_factory = sqlite3.Row

    try:
        yield conn
    finally:
        conn.close()


def start_database():
    conn = sqlite3.connect("product_database.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY,
            current_balance INTEGER NOT NULL
        )
        """)
    conn.execute("""
            CREATE TABLE IF NOT EXISTS request (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS product_request (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            request_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES request(id),
            FOREIGN KEY (product_id) REFERENCES product(id)
        )
        """)
    conn.commit()
    conn.close()
