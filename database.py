# database.py
"""
Módulo de Banco de Dados SQLite
Armazena trades, saldos e indicadores
"""
import sqlite3
import json
from datetime import datetime
import os

DB_PATH = os.getenv("DB_PATH", "trading_bot.db")

def init_db():
    """Inicializa as tabelas do banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de trades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            preco_compra REAL NOT NULL,
            preco_venda REAL NOT NULL,
            quantidade REAL NOT NULL,
            lucro REAL,
            lucro_pct REAL,
            data_compra TIMESTAMP,
            data_venda TIMESTAMP,
            motivo TEXT
        )
    ''')
    
    # Tabela de saldos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saldos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            saldo REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de indicadores (para análise posterior)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS indicadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            rsi REAL,
            ema_fast REAL,
            ema_slow REAL,
            sinal TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de estatísticas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estatisticas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_trades INTEGER DEFAULT 0,
            trades_ganhos INTEGER DEFAULT 0,
            trades_perdidos INTEGER DEFAULT 0,
            lucro_total REAL DEFAULT 0,
            maior_lucro REAL DEFAULT 0,
            maior_perda REAL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


def salvar_trade(symbol, preco_compra, preco_venda, quantidade, motivo=""):
    """Salva um trade concluído"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    lucro = (preco_venda - preco_compra) * quantidade
    lucro_pct = ((preco_venda / preco_compra) - 1) * 100
    
    cursor.execute('''
        INSERT INTO trades (symbol, preco_compra, preco_venda, quantidade, lucro, lucro_pct, data_compra, data_venda, motivo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (symbol, preco_compra, preco_venda, quantidade, lucro, lucro_pct, 
          datetime.now(), datetime.now(), motivo))
    
    # Atualizar estatísticas
    cursor.execute('SELECT * FROM estatisticas ORDER BY id DESC LIMIT 1')
    stats = cursor.fetchone()
    
    if stats:
        total_trades = stats[1] + 1
        trades_ganhos = stats[2] + (1 if lucro > 0 else 0)
        trades_perdidos = stats[3] + (1 if lucro < 0 else 0)
        lucro_total = stats[4] + lucro
        maior_lucro = max(stats[5], lucro) if lucro > 0 else stats[5]
        maior_perda = min(stats[6], lucro) if lucro < 0 else stats[6]
        
        cursor.execute('''
            UPDATE estatisticas 
            SET total_trades = ?, trades_ganhos = ?, trades_perdidos = ?, 
                lucro_total = ?, maior_lucro = ?, maior_perda = ?, updated_at = ?
            WHERE id = ?
        ''', (total_trades, trades_ganhos, trades_perdidos, lucro_total, 
              maior_lucro, maior_perda, datetime.now(), stats[0]))
    else:
        cursor.execute('''
            INSERT INTO estatisticas (total_trades, trades_ganhos, trades_perdidos, 
                                     lucro_total, maior_lucro, maior_perda)
            VALUES (1, ?, ?, ?, ?, ?)
        ''', (1 if lucro > 0 else 0, 1 if lucro < 0 else 0, lucro, 
              lucro if lucro > 0 else 0, lucro if lucro < 0 else 0))
    
    conn.commit()
    conn.close()
    
    print(f"📝 Trade salvo: {symbol} | Lucro: ${lucro:.2f} ({lucro_pct:+.2f}%)")
    return True


def salvar_saldo(saldo):
    """Salva o saldo atual no histórico"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO saldos (saldo) VALUES (?)', (saldo,))
    conn.commit()
    conn.close()


def salvar_indicador(symbol, rsi, ema_fast, ema_slow, sinal):
    """Salva indicadores para análise posterior"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO indicadores (symbol, rsi, ema_fast, ema_slow, sinal)
        VALUES (?, ?, ?, ?, ?)
    ''', (symbol, rsi, ema_fast, ema_slow, sinal))
    conn.commit()
    conn.close()


def get_estatisticas():
    """Retorna estatísticas do bot"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM estatisticas ORDER BY id DESC LIMIT 1')
    stats = cursor.fetchone()
    
    # Trades recentes
    cursor.execute('''
        SELECT symbol, preco_compra, preco_venda, lucro, lucro_pct, data_venda, motivo
        FROM trades ORDER BY id DESC LIMIT 10
    ''')
    trades_recentes = cursor.fetchall()
    
    conn.close()
    
    if stats:
        return {
            'total_trades': stats[1],
            'trades_ganhos': stats[2],
            'trades_perdidos': stats[3],
            'taxa_acerto': round((stats[2] / stats[1] * 100), 2) if stats[1] > 0 else 0,
            'lucro_total': round(stats[4], 4),
            'maior_lucro': round(stats[5], 4),
            'maior_perda': round(stats[6], 4),
            'trades_recentes': [
                {
                    'symbol': t[0],
                    'preco_compra': t[1],
                    'preco_venda': t[2],
                    'lucro': round(t[3], 4),
                    'lucro_pct': round(t[4], 2),
                    'data': t[5],
                    'motivo': t[6]
                } for t in trades_recentes
            ]
        }
    else:
        return {
            'total_trades': 0,
            'trades_ganhos': 0,
            'trades_perdidos': 0,
            'taxa_acerto': 0,
            'lucro_total': 0,
            'maior_lucro': 0,
            'maior_perda': 0,
            'trades_recentes': []
        }


# Inicializar banco ao importar
init_db()
print("✅ Módulo Database carregado com sucesso!")
