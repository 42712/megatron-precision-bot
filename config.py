"""
Configurações do Bot Trading Binance
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# 🔐 CONFIGURAÇÕES DA BINANCE
# ============================================
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")

# ============================================
# ⚙️ CONFIGURAÇÕES DA ESTRATÉGIA
# ============================================
VALOR_COMPRA = float(os.getenv("VALOR_COMPRA", "50.0"))
TAKE_PROFIT = float(os.getenv("TAKE_PROFIT", "1.05"))
STOP_LOSS = float(os.getenv("STOP_LOSS", "0.98"))

# ============================================
# 🔧 CONFIGURAÇÕES GERAIS
# ============================================
MODO_TESTE = os.getenv("MODO_TESTE", "True").lower() in ("true", "1", "yes")
SALDO_INICIAL = float(os.getenv("SALDO_INICIAL", "100.0"))

# ============================================
# ⏱️ RATE LIMITING — valores seguros para Binance
# ============================================
# Binance permite 1200 "pesos" por minuto.
# get_symbol_ticker = peso 1. Cada ordem = peso 1.
# Com 3 pares x várias chamadas, mínimo seguro = 0.5s entre requisições.
MIN_INTERVALO = float(os.getenv("MIN_INTERVALO", "0.5"))   # 500ms (era 100ms — muito rápido!)
DELAY_ENTRE_PARES = float(os.getenv("DELAY_ENTRE_PARES", "2.0"))  # 2s entre pares

# ============================================
# 🎯 PARES PARA OPERAR
# ============================================
PARES = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # Formato correto da Binance (sem "/")

# ============================================
# 📈 INDICADORES TÉCNICOS
# ============================================
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
EMA_FAST = 9
EMA_SLOW = 21

print("✅ Configurações carregadas com sucesso!")
