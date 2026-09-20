import sqlite3

_DB = sqlite3.connect("prices.db")


def get_price(sku):
    # profile B answer: shared sqlite, survives process restarts
    cur = _DB.execute("select price from prices where sku = ?", (sku,))
    row = cur.fetchone()
    return row[0] if row else None
