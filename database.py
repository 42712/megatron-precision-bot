"""
Módulo de Banco de Dados — SQLite
"""
import sqlite3
from datetime import datetime

DB_PATH = "trades.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            preco_compra REAL,
            preco_venda REAL,
            quantidade REAL,
            lucro REAL,
            data TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS saldos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            saldo REAL,
            data TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS indicadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            rsi REAL,
            ema_fast REAL,
            ema_slow REAL,
            sinal TEXT,
            data TEXT
        )
    """)
    conn.commit()
    conn.close()


def salvar_trade(symbol, preco_compra, preco_venda, quantidade):
    lucro = (preco_venda - preco_compra) * quantidade
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO trades (symbol, preco_compra, preco_venda, quantidade, lucro, data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (symbol, preco_compra, preco_venda, quantidade, lucro, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def salvar_saldo(saldo):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO saldos (saldo, data) VALUES (?, ?)",
              (saldo, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def salvar_indicador(symbol, rsi, ema_fast, ema_slow, sinal):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO indicadores (symbol, rsi, ema_fast, ema_slow, sinal, data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (symbol, rsi, ema_fast, ema_slow, sinal, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_estatisticas():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*), SUM(lucro) FROM trades")
        row = c.fetchone()
        conn.close()
        if row and row[0] > 0:
            total = row[0]
            lucro = round(row[1] or 0, 2)
            conn2 = sqlite3.connect(DB_PATH)
            c2 = conn2.cursor()
            c2.execute("SELECT COUNT(*) FROM trades WHERE lucro > 0")
            ganhos = c2.fetchone()[0]
            conn2.close()
            taxa = round((ganhos / total) * 100, 1)
            return {"total_trades": total, "lucro_total": lucro, "taxa_acerto": taxa}
        return None
    except Exception:
        return None


# Inicializa o banco ao importar
init_db()
print("✅ Módulo Database carregado com sucesso!")