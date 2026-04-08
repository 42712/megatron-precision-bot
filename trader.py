from binance.client import Client
from config import *
from database import salvar_trade
import time

# 🔥 CONFIGURAÇÃO DA BINANCE (AJUSTADA)
client = Client(
    BINANCE_KEY,
    BINANCE_SECRET,
    tld='com',
    testnet=False  # ⚠️ Se der erro, mudar para True
)

def get_preco(symbol):
    return float(client.get_symbol_ticker(symbol=symbol)["price"])

def comprar(symbol):
    try:
        print(f"🟢 Comprando {symbol}...")

        order = client.order_market_buy(
            symbol=symbol,
            quoteOrderQty=VALOR_COMPRA
        )

        preco_compra = get_preco(symbol)
        print(f"✅ Compra feita: {preco_compra}")

        monitorar(symbol, preco_compra)

    except Exception as e:
        print(f"❌ Erro ao comprar {symbol}: {e}")

def vender(symbol, preco_compra):
    try:
        asset = symbol.replace("USDT", "")
        balance = client.get_asset_balance(asset=asset)

        qtd = float(balance["free"])

        if qtd > 0:
            client.order_market_sell(
                symbol=symbol,
                quantity=qtd
            )

            preco_venda = get_preco(symbol)
            print(f"🔴 Venda realizada: {preco_venda}")

            salvar_trade(symbol, preco_compra, preco_venda)

    except Exception as e:
        print(f"❌ Erro ao vender {symbol}: {e}")

def monitorar(symbol, preco_compra):
    topo = preco_compra

    print(f"📊 Monitorando {symbol}...")

    while True:
        try:
            preco = get_preco(symbol)

            if preco > topo:
                topo = preco

            # 🎯 TAKE PROFIT
            if preco >= preco_compra * TAKE_PROFIT:
                print("💰 Take Profit atingido")
                vender(symbol, preco_compra)
                break

            # 🛑 STOP LOSS
            if preco <= preco_compra * STOP_LOSS:
                print("🛑 Stop Loss acionado")
                vender(symbol, preco_compra)
                break

            # 📉 TRAILING STOP
            if preco < topo * (1 - TRAILING):
                print("📉 Trailing Stop acionado")
                vender(symbol, preco_compra)
                break

            time.sleep(5)

        except Exception as e:
            print(f"⚠️ Erro no monitoramento: {e}")
            time.sleep(5)