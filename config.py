"""
Configurações do Megatron Precision Bot v2.1
Sistema 100% percentual — funciona com qualquer saldo
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# 🔐 BINANCE
# ============================================
BINANCE_API_KEY    = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")

# ============================================
# ⚙️ ESTRATÉGIA — TUDO EM PERCENTUAL
# ============================================

# % do saldo total usado por operação
# Ex: 0.20 = usa 20% do saldo em cada compra
# Com $15 → usa $3 por operação
# Com $100 → usa $20 por operação
# Com $500 → usa $100 por operação
PERCENTUAL_POR_OPERACAO = float(os.getenv("PERCENTUAL_POR_OPERACAO", "0.20"))  # 20%

# Take Profit: % de lucro para vender
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "0.05"))   # +5%

# Stop Loss: % de perda máxima por operação
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.02"))        # -2%

# Trailing Stop: % de queda do topo para acionar
TRAILING_STOP_PCT = float(os.getenv("TRAILING_STOP_PCT", "0.015"))  # 1.5%

# Convertidos para multiplicador (compatibilidade interna)
TAKE_PROFIT  = 1 + TAKE_PROFIT_PCT
STOP_LOSS    = 1 - STOP_LOSS_PCT
TRAILING_STOP = TRAILING_STOP_PCT

# ============================================
# 🛡️ GESTÃO DE RISCO — EM PERCENTUAL
# ============================================

# Máximo de posições abertas ao mesmo tempo
MAX_POSICOES = int(os.getenv("MAX_POSICOES", "2"))

# Perda diária máxima em % do saldo inicial
# Ex: 0.15 = para o bot se perder 15% do saldo no dia
MAX_PERDA_DIARIA_PCT = float(os.getenv("MAX_PERDA_DIARIA_PCT", "0.15"))  # 15%

# Saldo mínimo para operar (% do saldo inicial)
# Ex: 0.30 = para se saldo cair abaixo de 30% do inicial
SALDO_MINIMO_PCT = float(os.getenv("SALDO_MINIMO_PCT", "0.30"))  # 30%

# Cooldown após stop loss (ciclos bloqueados)
COOLDOWN_APOS_STOP = int(os.getenv("COOLDOWN_APOS_STOP", "10"))

# Pontuação mínima de confluência (máx = 5)
MIN_CONFLUENCIA = int(os.getenv("MIN_CONFLUENCIA", "4"))

# ============================================
# 🔧 CONFIGURAÇÕES GERAIS
# ============================================
MODO_TESTE    = os.getenv("MODO_TESTE", "True").lower() in ("true", "1", "yes")
SALDO_INICIAL = float(os.getenv("SALDO_INICIAL", "15.0"))  # Seu saldo inicial em USDT

# ============================================
# ⏱️ RATE LIMITING
# ============================================
MIN_INTERVALO     = float(os.getenv("MIN_INTERVALO",     "0.5"))
DELAY_ENTRE_PARES = float(os.getenv("DELAY_ENTRE_PARES", "2.0"))

# ============================================
# 🎯 PARES
# ============================================
PARES = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

# ============================================
# 📈 INDICADORES TÉCNICOS
# ============================================
RSI_PERIOD     = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD   = 30

EMA_FAST  = 9
EMA_SLOW  = 21
EMA_TREND = 50

MACD_FAST   = 12
MACD_SLOW   = 26
MACD_SIGNAL = 9

BB_PERIOD = 20
BB_DESVIO = 2.0

VOLUME_PERIOD = 20

# ============================================
# 🔍 RESUMO NO BOOT
# ============================================
print("✅ Configurações carregadas!")
print(f"   💰 Saldo inicial: ${SALDO_INICIAL}")
print(f"   📊 Por operação: {PERCENTUAL_POR_OPERACAO*100:.0f}% do saldo")
print(f"   📈 Take Profit: +{TAKE_PROFIT_PCT*100:.1f}%")
print(f"   📉 Stop Loss: -{STOP_LOSS_PCT*100:.1f}%")
print(f"   🔒 Trailing Stop: {TRAILING_STOP_PCT*100:.1f}%")
print(f"   🛡️ Perda diária máx: {MAX_PERDA_DIARIA_PCT*100:.0f}% do saldo")
print(f"   🎯 Confluência mínima: {MIN_CONFLUENCIA}/5")
