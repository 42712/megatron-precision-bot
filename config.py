"""
Configurações do Megatron Precision Bot v2.1
MODO REAL - Pronto para operar na Binance
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# 🔐 BINANCE - PREENCHA SUAS KEYS AQUI OU NO .ENV
# ============================================
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "COLE_SUA_API_KEY_AQUI")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "COLE_SUA_SECRET_KEY_AQUI")

# ============================================
# ⚙️ MODO REAL - Desativar simulação
# ============================================
MODO_TESTE = False  # 🔴 FALSE = OPERAÇÃO REAL NA BINANCE

# ============================================
# ⚙️ ESTRATÉGIA — TUDO EM PERCENTUAL
# ============================================
PERCENTUAL_POR_OPERACAO = float(os.getenv("PERCENTUAL_POR_OPERACAO", "0.20"))  # 20% do saldo
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "0.05"))   # +5% lucro
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.02"))        # -2% perda
TRAILING_STOP_PCT = float(os.getenv("TRAILING_STOP_PCT", "0.015"))  # 1.5% trailing

# Convertidos para multiplicador
TAKE_PROFIT = 1 + TAKE_PROFIT_PCT
STOP_LOSS = 1 - STOP_LOSS_PCT
TRAILING_STOP = TRAILING_STOP_PCT

# ============================================
# 🛡️ GESTÃO DE RISCO
# ============================================
MAX_POSICOES = int(os.getenv("MAX_POSICOES", "2"))  # Máximo 2 operações simultâneas
MAX_PERDA_DIARIA_PCT = float(os.getenv("MAX_PERDA_DIARIA_PCT", "0.15"))  # Para se perder 15%
SALDO_MINIMO_PCT = float(os.getenv("SALDO_MINIMO_PCT", "0.30"))  # Para se saldo cair 70%
COOLDOWN_APOS_STOP = int(os.getenv("COOLDOWN_APOS_STOP", "10"))
MIN_CONFLUENCIA = int(os.getenv("MIN_CONFLUENCIA", "4"))  # 4/5 indicadores

# ============================================
# 🔧 CONFIGURAÇÕES GERAIS
# ============================================
SALDO_INICIAL = float(os.getenv("SALDO_INICIAL", "15.0"))  # Seu saldo inicial em USDT

# ============================================
# ⏱️ RATE LIMITING
# ============================================
MIN_INTERVALO = float(os.getenv("MIN_INTERVALO", "0.5"))
DELAY_ENTRE_PARES = float(os.getenv("DELAY_ENTRE_PARES", "2.0"))

# ============================================
# 🎯 PARES PARA OPERAR
# ============================================
PARES = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

# ============================================
# 📈 INDICADORES TÉCNICOS
# ============================================
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

EMA_FAST = 9
EMA_SLOW = 21
EMA_TREND = 50

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

BB_PERIOD = 20
BB_DESVIO = 2.0

VOLUME_PERIOD = 20

print("✅ Configurações carregadas - MODO REAL!")
print(f"   💰 Saldo inicial: ${SALDO_INICIAL}")
print(f"   📊 Por operação: {PERCENTUAL_POR_OPERACAO*100:.0f}% do saldo")
print(f"   📈 Take Profit: +{TAKE_PROFIT_PCT*100:.1f}%")
print(f"   📉 Stop Loss: -{STOP_LOSS_PCT*100:.1f}%")
print(f"   🎯 Confluência mínima: {MIN_CONFLUENCIA}/5")
print(f"   🔴 MODO REAL ATIVADO - Operações reais na Binance!")
