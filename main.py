"""
Bot de Trading Binance - Main Entry Point
"""
import time
import sys
from datetime import datetime
from config import MODO_TESTE, PARES, VALOR_COMPRA, TAKE_PROFIT, STOP_LOSS
from database import get_estatisticas
from trader import Trader
from analyzer import Analyzer

# ============================================
# FUNÇÕES DE INTERFACE
# ============================================
def mostrar_banner():
    """Mostra banner inicial"""
    print("""
    ╔═══════════════════════════════════════╗
    ║   BOT TRADING BINANCE v1.0            ║
    ║   Estratégia: RSI + EMA + TP/SL       ║
    ╚═══════════════════════════════════════╝
    """)

def mostrar_config():
    """Mostra configurações atuais"""
    print(f"📌 Modo: {'🔵 SIMULAÇÃO' if MODO_TESTE else '🔴 REAL'}")
    print(f"🎯 Pares: {', '.join(PARES)}")
    print(f"💰 Valor por operação: R$ {VALOR_COMPRA}")
    print(f"📈 Take Profit: +{(TAKE_PROFIT-1)*100:.1f}%")
    print(f"📉 Stop Loss: -{(1-STOP_LOSS)*100:.1f}%")
    print(f"💾 Banco de dados: trades.db\n")

def mostrar_status(trader, analyzer):
    """Mostra status atual"""
    print("\n" + "="*50)
    print(f"📊 STATUS - {datetime.now().strftime('%H:%M:%S')}")
    print(f"💰 Saldo: R$ {trader.get_saldo():.2f}")
    print(f"📈 Posições: {len(trader.get_posicoes())}")
    
    if trader.get_posicoes():
        for sym, dados in trader.get_posicoes().items():
            preco_atual = trader.get_preco(sym)
            if preco_atual:
                lucro_percentual = ((preco_atual / dados['preco_compra']) - 1) * 100
                print(f"   {sym}: {lucro_percentual:+.2f}%")
    
    # Estatísticas
    stats = get_estatisticas()
    if stats:
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   Total trades: {stats['total_trades']}")
        print(f"   Lucro total: R$ {stats['lucro_total']}")
        print(f"   Taxa acerto: {stats['taxa_acerto']}%")
    
    print("="*50)

def executar_estrategia(trader, analyzer):
    """Executa a lógica principal do bot"""
    print("\n🔍 Iniciando análise de mercado...")
    
    # Analisa todos os pares
    resultados = analyzer.monitorar_todos()
    
    # Executa ações baseadas na análise
    for par, analise in resultados:
        if analise['acao'] == 'COMPRA':
            print(f"\n🚀 SINAL DE COMPRA para {par}!")
            print(f"   Motivo: {analise['motivo']}")
            trader.comprar(par)
        
        elif analise['acao'] == 'VENDA':
            print(f"\n📉 SINAL DE VENDA para {par}!")
            print(f"   Motivo: {analise['motivo']}")
            trader.vender(par, analise['motivo'])

# ============================================
# MAIN
# ============================================
def main():
    """Função principal"""
    mostrar_banner()
    mostrar_config()
    
    # Inicializa módulos
    trader = Trader()
    analyzer = Analyzer(trader)
    
    print("✅ Bot iniciado com sucesso!")
    print("⚠️ Pressione Ctrl+C para parar\n")
    
    contador = 0
    
    try:
        while True:
            # Mostra status a cada 10 ciclos
            if contador % 10 == 0:
                mostrar_status(trader, analyzer)
            
            # Executa estratégia
            executar_estrategia(trader, analyzer)
            
            # Aguarda próximo ciclo
            print(f"\n⏳ Aguardando 30 segundos para próxima análise...")
            time.sleep(30)
            contador += 1
            
    except KeyboardInterrupt:
        print("\n\n🛑 Bot interrompido pelo usuário")
        
        # Fecha posições abertas
        if trader.get_posicoes():
            print("🔒 Fechando posições abertas...")
            for symbol in list(trader.get_posicoes().keys()):
                trader.vender(symbol, "ENCERRAMENTO MANUAL")
        
        # Mostra resultado final
        mostrar_status(trader, analyzer)
        
        saldo_final = trader.get_saldo()
        print(f"\n✅ Bot encerrado!")
        print(f"💰 Saldo final: R$ {saldo_final:.2f}")
        print(f"📈 Resultado: R$ {saldo_final - SALDO_INICIAL:+.2f}")
        sys.exit(0)

if __name__ == "__main__":
    main()