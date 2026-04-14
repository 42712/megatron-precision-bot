"""
Módulo de Execução de Trades — Sistema Percentual
"""
import time
import random
from config import (
    MODO_TESTE, SALDO_INICIAL,
    PERCENTUAL_POR_OPERACAO, SALDO_MINIMO_PCT,
    MIN_INTERVALO, BINANCE_API_KEY, BINANCE_SECRET_KEY
)
from database import salvar_trade, salvar_saldo


class Trader:
    def __init__(self):
        self.client = None
        self.saldo = SALDO_INICIAL
        self.ativos = {}
        self.ultima_requisicao = 0

        if not MODO_TESTE:
            try:
                from binance.client import Client
                self.client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
                print("✅ Binance conectada (MODO REAL)")
                self._sincronizar_saldo_real()
            except Exception as e:
                print(f"⚠️ Erro ao conectar Binance: {e}")
                print("   Continuando em modo SIMULAÇÃO")
        else:
            print("🔵 Modo SIMULAÇÃO ativo")

    def _sincronizar_saldo_real(self):
        try:
            conta = self.client.get_account()
            for ativo in conta['balances']:
                if ativo['asset'] == 'USDT':
                    self.saldo = float(ativo['free'])
                    print(f"💰 Saldo real: ${self.saldo:.2f}")
                    return
        except Exception as e:
            print(f"⚠️ Erro sincronização: {e}")

    def aguardar_rate_limit(self):
        agora = time.time()
        decorrido = agora - self.ultima_requisicao
        if decorrido < MIN_INTERVALO:
            time.sleep(MIN_INTERVALO - decorrido)
        self.ultima_requisicao = time.time()

    def calcular_valor_operacao(self):
        saldo_em_posicoes = sum(dados['valor_investido'] for dados in self.ativos.values())
        saldo_livre = self.saldo - saldo_em_posicoes
        valor = saldo_livre * PERCENTUAL_POR_OPERACAO
        
        MINIMO_BINANCE = 11.0 if not MODO_TESTE else 1.0
        
        if valor < MINIMO_BINANCE:
            return None, f"Valor ${valor:.2f} abaixo do mínimo (${MINIMO_BINANCE:.2f})"
        return round(valor, 2), None

    def saldo_acima_minimo(self):
        minimo = SALDO_INICIAL * SALDO_MINIMO_PCT
        return self.saldo >= minimo

    def get_preco(self, symbol):
        if MODO_TESTE or not self.client:
            bases = {"BTCUSDT": 85000, "ETHUSDT": 2000, "BNBUSDT": 600}
            base = bases.get(symbol, 100)
            preco = base * (1 + random.uniform(-0.01, 0.01))
            return preco
        
        try:
            self.aguardar_rate_limit()
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            print(f"❌ Erro ao obter preço {symbol}: {e}")
            return None

    def comprar(self, symbol):
        if not self.saldo_acima_minimo():
            minimo = SALDO_INICIAL * SALDO_MINIMO_PCT
            print(f"🛑 Saldo (${self.saldo:.2f}) abaixo do mínimo (${minimo:.2f})")
            return False

        valor_operacao, erro = self.calcular_valor_operacao()
        if erro:
            print(f"❌ {erro}")
            return False

        preco = self.get_preco(symbol)
        if not preco:
            return False

        qtd = valor_operacao / preco

        print(f"\n🟢 COMPRA: {symbol}")
        print(f"   Valor ({PERCENTUAL_POR_OPERACAO*100:.0f}%): ${valor_operacao:.2f}")
        print(f"   Preço: ${preco:.4f} | Qtd: {qtd:.6f}")

        if not MODO_TESTE and self.client:
            try:
                self.aguardar_rate_limit()
                resultado = self.client.order_market_buy(
                    symbol=symbol,
                    quantity=round(qtd, 6)
                )
                preco = float(resultado['fills'][0]['price'])
                print(f"✅ COMPRA EXECUTADA @ ${preco:.4f}")
            except Exception as e:
                print(f"❌ Erro na compra: {e}")
                return False

        self.ativos[symbol] = {
            "preco_compra": preco,
            "qtd": qtd,
            "topo": preco,
            "valor_investido": valor_operacao
        }
        self.saldo -= valor_operacao
        print(f"💼 Saldo restante: ${self.saldo:.2f}")
        salvar_saldo(self.saldo)
        return True

    def vender(self, symbol, motivo="TP/SL"):
        if symbol not in self.ativos:
            return False

        preco = self.get_preco(symbol)
        if not preco:
            return False

        dados = self.ativos[symbol]
        valor_recebido = preco * dados["qtd"]
        valor_investido = dados["valor_investido"]
        lucro = valor_recebido - valor_investido
        lucro_pct = (lucro / valor_investido) * 100

        print(f"\n🔴 VENDA ({motivo}): {symbol}")
        print(f"   Comprado @ ${dados['preco_compra']:.4f} → Vendido @ ${preco:.4f}")
        print(f"   Resultado: ${lucro:+.2f} ({lucro_pct:+.2f}%)")

        if not MODO_TESTE and self.client:
            try:
                self.aguardar_rate_limit()
                self.client.order_market_sell(
                    symbol=symbol,
                    quantity=round(dados["qtd"], 6)
                )
                print("✅ VENDA EXECUTADA")
            except Exception as e:
                print(f"❌ Erro na venda: {e}")
                return False

        self.saldo += valor_recebido
        salvar_trade(symbol, dados["preco_compra"], preco, dados["qtd"], motivo)
        salvar_saldo(self.saldo)
        del self.ativos[symbol]

        print(f"💼 Novo saldo: ${self.saldo:.2f}")
        return True

    def get_saldo(self):
        return self.saldo

    def get_posicoes(self):
        return self.ativos


print("✅ Trader carregado!")
