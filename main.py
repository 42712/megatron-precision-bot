from analyzer import analisar
from trader import comprar
from config import MAX_TRADES
import time

ativos = []

while True:
    sinais = analisar()

    for moeda in sinais:
        if moeda not in ativos and len(ativos) < MAX_TRADES:
            print("🔥 ENTRADA:", moeda)
            comprar(moeda)
            ativos.append(moeda)

    print("⏳ aguardando próxima rodada...")
    time.sleep(300)
