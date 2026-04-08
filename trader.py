import time
from database import salvar_trade
from config import *

# 💰 SIMULAÇÃO DE SALDO
saldo = 100
ativos = {}

def get_preco_fake(symbol):
    import random
    return random.uniform(0.5, 1.5)

def comprar(symbol):
    global saldo

    if saldo < VALOR_COMPRA:
        print("❌ Saldo insuficiente")
        return

    preco = get_preco_fake(symbol)
    qtd = VALOR_COMPRA / preco

    ativos[symbol] = {
        "preco_compra": preco,
        "qtd": qtd
    }

    saldo -= VALOR_COMPRA

    print(f"🟢 COMPRA SIMULADA: {symbol} a {preco:.4f}")
    monitorar(symbol)

def vender(symbol):
    global saldo

    if symbol not in ativos:
        return

    preco = get_preco_fake(symbol)
    dados = ativos[symbol]

    valor = preco * dados["qtd"]
    lucro = valor - VALOR_COMPRA

    saldo += valor

    print(f"🔴 VENDA SIMULADA: {symbol} a {preco:.4f}")
    print(f"💰 Lucro: {lucro:.2f}")

    salvar_trade(symbol, dados["preco_compra"], preco)

    del ativos[symbol]

def monitorar(symbol):
    dados = ativos[symbol]
    preco_compra = dados["preco_compra"]
    topo = preco_compra

    while True:
        preco = get_preco_fake(symbol)

        if preco > topo:
            topo = preco

        if preco >= preco_compra * TAKE_PROFIT:
            print("💰 Take Profit")
            vender(symbol)
            break

        if preco <= preco_compra * STOP_LOSS:
            print("🛑 Stop Loss")
            vender(symbol)
            break

        if preco