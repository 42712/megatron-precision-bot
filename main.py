"""
Bot de Trading Binance - Web Service
"""
import time
import threading
from datetime import datetime
from flask import Flask, jsonify
from config import MODO_TESTE, PARES, SALDO_INICIAL
from trader import Trader
from analyzer import Analyzer

app = Flask(__name__)
trader = Trader()
analyzer = Analyzer(trader)

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'modo': 'SIMULAÇÃO' if MODO_TESTE else 'REAL',
        'pares': PARES
    })

@app.route('/status')
def status():
    return jsonify({
        'saldo': trader.get_saldo(),
        'posicoes': len(trader.get_posicoes()),
        'detalhes': trader.get_posicoes()
    })

def bot_loop():
    """Loop do bot rodando em background"""
    while True:
        try:
            resultados = analyzer.monitorar_todos()
            for par, analise in resultados:
                if analise['acao'] == 'COMPRA':
                    trader.comprar(par)
                elif analise['acao'] == 'VENDA':
                    trader.vender(par, analise['motivo'])
            time.sleep(30)
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(60)

if __name__ == "__main__":
    # Inicia o bot em thread separada
    thread = threading.Thread(target=bot_loop, daemon=True)
    thread.start()
    
    # Sobe o servidor web
    app.run(host='0.0.0.0', port=10000)