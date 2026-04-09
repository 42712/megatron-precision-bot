"""
Bot de Trading Binance - Main Entry Point
"""
import time
import sys
from datetime import datetime
from config import MODO_TESTE, PARES, VALOR_COMPRA, TAKE_PROFIT, STOP_LOSS, SALDO_INICIAL
from database import get_estatisticas
from trader import Trader
from analyzer import Analyzer


# ============================================
# FUNÇÕES DE INTERFACE
# ============================================
def mostrar_banner():
    print("""
    ╔═══════════════════════════════════════╗
    ║   MEGATRON PRECISION BOT v1.1         ║
    ║   Estratégia: RSI + EMA + TP/SL       ║
    ╚═══════════════════════════════════════╝
    """)

def mostrar_config():
    print(f"📌 Modo: {'🔵 SIMULAÇÃO' if MODO_TESTE else '🔴 REAL'}")
    print(f"🎯 Pares: {', '.join(PARES)}")
    print(f"💰 Valor por operação: ${VALOR_COMPRA:.2f}")
    print(f"📈 Take Profit: +{(TAKE_PROFIT-1)*100:.1f}%")
    print(f"📉 Stop Loss: -{(1-STOP_LOSS)*100:.1f}%")
    print(f"💾 Banco de dados: trades.db\n")

def mostrar_status(trader, analyzer):
    print("\n" + "="*50)
    print(f"📊 STATUS — {datetime.now().strftime('%H:%M:%S')}")
    print(f"💰 Saldo: ${trader.get_saldo():.2f}")
    print(f"📈 Posições abertas: {len(trader.get_posicoes())}")

    for sym, dados in trader.get_posicoes().items():
        preco_atual = trader.get_preco(sym)
        if preco_atual:
            lucro_pct = ((preco_atual / dados['preco_compra']) - 1) * 100
            print(f"   {sym}: {lucro_pct:+.2f}%")

    stats = get_estatisticas()
    if stats:
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   Total trades: {stats['total_trades']}")
        print(f"   Lucro total: ${stats['lucro_total']}")
        print(f"   Taxa de acerto: {stats['taxa_acerto']}%")

    print("="*50)

def executar_estrategia(trader, analyzer):
    print("\n🔍 Analisando mercado...")
    resultados = analyzer.monitorar_todos()

    for par, analise in resultados:
        if analise['acao'] == 'COMPRA':
            print(f"\n🚀 SINAL DE COMPRA — {par}!")
            print(f"   Motivo: {analise['motivo']}")
            trader.comprar(par)

        elif analise['acao'] == 'VENDA':
            print(f"\n📉 SINAL DE VENDA — {par}!")
            print(f"   Motivo: {analise['motivo']}")
            trader.vender(par, analise['motivo'])


# ============================================
# MAIN
# ============================================
def main():
    mostrar_banner()
    mostrar_config()

    trader = Trader()
    analyzer = Analyzer(trader)

    print("✅ Bot iniciado com sucesso!")
    print("⚠️  Pressione Ctrl+C para parar\n")

    contador = 0

    try:
        while True:
            if contador % 10 == 0:
                mostrar_status(trader, analyzer)

            executar_estrategia(trader, analyzer)

            print(f"\n⏳ Próxima análise em 30 segundos...")
            time.sleep(30)
            contador += 1

    except KeyboardInterrupt:
        print("\n\n🛑 Bot interrompido pelo usuário")

        if trader.get_posicoes():
            print("🔒 Fechando posições abertas...")
            for symbol in list(trader.get_posicoes().keys()):
                trader.vender(symbol, "ENCERRAMENTO MANUAL")

        mostrar_status(trader, analyzer)

        saldo_final = trader.get_saldo()
        resultado = saldo_final - SALDO_INICIAL  # ✅ SALDO_INICIAL agora importado corretamente
        print(f"\n✅ Bot encerrado!")
        print(f"💰 Saldo final: ${saldo_final:.2f}")
        print(f"📈 Resultado: ${resultado:+.2f}")
        sys.exit(0)


if __name__ == "__main__":
    main()
