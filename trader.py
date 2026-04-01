from binance.client import Client
from config import *
from database import salvar_trade
import time

client = Client(BINANCE_KEY, BINANCE_SECRET)

def get_preco(symbol):
    return float(client.get_symbol_ticker(symbol=symbol)["price"])

def comprar(symbol):
    client.order_market_buy(symbol=symbol, quoteOrderQty=VALOR_COMPRA)
    preco_compra = get_preco(symbol)
    monitorar(symbol, preco_compra)

def vender(symbol, preco_compra):
    balance = client.get_asset_balance(asset=symbol.replace("USDT",""))
    qtd = float(balance["free"])

    if qtd > 0:
        client.order_market_sell(symbol=symbol, quantity=qtd)
        preco_venda = get_preco(symbol)
        salvar_trade(symbol, preco_compra, preco_venda)

def monitorar(symbol, preco_compra):
    topo = preco_compra

    while True:
        preco = get_preco(symbol)

        if preco > topo:
            topo = preco

        if preco >= preco_compra * TAKE_PROFIT:
            vender(symbol, preco_compra)
            break

        if preco <= preco_compra * STOP_LOSS:
            vender(symbol, preco_compra)
            break

        if preco < topo * (1 - TRAILING):
            vender(symbol, preco_compra)
            break

        time.sleep(5)
