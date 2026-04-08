"""
Indicadores Técnicos para análise de mercado (SEM numpy)
"""
from config import RSI_PERIOD, EMA_FAST, EMA_SLOW, RSI_OVERBOUGHT, RSI_OVERSOLD

def calcular_rsi(precos, periodo=14):
    """Calcula RSI sem numpy"""
    if len(precos) < periodo + 1:
        return 50.0
    
    ganhos = 0.0
    perdas = 0.0
    
    for i in range(1, periodo + 1):
        diferenca = precos[-i] - precos[-i-1]
        if diferenca > 0:
            ganhos += diferenca
        else:
            perdas += abs(diferenca)
    
    if perdas == 0:
        return 100.0
    
    rs = ganhos / perdas
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def calcular_ema(precos, periodo=9):
    """Calcula EMA sem numpy"""
    if len(precos) < periodo:
        return precos[-1] if precos else 0.0
    
    multiplicador = 2 / (periodo + 1)
    ema = sum(precos[-periodo:]) / periodo  # SMA inicial
    
    for preco in precos[-periodo+1:]:
        ema = (preco - ema) * multiplicador + ema
    
    return round(ema, 2)

def calcular_sma(precos, periodo=20):
    """Calcula SMA sem numpy"""
    if len(precos) < periodo:
        return precos[-1] if precos else 0.0
    
    return round(sum(precos[-periodo:]) / periodo, 2)

def gerar_sinal(rsi, ema_fast, ema_slow):
    """Gera sinal baseado nos indicadores"""
    if rsi < RSI_OVERSOLD and ema_fast > ema_slow:
        return "COMPRA"
    elif rsi > RSI_OVERBOUGHT and ema_fast < ema_slow:
        return "VENDA"
    return "NEUTRO"

def analisar_mercado(historico_precos):
    """Análise completa do mercado"""
    if len(historico_precos) < max(RSI_PERIOD, EMA_SLOW):
        return {
            'rsi': 50.0,
            'ema_fast': historico_precos[-1] if historico_precos else 0.0,
            'ema_slow': historico_precos[-1] if historico_precos else 0.0,
            'sma': historico_precos[-1] if historico_precos else 0.0,
            'sinal': 'NEUTRO',
            'tendencia': 'DADOS_INSUFICIENTES'
        }
    
    rsi = calcular_rsi(historico_precos, RSI_PERIOD)
    ema_fast = calcular_ema(historico_precos, EMA_FAST)
    ema_slow = calcular_ema(historico_precos, EMA_SLOW)
    sma = calcular_sma(historico_precos, 20)
    sinal = gerar_sinal(rsi, ema_fast, ema_slow)
    
    if ema_fast > ema_slow:
        tendencia = "ALTA"
    elif ema_fast < ema_slow:
        tendencia = "BAIXA"
    else:
        tendencia = "LATERAL"
    
    return {
        'rsi': rsi,
        'ema_fast': ema_fast,
        'ema_slow': ema_slow,
        'sma': sma,
        'sinal': sinal,
        'tendencia': tendencia
    }

print("✅ Indicadores carregados com sucesso (versão sem numpy)!")