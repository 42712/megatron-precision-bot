"""
Megatron Precision Bot v2.1 — Sistema Percentual
"""
import time
import threading
import os
from datetime import datetime
from flask import Flask, jsonify
from config import (
    MODO_TESTE, PARES, SALDO_INICIAL,
    PERCENTUAL_POR_OPERACAO, TAKE_PROFIT_PCT, STOP_LOSS_PCT,
    TRAILING_STOP_PCT, MAX_PERDA_DIARIA_PCT, MIN_CONFLUENCIA
)
from database import get_estatisticas
from trader import Trader
from analyzer import Analyzer

app = Flask(__name__)
trader = Trader()
analyzer = Analyzer(trader)


@app.route('/')
def home():
    return jsonify({
        'bot': 'Megatron Precision Bot v2.1',
        'status': 'online',
        'modo': 'SIMULAÇÃO' if MODO_TESTE else 'REAL',
        'pares': PARES,
        'configuracao': {
            'por_operacao': f"{PERCENTUAL_POR_OPERACAO*100:.0f}% do saldo",
            'take_profit': f"+{TAKE_PROFIT_PCT*100:.1f}%",
            'stop_loss': f"-{STOP_LOSS_PCT*100:.1f}%",
            'trailing_stop': f"{TRAILING_STOP_PCT*100:.1f}% do topo",
            'perda_diaria_max': f"{MAX_PERDA_DIARIA_PCT*100:.0f}% do saldo",
            'confluencia_min': f"{MIN_CONFLUENCIA}/5 indicadores",
        },
        'hora': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/status')
def status():
    posicoes = trader.get_posicoes()
    saldo = trader.get_saldo()
    limite_perda = SALDO_INICIAL * MAX_PERDA_DIARIA_PCT
    stats = get_estatisticas()
    return jsonify({
        'saldo_atual': round(saldo, 4),
        'saldo_inicial': SALDO_INICIAL,
        'resultado_total': round(saldo - SALDO_INICIAL, 4),
        'resultado_pct': round(((saldo / SALDO_INICIAL) - 1) * 100, 2),
        'posicoes_abertas': len(posicoes),
        'bot_pausado': analyzer.bot_pausado,
        'perda_diaria': round(analyzer.perda_diaria, 4),
        'limite_perda_dia': round(limite_perda, 4),
        'cooldowns': analyzer.cooldown,
        'posicoes': {
            sym: {
                'preco_entrada': dados['preco_compra'],
                'quantidade': round(dados['qtd'], 6),
                'valor_invest': round(dados['valor_investido'], 4),
                'topo': dados.get('topo', dados['preco_compra'])
            }
            for sym, dados in posicoes.items()
        },
        'estatisticas': stats
    })


@app.route('/analise')
def analise():
    resultado = {}
    for par in PARES:
        precos = list(analyzer.historico_precos[par])
        volumes = list(analyzer.historico_volumes[par])
        if len(precos) >= 2:
            from indicators import calcular_confluencia
            a = calcular_confluencia(precos, volumes if volumes else None)
            resultado[par] = {
                'preco': precos[-1],
                'dados_coletados': len(precos),
                'rsi': a['rsi'],
                'macd_hist': a['macd_hist'],
                'bb_pct': a['bb_pct'],
                'volume_ratio': a['volume_ratio'],
                'tendencia_maior': a['tendencia_maior'],
                'pontos_compra': a['pontos_compra'],
                'pontos_venda': a['pontos_venda'],
                'sinal': a['sinal'],
                'faltam_dados': a.get('faltam_dados', 0)
            }
        else:
            resultado[par] = {'status': 'coletando', 'dados': len(precos)}
    return jsonify(resultado)


@app.route('/health')
def health():
    return jsonify({'ok': True}), 200


def bot_loop():
    print("🤖 Bot TURBINADO v2.1 iniciado!")
    contador = 0
    while True:
        try:
            saldo = trader.get_saldo()
            resultado_total = saldo - SALDO_INICIAL
            print(f"\n{'='*50}")
            print(f"🔁 Ciclo #{contador} — {datetime.now().strftime('%H:%M:%S')}")
            print(f"💰 Saldo: ${saldo:.4f} ({resultado_total:+.4f}) | Posições: {len(trader.get_posicoes())}")

            resultados = analyzer.monitorar_todos()

            for par, resultado in resultados:
                acao = resultado.get('acao')
                motivo = resultado.get('motivo', '')

                if acao == 'COMPRA':
                    print(f"\n🚀 COMPRANDO {par}!")
                    print(f"   {motivo}")
                    trader.comprar(par)

                elif acao == 'VENDA':
                    print(f"\n📉 VENDENDO {par}!")
                    print(f"   {motivo}")
                    saldo_antes = trader.get_saldo()
                    trader.vender(par, motivo)
                    saldo_depois = trader.get_saldo()
                    lucro = saldo_depois - saldo_antes
                    analyzer.registrar_resultado(lucro)

            contador += 1
            print(f"\n⏳ Próxima análise em 30s...")
            time.sleep(30)

        except Exception as e:
            print(f"❌ Erro no ciclo: {e}")
            time.sleep(60)


if __name__ == "__main__":
    print(f"""
    ╔══════════════════════════════════════════╗
    ║   MEGATRON PRECISION BOT v2.1            ║
    ║   RSI + EMA + MACD + Bollinger + Volume  ║
    ║   Sistema 100% Percentual                ║
    ╚══════════════════════════════════════════╝

    💰 Saldo inicial: ${SALDO_INICIAL}
    📊 Por operação:  {PERCENTUAL_POR_OPERACAO*100:.0f}% do saldo
    📈 Take Profit:   +{TAKE_PROFIT_PCT*100:.1f}%
    📉 Stop Loss:     -{STOP_LOSS_PCT*100:.1f}%
    🔒 Trailing Stop: {TRAILING_STOP_PCT*100:.1f}% do topo
    🛡️  Perda diária: máx {MAX_PERDA_DIARIA_PCT*100:.0f}%
    🎯 Confluência:   {MIN_CONFLUENCIA}/5 indicadores
    """)

    thread = threading.Thread(target=bot_loop, daemon=True)
    thread.start()
    print("✅ Thread do bot iniciada com sucesso!")

    # PORTA CORRIGIDA PARA O RENDER
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
