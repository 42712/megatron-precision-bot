"""
Bot de Trading Binance - Versão Web Service (Keep Alive)
"""
import time
import sys
from datetime import datetime
from flask import Flask, jsonify
from threading import Thread
from config import MODO_TESTE, PARES, VALOR_COMPRA, TAKE_PROFIT, STOP_LOSS, SALDO_INICIAL
from database import get_estatisticas
from trader import Trader
from analyzer import Analyzer

app = Flask(__name__)
trader = Trader()
analyzer = Analyzer(trader)
bot_ativo = True

# ============================================
# ROTAS WEB
# ============================================

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'bot': 'MEGATRON PRECISION BOT',
        'modo': 'SIMULAÇÃO' if MODO_TESTE else 'REAL',
        'pares': PARES,
        'saldo': trader.get_saldo(),
        'posicoes': len(trader.get_posicoes())
    })

@app.route('/status')
def status():
    stats = get_estatisticas()
    return jsonify({
        'saldo': trader.get_saldo(),
        'posicoes': trader.get_posicoes(),
        'estatisticas': stats,
        'timestamp': datetime.now().isoformat()
    })

# ============================================
# LOOP DO BOT
# ============================================

def bot_loop():
    """Loop principal do trading"""
    global bot_ativo
    contador = 0
    
    while bot_ativo:
        try:
            if contador % 10 == 0:
                print("\n" + "="*50)
                print(f"📊 STATUS — {datetime.now().strftime('%H:%M:%S')}")
                print(f"💰 Saldo: ${trader.get_saldo():.2f}")
                print(f"📈 Posições abertas: {len(trader.get_posicoes())}")

            print("\n🔍 Analisando mercado...")
            resultados = analyzer.monitorar_todos()

            for par, analise in resultados:
                if analise['acao'] == 'COMPRA':
                    print(f"\n🚀 SINAL DE COMPRA — {par}!")
                    trader.comprar(par)
                elif analise['acao'] == 'VENDA':
                    print(f"\n📉 SINAL DE VENDA — {par}!")
                    trader.vender(par, analise['motivo'])

            print(f"\n⏳ Próxima análise em 30 segundos...")
            time.sleep(30)
            contador += 1
            
        except Exception as e:
            print(f"❌ Erro no loop: {e}")
            time.sleep(60)

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════╗
    ║   MEGATRON PRECISION BOT v1.1         ║
    ║   Rodando como Web Service            ║
    ╚═══════════════════════════════════════╝
    """)
    
    # Inicia o bot em thread separada
    bot_thread = Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    
    # Sobe o servidor web (NUNCA termina)
    app.run(host='0.0.0.0', port=10000)