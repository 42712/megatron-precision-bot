"""
Megatron Precision Bot — Web Service (Flask 3.1 + Python 3.14 compatível)
"""
import time
import threading
from datetime import datetime
from flask import Flask, jsonify
from config import MODO_TESTE, PARES, SALDO_INICIAL
from database import get_estatisticas
from trader import Trader
from analyzer import Analyzer

# ============================================
# INICIALIZAÇÃO
# ============================================
app = Flask(__name__)
trader = Trader()
analyzer = Analyzer(trader)

# ============================================
# ROTAS WEB (para o Render manter o serviço vivo)
# ============================================
@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'bot': 'Megatron Precision Bot v1.1',
        'modo': 'SIMULAÇÃO' if MODO_TESTE else 'REAL',
        'pares': PARES,
        'hora': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/status')
def status():
    posicoes = trader.get_posicoes()
    stats = get_estatisticas()
    return jsonify({
        'saldo': round(trader.get_saldo(), 2),
        'posicoes_abertas': len(posicoes),
        'detalhes': {
            sym: {
                'preco_compra': dados['preco_compra'],
                'quantidade': dados['qtd']
            }
            for sym, dados in posicoes.items()
        },
        'estatisticas': stats
    })

@app.route('/health')
def health():
    return jsonify({'ok': True}), 200

# ============================================
# LOOP DO BOT (roda em thread separada)
# ============================================
def bot_loop():
    """Loop principal do bot rodando em background"""
    print("🤖 Thread do bot iniciada!")
    contador = 0

    while True:
        try:
            print(f"\n{'='*50}")
            print(f"🔁 Ciclo #{contador} — {datetime.now().strftime('%H:%M:%S')}")
            print(f"💰 Saldo: ${trader.get_saldo():.2f} | Posições: {len(trader.get_posicoes())}")

            resultados = analyzer.monitorar_todos()

            for par, analise in resultados:
                if analise['acao'] == 'COMPRA':
                    print(f"\n🚀 SINAL DE COMPRA — {par}! Motivo: {analise['motivo']}")
                    trader.comprar(par)
                elif analise['acao'] == 'VENDA':
                    print(f"\n📉 SINAL DE VENDA — {par}! Motivo: {analise['motivo']}")
                    trader.vender(par, analise['motivo'])

            contador += 1
            print(f"\n⏳ Próxima análise em 30 segundos...")
            time.sleep(30)

        except Exception as e:
            print(f"❌ Erro no ciclo do bot: {e}")
            time.sleep(60)

# ============================================
# ENTRY POINT
# ============================================
if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════╗
    ║   MEGATRON PRECISION BOT v1.1         ║
    ║   Flask 3.1 + Python 3.14             ║
    ╚═══════════════════════════════════════╝
    """)
    print(f"📌 Modo: {'🔵 SIMULAÇÃO' if MODO_TESTE else '🔴 REAL'}")
    print(f"🎯 Pares: {', '.join(PARES)}")

    # Inicia o bot em thread daemon
    thread = threading.Thread(target=bot_loop, daemon=True)
    thread.start()
    print("✅ Thread do bot iniciada com sucesso!")

    # Sobe o servidor web na porta 10000 (padrão do Render)
    app.run(host='0.0.0.0', port=10000, debug=False)
