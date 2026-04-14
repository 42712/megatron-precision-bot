"""
Módulo de Indicadores Técnicos
"""
import numpy as np
from config import (
    RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD,
    EMA_FAST, EMA_SLOW, EMA_TREND,
    MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    BB_PERIOD, BB_DESVIO,
    VOLUME_PERIOD
)


def calcular_rsi(precos, periodo=RSI_PERIOD):
    if len(precos) < periodo + 1:
        return 50.0
    
    deltas = np.diff(precos)
    ganhos = np.where(deltas > 0, deltas, 0)
    perdas = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(ganhos[:periodo])
    avg_loss = np.mean(perdas[:periodo])
    
    if avg_loss == 0:
        return 100.0
    
    for i in range(periodo, len(ganhos)):
        avg_gain = (avg_gain * (periodo - 1) + ganhos[i]) / periodo
        avg_loss = (avg_loss * (periodo - 1) + perdas[i]) / periodo
        if avg_loss == 0:
            return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calcular_ema(precos, periodo):
    if len(precos) < periodo:
        return precos[-1] if precos else 0
    
    multiplicador = 2 / (periodo + 1)
    ema = precos[0]
    
    for preco in precos[1:]:
        ema = (preco - ema) * multiplicador + ema
    
    return ema


def calcular_macd(precos, fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL):
    if len(precos) < slow + signal:
        return 0, 0, 0
    
    ema_fast = []
    ema_slow = []
    
    for i in range(len(precos)):
        if i < fast - 1:
            ema_fast.append(precos[i])
        else:
            if i == fast - 1:
                ema = np.mean(precos[:fast])
            else:
                mult = 2 / (fast + 1)
                ema = (precos[i] - ema_fast[-1]) * mult + ema_fast[-1]
            ema_fast.append(ema)
        
        if i < slow - 1:
            ema_slow.append(precos[i])
        else:
            if i == slow - 1:
                ema = np.mean(precos[:slow])
            else:
                mult = 2 / (slow + 1)
                ema = (precos[i] - ema_slow[-1]) * mult + ema_slow[-1]
            ema_slow.append(ema)
    
    macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(ema_fast))]
    
    signal_line = []
    mult_signal = 2 / (signal + 1)
    
    for i in range(len(macd_line)):
        if i < signal - 1:
            signal_line.append(macd_line[i])
        else:
            if i == signal - 1:
                ema = np.mean(macd_line[:signal])
            else:
                ema = (macd_line[i] - signal_line[-1]) * mult_signal + signal_line[-1]
            signal_line.append(ema)
    
    histogram = macd_line[-1] - signal_line[-1]
    return macd_line[-1], signal_line[-1], histogram


def calcular_bollinger(precos, periodo=BB_PERIOD, desvio=BB_DESVIO):
    if len(precos) < periodo:
        return 0.5
    
    recentes = precos[-periodo:]
    media = np.mean(recentes)
    std = np.std(recentes)
    
    banda_inferior = media - (std * desvio)
    banda_superior = media + (std * desvio)
    preco_atual = precos[-1]
    
    if banda_superior == banda_inferior:
        return 0.5
    
    b_pct = (preco_atual - banda_inferior) / (banda_superior - banda_inferior)
    return max(0, min(1, b_pct))


def calcular_volume_ratio(volumes, periodo=VOLUME_PERIOD):
    if not volumes or len(volumes) < periodo:
        return 1.0
    
    volume_atual = volumes[-1]
    media_volume = np.mean(volumes[-periodo:])
    
    if media_volume == 0:
        return 1.0
    
    return volume_atual / media_volume


def calcular_confluencia(precos, volumes=None):
    if len(precos) < EMA_TREND:
        return {
            'faltam_dados': EMA_TREND - len(precos),
            'pontos_compra': 0,
            'pontos_venda': 0,
            'sinal': 'AGUARDAR'
        }
    
    rsi = calcular_rsi(precos)
    ema_fast = calcular_ema(precos, EMA_FAST)
    ema_slow = calcular_ema(precos, EMA_SLOW)
    ema_trend = calcular_ema(precos, EMA_TREND)
    _, _, macd_hist = calcular_macd(precos)
    bb_pct = calcular_bollinger(precos)
    
    volume_ok = False
    volume_ratio = 1.0
    if volumes and len(volumes) >= VOLUME_PERIOD:
        volume_ratio = calcular_volume_ratio(volumes)
        volume_ok = volume_ratio >= 1.2
    
    # Tendência
    if ema_fast > ema_slow and ema_slow > ema_trend:
        tendencia_maior = "ALTA"
    elif ema_fast < ema_slow and ema_slow < ema_trend:
        tendencia_maior = "BAIXA"
    else:
        tendencia_maior = "LATERAL"
    
    # Pontos COMPRA
    pontos_compra = 0
    detalhes_compra = []
    
    if rsi < RSI_OVERSOLD:
        pontos_compra += 1
        detalhes_compra.append(f"RSI({rsi:.0f})")
    if macd_hist > 0:
        pontos_compra += 1
        detalhes_compra.append("MACD+")
    if ema_fast > ema_slow:
        pontos_compra += 1
        detalhes_compra.append("EMA9>21")
    if bb_pct < 0.2:
        pontos_compra += 1
        detalhes_compra.append("BB oversold")
    if volume_ok:
        pontos_compra += 1
        detalhes_compra.append(f"Vol {volume_ratio:.1f}x")
    
    # Pontos VENDA
    pontos_venda = 0
    detalhes_venda = []
    
    if rsi > RSI_OVERBOUGHT:
        pontos_venda += 1
        detalhes_venda.append(f"RSI({rsi:.0f})")
    if macd_hist < 0:
        pontos_venda += 1
        detalhes_venda.append("MACD-")
    if ema_fast < ema_slow:
        pontos_venda += 1
        detalhes_venda.append("EMA9<21")
    if bb_pct > 0.8:
        pontos_venda += 1
        detalhes_venda.append("BB overbought")
    if volume_ok and tendencia_maior == "BAIXA":
        pontos_venda += 1
        detalhes_venda.append(f"Vol {volume_ratio:.1f}x")
    
    if pontos_compra >= 3:
        sinal = "COMPRA"
    elif pontos_venda >= 3:
        sinal = "VENDA"
    else:
        sinal = "AGUARDAR"
    
    return {
        'faltam_dados': 0,
        'rsi': round(rsi, 1),
        'ema_fast': round(ema_fast, 2),
        'ema_slow': round(ema_slow, 2),
        'ema_trend': round(ema_trend, 2),
        'macd_hist': macd_hist,
        'bb_pct': round(bb_pct, 3),
        'volume_ratio': round(volume_ratio, 2),
        'volume_ok': volume_ok,
        'tendencia_maior': tendencia_maior,
        'pontos_compra': pontos_compra,
        'pontos_venda': pontos_venda,
        'detalhes_compra': detalhes_compra,
        'detalhes_venda': detalhes_venda,
        'sinal': sinal
    }


print("✅ Módulo Indicators carregado!")
