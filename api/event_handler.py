# ===================================================
# Autor: Moisés Silva de Azevedo
#
# Universidade Federal do Mato Grosso do Sul,
# Câmpus de Três Lagoas (UFMS/CPTL),
# Sistemas de Informaçao,
# Computaçao Distribuída,
# Novembro de 2025
# ===================================================

from sqlite3 import Connection, Cursor

import requests
from models import NotifyIn


def consume_create(db: Connection, cursor: Cursor, notify_data: NotifyIn, BRANCH_ID):
    product = cursor.execute(
        "SELECT id FROM product WHERE id = ?", (notify_data.sub,)
    ).fetchone()
    if product is not None:
        print("Product already exists. Ignore")
        return
    print(f"Product {notify_data.sub} not foun in brach {BRANCH_ID}. Start syncing...")
    cursor.execute(
        "INSERT INTO product (id, current_balance) VALUES (?, ?)",
        (notify_data.sub, notify_data.initial_balance),
    )
    db.commit()
    print("Sync OK.")

    consume_request = requests.patch(
        f"http://localhost:4000/event/consume/{notify_data.event_consumer_id}"
    )

    print(consume_request.status_code)
