"""
Módulo de Indicadores Técnicos — RSI + EMA
"""
from config import RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD, EMA_FAST, EMA_SLOW


def calcular_ema(precos, periodo):
    """Calcula EMA (Exponential Moving Average)"""
    if len(precos) < periodo:
        return precos[-1] if precos else 0

    k = 2 / (periodo + 1)
    ema = sum(precos[:periodo]) / periodo  # SMA inicial
    for preco in precos[periodo:]:
        ema = preco * k + ema * (1 - k)
    return round(ema, 6)


def calcular_rsi(precos, periodo=RSI_PERIOD):
    """Calcula RSI (Relative Strength Index)"""
    if len(precos) < periodo + 1:
        return 50  # neutro enquanto coleta dados

    deltas = [precos[i] - precos[i - 1] for i in range(1, len(precos))]
    ganhos = [d for d in deltas if d > 0]
    perdas = [-d for d in deltas if d < 0]

    if not perdas:
        return 100
    if not ganhos:
        return 0

    media_ganho = sum(ganhos[-periodo:]) / periodo
    media_perda = sum(perdas[-periodo:]) / periodo

    if media_perda == 0:
        return 100

    rs = media_ganho / media_perda
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)


def analisar_mercado(precos):
    """
    Analisa o mercado usando RSI + EMA crossover.

    Returns:
        dict: rsi, ema_fast, ema_slow, tendencia, sinal
    """
    rsi = calcular_rsi(precos)
    ema_fast = calcular_ema(precos, EMA_FAST)
    ema_slow = calcular_ema(precos, EMA_SLOW)

    # Tendência baseada nas EMAs
    if ema_fast > ema_slow:
        tendencia = "ALTA 📈"
    elif ema_fast < ema_slow:
        tendencia = "BAIXA 📉"
    else:
        tendencia = "LATERAL ↔️"

    # Sinal combinado: RSI + EMA
    if rsi < RSI_OVERSOLD and ema_fast > ema_slow:
        sinal = "COMPRA"
    elif rsi > RSI_OVERBOUGHT and ema_fast < ema_slow:
        sinal = "VENDA"
    else:
        sinal = "NEUTRO"

    return {
        "rsi": rsi,
        "ema_fast": ema_fast,
        "ema_slow": ema_slow,
        "tendencia": tendencia,
        "sinal": sinal
    }


print("✅ Módulo Indicators carregado com sucesso!")