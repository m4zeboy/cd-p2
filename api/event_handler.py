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
from fastapi.exceptions import HTTPException
from models import NotifyIn
from starlette.status import HTTP_404_NOT_FOUND


def publish_event(
    SYNC_SERVICE_BASE_URL: str,
    BRANCH_ID: str,
    operation: str,
    sub: int,
    initial_balance: int = 0,
    current_balance: int = 0,
    delta: int = 0,
):
    event_data = {
        "branch_id": BRANCH_ID,
        "operation": operation,
        "sub": sub,
        "initial_balance": initial_balance,
        "current_balance": current_balance,
        "delta": delta,
    }

    result = requests.post(
        f"{SYNC_SERVICE_BASE_URL}/event/publish",
        json=event_data,
    )
    return result


def consume_create(
    db: Connection, cursor: Cursor, notify_data: NotifyIn, BRANCH_ID: str
):
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


def consume_update(
    db: Connection, cursor: Cursor, notify_data: NotifyIn, BRANCH_ID: str
):
    product = cursor.execute(
        "SELECT current_balance FROM product WHERE id = ?", (notify_data.sub,)
    ).fetchone()

    if product is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Product not found")

    print(f"Found product {notify_data.sub} in branch {BRANCH_ID}. Start updating...")
    current_balance = product[0]

    cursor.execute(
        "UPDATE product SET current_balance = ? WHERE id = ?",
        (current_balance + notify_data.delta, notify_data.sub),
    )
    db.commit()
    print("Sync OK.")

    consume_request = requests.patch(
        f"http://localhost:4000/event/consume/{notify_data.event_consumer_id}"
    )

    print(consume_request.status_code)
