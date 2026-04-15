"""
Configurações do Megatron Precision Bot v2.2
Railway — Binance.com funciona normalmente (servidores fora dos EUA)
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# 🔐 BINANCE
# ============================================
BINANCE_API_KEY    = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")

# Railway usa servidores fora dos EUA — Binance.com funciona!
# Só mude para "us" se tiver conta na Binance.US
BINANCE_TLD = os.getenv("BINANCE_TLD", "com")

# ============================================
# ⚙️ MODO
# ============================================
MODO_TESTE = os.getenv("MODO_TESTE", "False").lower() in ("true", "1", "yes")

# ============================================
# ⚙️ ESTRATÉGIA — TUDO EM PERCENTUAL
# ============================================
PERCENTUAL_POR_OPERACAO = float(os.getenv("PERCENTUAL_POR_OPERACAO", "0.20"))
TAKE_PROFIT_PCT         = float(os.getenv("TAKE_PROFIT_PCT",         "0.05"))
STOP_LOSS_PCT           = float(os.getenv("STOP_LOSS_PCT",           "0.02"))
TRAILING_STOP_PCT       = float(os.getenv("TRAILING_STOP_PCT",       "0.015"))

# Multiplicadores internos
TAKE_PROFIT   = 1 + TAKE_PROFIT_PCT
STOP_LOSS     = 1 - STOP_LOSS_PCT
TRAILING_STOP = TRAILING_STOP_PCT

# ============================================
# 🛡️ GESTÃO DE RISCO
# ============================================
MAX_POSICOES         = int(os.getenv("MAX_POSICOES",          "2"))
MAX_PERDA_DIARIA_PCT = float(os.getenv("MAX_PERDA_DIARIA_PCT","0.15"))
SALDO_MINIMO_PCT     = float(os.getenv("SALDO_MINIMO_PCT",    "0.30"))
COOLDOWN_APOS_STOP   = int(os.getenv("COOLDOWN_APOS_STOP",    "10"))
MIN_CONFLUENCIA      = int(os.getenv("MIN_CONFLUENCIA",        "4"))

# ============================================
# 🔧 GERAL
# ============================================
SALDO_INICIAL = float(os.getenv("SALDO_INICIAL", "15.0"))

# ============================================
# ⏱️ RATE LIMITING
# ============================================
MIN_INTERVALO     = float(os.getenv("MIN_INTERVALO",     "0.5"))
DELAY_ENTRE_PARES = float(os.getenv("DELAY_ENTRE_PARES", "2.0"))

# ============================================
# 💓 KEEP-ALIVE (evita o serviço dormir)
# Railway não dorme, mas o ping garante que o bot está vivo
# ============================================
KEEPALIVE_INTERVALO = int(os.getenv("KEEPALIVE_INTERVALO", "600"))  # 10 min
RAILWAY_PUBLIC_URL  = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")        # preenchido automaticamente pelo Railway

# ============================================
# 🎯 PARES
# ============================================
PARES = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

# ============================================
# 📈 INDICADORES
# ============================================
RSI_PERIOD     = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD   = 30
EMA_FAST       = 9
EMA_SLOW       = 21
EMA_TREND      = 50
MACD_FAST      = 12
MACD_SLOW      = 26
MACD_SIGNAL    = 9
BB_PERIOD      = 20
BB_DESVIO      = 2.0
VOLUME_PERIOD  = 20

modo_label = "🔵 SIMULAÇÃO" if MODO_TESTE else "🔴 REAL"
print(f"✅ Configurações carregadas! Modo: {modo_label} | Binance.{BINANCE_TLD.upper()}")
print(f"   💰 Saldo: ${SALDO_INICIAL} | Por operação: {PERCENTUAL_POR_OPERACAO*100:.0f}%")
print(f"   📈 TP: +{TAKE_PROFIT_PCT*100:.1f}% | SL: -{STOP_LOSS_PCT*100:.1f}% | Trail: {TRAILING_STOP_PCT*100:.1f}%")
print(f"   🎯 Confluência: {MIN_CONFLUENCIA}/5 | Perda diária máx: {MAX_PERDA_DIARIA_PCT*100:.0f}%")
