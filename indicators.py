import numpy as np

def ema(precos, periodo):
    pesos = np.exp(np.linspace(-1., 0., periodo))
    pesos /= pesos.sum()
    return np.convolve(precos, pesos, mode='valid')[-1]

def rsi(precos, periodos=14):
    deltas = np.diff(precos)
    ganhos = deltas[deltas > 0].sum() / periodos
    perdas = -deltas[deltas < 0].sum() / periodos

    if perdas == 0:
        return 100

    rs = ganhos / perdas
    return 100 - (100 / (1 + rs))
