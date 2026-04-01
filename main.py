from flask import Flask
from analyzer import analisar
from trader import comprar
from config import MAX_TRADES
import threading
import time

app = Flask(__name__)

ativos = []

def bot_loop():
    while True:
        try:
            sinais = analisar()

            for moeda in sinais:
                if moeda not in ativos and len(ativos) < MAX_TRADES:
                    print("🔥 ENTRADA:", moeda)
                    comprar(moeda)
                    ativos.append(moeda)

            print("⏳ aguardando...")
            time.sleep(300)

        except Exception as e:
            print("Erro:", e)
            time.sleep(60)

@app.route("/")
def home():
    return "🤖 MEGATRON BOT ONLINE"

if __name__ == "__main__":
    t = threading.Thread(target=bot_loop)
    t.start()

    app.run(host="0.0.0.0", port=10000)
