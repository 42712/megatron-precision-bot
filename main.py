"""
Megatron Precision Bot v2.2 — Railway
- Binance.com funciona (servidores fora dos EUA)
- Keep-alive thread
- Porta dinâmica via $PORT (padrão Railway)
"""
import time
import threading
import requests
import os
from datetime import datetime
from flask import Flask, jsonify
from config import (
    MODO_TESTE, PARES, SALDO_INICIAL,
    PERCENTUAL_POR_OPERACAO, TAKE_PROFIT_PCT, STOP_LOSS_PCT,
    TRAILING_STOP_PCT, MAX_PERDA_DIARIA_PCT, MIN_CONFLUENCIA,
    KEEPALIVE_INTERVALO, RAILWAY_PUBLIC_URL, BINANCE_TLD
)
from database import get_estatisticas
from trader import Trader
from analyzer import Analyzer

app      = Flask(__name__)
trader   = Trader()
analyzer = Analyzer(trader)

# ============================================
# ROTAS
# ============================================

@app.route('/')
def home():
    return jsonify({
        'bot':    'Megatron Precision Bot v2.2',
        'status': 'online ✅',
        'modo':   '🔵 SIMULAÇÃO' if MODO_TESTE else '🔴 REAL',
        'exchange': f'Binance.{BINANCE_TLD.upper()}',
        'pares':  PARES,
        'config': {
            'por_operacao':     f"{PERCENTUAL_POR_OPERACAO*100:.0f}% do saldo",
            'take_profit':      f"+{TAKE_PROFIT_PCT*100:.1f}%",
            'stop_loss':        f"-{STOP_LOSS_PCT*100:.1f}%",
            'trailing_stop':    f"{TRAILING_STOP_PCT*100:.1f}% do topo",
            'perda_diaria_max': f"{MAX_PERDA_DIARIA_PCT*100:.0f}% do saldo",
            'confluencia_min':  f"{MIN_CONFLUENCIA}/5",
        },
        'hora': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/status')
def status():
    posicoes     = trader.get_posicoes()
    saldo        = trader.get_saldo()
    limite_perda = SALDO_INICIAL * MAX_PERDA_DIARIA_PCT
    return jsonify({
        'saldo_atual':      round(saldo, 4),
        'saldo_inicial':    SALDO_INICIAL,
        'resultado_total':  round(saldo - SALDO_INICIAL, 4),
        'resultado_pct':    round(((saldo / SALDO_INICIAL) - 1) * 100, 2),
        'posicoes_abertas': len(posicoes),
        'bot_pausado':      analyzer.bot_pausado,
        'perda_diaria':     round(analyzer.perda_diaria, 4),
        'limite_perda_dia': round(limite_perda, 4),
        'cooldowns':        analyzer.cooldown,
        'posicoes': {
            sym: {
                'preco_entrada':  dados['preco_compra'],
                'quantidade':     round(dados['qtd'], 6),
                'valor_investido':round(dados['valor_investido'], 4),
                'topo':           dados.get('topo', dados['preco_compra'])
            }
            for sym, dados in posicoes.items()
        },
        'estatisticas': get_estatisticas()
    })

@app.route('/analise')
def analise():
    resultado = {}
    for par in PARES:
        precos  = list(analyzer.historico_precos[par])
        volumes = list(analyzer.historico_volumes[par])
        if len(precos) >= 2:
            from indicators import calcular_confluencia
            a = calcular_confluencia(precos, volumes if volumes else None)
            resultado[par] = {
                'preco':           precos[-1],
                'dados_coletados': len(precos),
                'rsi':             a.get('rsi', 50),
                'macd_hist':       a.get('macd_hist', 0),
                'bb_pct':          a.get('bb_pct', 0.5),
                'volume_ratio':    a.get('volume_ratio', 1.0),
                'tendencia_maior': a.get('tendencia_maior', '?'),
                'pontos_compra':   a.get('pontos_compra', 0),
                'pontos_venda':    a.get('pontos_venda', 0),
                'sinal':           a.get('sinal', 'AGUARDAR'),
                'faltam_dados':    a.get('faltam_dados', 0)
            }
        else:
            resultado[par] = {'status': 'coletando', 'dados': len(precos)}
    return jsonify(resultado)

@app.route('/health')
def health():
    return jsonify({'ok': True}), 200

# ============================================
# KEEP-ALIVE — mantém o serviço acordado
# ============================================

def keepalive_loop():
    time.sleep(30)  # aguarda subir

    # Railway expõe a URL via variável RAILWAY_PUBLIC_DOMAIN
    domain = RAILWAY_PUBLIC_URL
    if domain:
        url = f"https://{domain}/health"
    else:
        port = int(os.environ.get("PORT", 8080))
        url  = f"http://127.0.0.1:{port}/health"

    print(f"💓 Keep-alive ativo → ping a cada {KEEPALIVE_INTERVALO}s em {url}")

    while True:
        try:
            r = requests.get(url, timeout=10)
            print(f"💓 Keep-alive [{datetime.now().strftime('%H:%M:%S')}] → {r.status_code}")
        except Exception as e:
            print(f"💓 Keep-alive erro: {e}")
        time.sleep(KEEPALIVE_INTERVALO)

# ============================================
# LOOP DO BOT
# ============================================

def bot_loop():
    print("🤖 Bot v2.2 Railway iniciado!")
    contador = 0
    while True:
        try:
            saldo = trader.get_saldo()
            print(f"\n{'='*50}")
            print(f"🔁 Ciclo #{contador} — {datetime.now().strftime('%H:%M:%S')}")
            print(f"💰 Saldo: ${saldo:.4f} ({saldo - SALDO_INICIAL:+.4f}) | Posições: {len(trader.get_posicoes())}")

            resultados = analyzer.monitorar_todos()

            for par, resultado in resultados:
                acao   = resultado.get('acao')
                motivo = resultado.get('motivo', '')

                if acao == 'COMPRA':
                    print(f"\n🚀 COMPRANDO {par}! {motivo}")
                    trader.comprar(par)

                elif acao == 'VENDA':
                    print(f"\n📉 VENDENDO {par}! {motivo}")
                    saldo_antes = trader.get_saldo()
                    trader.vender(par, motivo)
                    lucro = trader.get_saldo() - saldo_antes
                    analyzer.registrar_resultado(lucro)

            contador += 1
            print(f"\n⏳ Próxima análise em 30s...")
            time.sleep(30)

        except Exception as e:
            print(f"❌ Erro no ciclo: {e}")
            time.sleep(60)

# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    print(f"""
    ╔══════════════════════════════════════════╗
    ║   MEGATRON PRECISION BOT v2.2            ║
    ║   🚂 Railway | Binance.{BINANCE_TLD.upper():<16}  ║
    ║   RSI+EMA+MACD+Bollinger+Volume          ║
    ╚══════════════════════════════════════════╝
    💰 Saldo: ${SALDO_INICIAL} | Por operação: {PERCENTUAL_POR_OPERACAO*100:.0f}%
    📈 TP: +{TAKE_PROFIT_PCT*100:.1f}% | SL: -{STOP_LOSS_PCT*100:.1f}% | Trail: {TRAILING_STOP_PCT*100:.1f}%
    🎯 Confluência: {MIN_CONFLUENCIA}/5 | Modo: {'🔵 SIM' if MODO_TESTE else '🔴 REAL'}
    """)

    # Thread do bot
    threading.Thread(target=bot_loop,       daemon=True).start()
    # Thread keep-alive
    threading.Thread(target=keepalive_loop, daemon=True).start()

    print("✅ Threads iniciadas! Bot + Keep-alive")

    # Railway usa variável PORT dinamicamente
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
