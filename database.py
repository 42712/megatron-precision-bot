import sqlite3

conn = sqlite3.connect("trades.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY,
    moeda TEXT,
    compra REAL,
    venda REAL,
    lucro REAL
)
""")

conn.commit()

def salvar_trade(moeda, compra, venda):
    lucro = venda - compra
    cursor.execute(
        "INSERT INTO trades (moeda, compra, venda, lucro) VALUES (?, ?, ?, ?)",
        (moeda, compra, venda, lucro)
    )
    conn.commit()
