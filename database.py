"""
Banco de dados para registrar todas as operações
"""
import sqlite3
from datetime import datetime

# ============================================
# CONEXÃO COM O BANCO DE DADOS
# ============================================
conn = sqlite3.connect("trades.db", check_same_thread=False)
cursor = conn.cursor()

# ============================================
# CRIAÇÃO DAS TABELAS
# ============================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    moeda TEXT,
    compra REAL,
    venda REAL,
    quantidade REAL,
    lucro REAL,
    lucro_percentual REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS saldo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    saldo REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS indicadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    moeda TEXT,
    rsi REAL,
    ema_fast REAL,
    ema_slow REAL,
    sinal TEXT
)
""")

conn.commit()

# ============================================
# FUNÇÕES PARA SALVAR DADOS
# ============================================
def salvar_trade(moeda, compra, venda, quantidade=0):
    """Salva um trade completo no banco"""
    lucro = (venda - compra) * quantidade if quantidade > 0 else venda - compra
    lucro_percentual = ((venda / compra) - 1) * 100 if compra > 0 else 0
    
    cursor.execute("""
        INSERT INTO trades (data, moeda, compra, venda, quantidade, lucro, lucro_percentual)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        moeda,
        compra,
        venda,
        quantidade,
        round(lucro, 2),
        round(lucro_percentual, 2)
    ))
    conn.commit()
    
    print(f"💾 Trade salvo: {moeda} | Lucro: R$ {lucro:.2f} ({lucro_percentual:.2f}%)")
    return lucro

def salvar_saldo(saldo):
    """Registra o saldo atual no banco"""
    cursor.execute("""
        INSERT INTO saldo (data, saldo)
        VALUES (?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), round(saldo, 2)))
    conn.commit()

def salvar_indicador(moeda, rsi, ema_fast, ema_slow, sinal):
    """Salva indicadores técnicos"""
    cursor.execute("""
        INSERT INTO indicadores (data, moeda, rsi, ema_fast, ema_slow, sinal)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        moeda,
        round(rsi, 2) if rsi else None,
        round(ema_fast, 2) if ema_fast else None,
        round(ema_slow, 2) if ema_slow else None,
        sinal
    ))
    conn.commit()

def get_historico(limite=10):
    """Retorna os últimos trades"""
    cursor.execute("""
        SELECT data, moeda, compra, venda, lucro, lucro_percentual
        FROM trades
        ORDER BY id DESC
        LIMIT ?
    """, (limite,))
    return cursor.fetchall()

def get_estatisticas():
    """Retorna estatísticas das operações"""
    cursor.execute("""
        SELECT 
            COUNT(*) as total_trades,
            SUM(lucro) as lucro_total,
            AVG(lucro_percentual) as media_lucro,
            COUNT(CASE WHEN lucro > 0 THEN 1 END) as trades_ganhos,
            COUNT(CASE WHEN lucro < 0 THEN 1 END) as trades_perdidos
        FROM trades
    """)
    resultado = cursor.fetchone()
    
    if resultado and resultado[0] > 0:
        return {
            "total_trades": resultado[0],
            "lucro_total": round(resultado[1] or 0, 2),
            "media_lucro": round(resultado[2] or 0, 2),
            "trades_ganhos": resultado[3] or 0,
            "trades_perdidos": resultado[4] or 0,
            "taxa_acerto": round((resultado[3] or 0) / resultado[0] * 100, 2)
        }
    return None

print("✅ Banco de dados inicializado com sucesso!")