"""
Indicadores Técnicos para análise de mercado
"""
import numpy as np

def calcular_rsi(precos, periodo=14):
    """
    Calcula o Índice de Força Relativa (RSI)
    
    Args:
        precos: Lista de preços
        periodo: Período para cálculo (padrão: 14)
    
    Returns:
        float: Valor do RSI (0-100)
    """
    if len(precos) < periodo + 1:
        return 50  # Retorna neutro se não há dados suficientes
    
    ganhos = 0
    perdas = 0
    
    # Calcula ganhos e perdas
    for i in range(1, periodo + 1):
        diferenca = precos[-i] - precos[-i-1]
        if diferenca > 0:
            ganhos += diferenca
        else:
            perdas += abs(diferenca)
    
    # Calcula médias
    ganho_medio = ganhos / periodo
    perda_media = perdas / periodo
    
    if perda_media == 0:
        return 100
    
    # Calcula RS e RSI
    rs = ganho_medio / perda_media
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)

def calcular_ema(precos, periodo=9):
    """
    Calcula a Média Móvel Exponencial (EMA)
    
    Args:
        precos: Lista de preços
        periodo: Período para cálculo
    
    Returns:
        float: Valor da EMA
    """
    if len(precos) < periodo:
        return precos[-1] if precos else 0
    
    # Fator de suavização
    k = 2 / (periodo + 1)
    
    # Calcula EMA
    ema = precos[-periodo]  # Começa com SMA simples
    for preco in precos[-periodo+1:]:
        ema = (preco * k) + (ema * (1 - k))
    
    return round(ema, 2)

def calcular_sma(precos, periodo=20):
    """
    Calcula a Média Móvel Simples (SMA)
    
    Args:
        precos: Lista de preços
        periodo: Período para cálculo
    
    Returns:
        float: Valor da SMA
    """
    if len(precos) < periodo:
        return precos[-1] if precos else 0
    
    return round(sum(precos[-periodo:]) / periodo, 2)

def gerar_sinal(rsi, ema_fast, ema_slow):
    """
    Gera sinal de compra/venda baseado nos indicadores
    
    Args:
        rsi: Valor do RSI
        ema_fast: EMA rápida
        ema_slow: EMA lenta
    
    Returns:
        str: 'COMPRA', 'VENDA' ou 'NEUTRO'
    """
    from config import RSI_OVERSOLD, RSI_OVERBOUGHT
    
    # Condições de compra
    if rsi < RSI_OVERSOLD and ema_fast > ema_slow:
        return "COMPRA"
    
    # Condições de venda
    if rsi > RSI_OVERBOUGHT and ema_fast < ema_slow:
        return "VENDA"
    
    return "NEUTRO"

def analisar_mercado(historico_precos):
    """
    Análise completa do mercado
    
    Args:
        historico_precos: Lista de preços históricos
    
    Returns:
        dict: Dicionário com todos os indicadores
    """
    from config import RSI_PERIOD, EMA_FAST, EMA_SLOW
    
    if len(historico_precos) < max(RSI_PERIOD, EMA_SLOW):
        return {
            'rsi': 50,
            'ema_fast': historico_precos[-1] if historico_precos else 0,
            'ema_slow': historico_precos[-1] if historico_precos else 0,
            'sma': historico_precos[-1] if historico_precos else 0,
            'sinal': 'NEUTRO',
            'tendencia': 'DADOS_INSUFICIENTES'
        }
    
    rsi = calcular_rsi(historico_precos, RSI_PERIOD)
    ema_fast = calcular_ema(historico_precos, EMA_FAST)
    ema_slow = calcular_ema(historico_precos, EMA_SLOW)
    sma = calcular_sma(historico_precos, 20)
    sinal = gerar_sinal(rsi, ema_fast, ema_slow)
    
    # Determina tendência
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

print("✅ Indicadores carregados com sucesso!")