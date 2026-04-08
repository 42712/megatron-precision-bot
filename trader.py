import time
import random
from database import salvar_trade
from config import *
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

# ============================================
# 🔐 CONEXÃO REAL COM A BINANCE
# ============================================
try:
    client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
    # Testa conexão
    status = client.get_system_status()
    print("✅ Conectado à Binance")
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
    exit(1)

# ============================================
# 💰 CONFIGURAÇÕES
# ============================================
saldo = 100
ativos = {}

# Controle de rate limiting (evita bloqueio)
ULTIMA_REQUISICAO = 0
MIN_INTERVALO = 0.1  # 100ms entre requisições (10 por segundo)

# ============================================
# 🛡️ FUNÇÃO ANTI-BLOQUEIO
# ============================================
def aguardar_rate_limit():
    """Respeita os limites da Binance para não ser bloqueado"""
    global ULTIMA_REQUISICAO
    agora = time.time()
    tempo_decorrido = agora - ULTIMA_REQUISICAO
    if tempo_decorrido < MIN_INTERVALO:
        time.sleep(MIN_INTERVALO - tempo_decorrido)
    ULTIMA_REQUISICAO = time.time()

def get_preco_real(symbol):
    """Obtém preço real da Binance com retry automático"""
    for tentativa in range(3):  # 3 tentativas
        try:
            aguardar_rate_limit()
            
            # Formata o símbolo corretamente (ex: "BTCUSDT")
            symbol_formatted = symbol.replace("/", "").upper()
            
            ticker = client.get_symbol_ticker(symbol=symbol_formatted)
            preco = float(ticker['price'])
            print(f"📊 {symbol}: R$ {preco:.4f}")
            return preco
            
        except BinanceAPIException as e:
            if e.code == -1003:  # Rate limit excedido
                print(f"⏳ Rate limit, aguardando 1s... (tentativa {tentativa+1}/3)")
                time.sleep(1)
            else:
                print(f"⚠️ Erro Binance: {e}")
                return None
        except BinanceRequestException as e:
            print(f"⚠️ Erro de rede: {e}")
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Erro inesperado: {e}")
            return None
    
    print("❌ Falha ao obter preço após 3 tentativas")
    return None

# ============================================
# 🚀 FUNÇÕES DE EXECUÇÃO REAL
# ============================================
def comprar(symbol):
    global saldo
    
    if saldo < VALOR_COMPRA:
        print(f"❌ Saldo insuficiente: R$ {saldo:.2f}")
        return
    
    preco = get_preco_real(symbol)
    if not preco:
        return
    
    # CALCULA QUANTIDADE REAL (respeitando lotes mínimos da Binance)
    qtd = VALOR_COMPRA / preco
    
    # OPÇÃO 1: APENAS SIMULAÇÃO (sem ordem real)
    print(f"\n🟢 ORDEM DE COMPRA SIMULADA:")
    print(f"   Símbolo: {symbol}")
    print(f"   Preço: R$ {preco:.4f}")
    print(f"   Quantidade: {qtd:.6f}")
    print(f"   Valor: R$ {VALOR_COMPRA:.2f}")
    
    # OPÇÃO 2: ORDEM REAL (descomente para usar dinheiro de verdade)
    """
    try:
        aguardar_rate_limit()
        order = client.order_market_buy(
            symbol=symbol.replace("/", "").upper(),
            quantity=round(qtd, 6)  # Ajustar casas decimais
        )
        print(f"✅ ORDEM REAL EXECUTADA: {order}")
        preco = float(order['fills'][0]['price'])
    except Exception as e:
        print(f"❌ Erro na ordem real: {e}")
        return
    """
    
    # Registra o ativo
    ativos[symbol] = {
        "preco_compra": preco,
        "qtd": qtd,
        "topo": preco
    }
    
    saldo -= VALOR_COMPRA
    print(f"💼 Saldo restante: R$ {saldo:.2f}")
    
    # Inicia monitoramento
    monitorar(symbol)

def vender(symbol):
    global saldo
    
    if symbol not in ativos:
        return
    
    preco = get_preco_real(symbol)
    if not preco:
        return
    
    dados = ativos[symbol]
    valor = preco * dados["qtd"]
    lucro = valor - VALOR_COMPRA
    lucro_percentual = (lucro / VALOR_COMPRA) * 100
    
    # OPÇÃO 2: ORDEM REAL (descomente para usar dinheiro de verdade)
    """
    try:
        aguardar_rate_limit()
        order = client.order_market_sell(
            symbol=symbol.replace("/", "").upper(),
            quantity=round(dados["qtd"], 6)
        )
        print(f"✅ VENDA REAL EXECUTADA")
    except Exception as e:
        print(f"❌ Erro na venda real: {e}")
        return
    """
    
    saldo += valor
    
    print(f"\n🔴 VENDA SIMULADA: {symbol}")
    print(f"   Preço compra: R$ {dados['preco_compra']:.4f}")
    print(f"   Preço venda: R$ {preco:.4f}")
    print(f"   Lucro: R$ {lucro:.2f} ({lucro_percentual:.2f}%)")
    print(f"   Saldo atual: R$ {saldo:.2f}")
    
    # Salva no banco de dados
    salvar_trade(symbol, dados["preco_compra"], preco)
    
    del ativos[symbol]

def monitorar(symbol):
    dados = ativos[symbol]
    preco_compra = dados["preco_compra"]
    topo = dados["topo"]
    
    print(f"\n🔍 Monitorando {symbol}...")
    print(f"   Preço compra: R$ {preco_compra:.4f}")
    print(f"   Take Profit: R$ {preco_compra * TAKE_PROFIT:.4f}")
    print(f"   Stop Loss: R$ {preco_compra * STOP_LOSS:.4f}")
    
    while True:
        preco = get_preco_real(symbol)
        if not preco:
            time.sleep(1)
            continue
        
        # Atualiza topo
        if preco > topo:
            topo = preco
            print(f"📈 Novo topo: R$ {topo:.4f}")
        
        # Verifica condições
        if preco >= preco_compra * TAKE_PROFIT:
            print(f"💰 Take Profit atingido!")
            vender(symbol)
            break
        
        if preco <= preco_compra * STOP_LOSS:
            print(f"🛑 Stop Loss atingido!")
            vender(symbol)
            break
        
        # Aguarda próximo ciclo
        time.sleep(1)  # Verifica a cada 1 segundo

# ============================================
# 🚀 MAIN
# ============================================
if __name__ == "__main__":
    print("=== BOT TRADING BINANCE ===\n")
    
    # Exemplo de uso
    comprar("BTC/USDT")
    
    # Mantém o bot rodando
    while True:
        time.sleep(1)