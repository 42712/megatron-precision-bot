"""
Configurações do Bot Trading Binance
"""
import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# ============================================
# 🔐 CONFIGURAÇÕES DA BINANCE
# ============================================
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "sua_api_key_aqui")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "sua_secret_key_aqui")

# ============================================
# ⚙️ CONFIGURAÇÕES DA ESTRATÉGIA
# ============================================
VALOR_COMPRA = 50.0          # R$ 50 por operação
TAKE_PROFIT = 1.05           # 5% de lucro
STOP_LOSS = 0.98             # 2% de perda

# ============================================
# 🔧 CONFIGURAÇÕES ADICIONAIS
# ============================================
MODO_TESTE = True            # True = simulação, False = operações reais
SALDO_INICIAL = 100.0        # Saldo inicial simulado
MIN_INTERVALO = 0.1          # 100ms entre requisições (evita bloqueio)

# ============================================
# 📊 API COINMARKETCAP (opcional)
# ============================================
CMC_API = os.getenv("CMC_API", "")

# ============================================
# 🎯 PARES PARA OPERAR
# ============================================
PARES = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]

# ============================================
# 📈 INDICADORES TÉCNICOS
# ============================================
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
EMA_FAST = 9
EMA_SLOW = 21

print("✅ Configurações carregadas com sucesso!")