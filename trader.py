"""
Módulo de Execução de Trades — Sistema Percentual
Valor por operação = % do saldo atual (se adapta ao saldo que você tem)
"""
import time
from config import (
    MODO_TESTE, SALDO_INICIAL,
    PERCENTUAL_POR_OPERACAO, SALDO_MINIMO_PCT,
    MIN_INTERVALO, BINANCE_API_KEY, BINANCE_SECRET_KEY
)
from database import salvar_trade, salvar_saldo
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException


class Trader:
    def __init__(self):
        self.client = None
        self.saldo  = SALDO_INICIAL
        self.ativos = {}
        self.ultima_requisicao  = 0
        self._requisicoes_minuto = 0
        self._inicio_minuto      = time.time()

        if not MODO_TESTE:
            self.conectar_binance()

    # ============================================
    # CONEXÃO
    # ============================================

    def conectar_binance(self):
        for tentativa in range(3):
            try:
                self.client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
                status = self.client.get_system_status()
                print(f"✅ Binance conectada | Status: {status}")
                # Sincroniza saldo real
                self._sincronizar_saldo_real()
                return True
            except Exception as e:
                print(f"❌ Tentativa {tentativa+1}/3: {e}")
                time.sleep(2 ** tentativa)
        print("❌ Falha ao conectar à Binance.")
        return False

    def _sincronizar_saldo_real(self):
        """Busca saldo USDT real da conta Binance"""
        try:
            conta = self.client.get_account()
            for ativo in conta['balances']:
                if ativo['asset'] == 'USDT':
                    self.saldo = float(ativo['free'])
                    print(f"💰 Saldo USDT real: ${self.saldo:.2f}")
                    return
        except Exception as e:
            print(f"⚠️ Não foi possível sincronizar saldo: {e}")

    # ============================================
    # RATE LIMITING
    # ============================================

    def aguardar_rate_limit(self):
        agora = time.time()
        decorrido = agora - self.ultima_requisicao
        if decorrido < MIN_INTERVALO:
            time.sleep(MIN_INTERVALO - decorrido)

        agora = time.time()
        if agora - self._inicio_minuto >= 60:
            self._requisicoes_minuto = 0
            self._inicio_minuto = agora

        self._requisicoes_minuto += 1
        if self._requisicoes_minuto >= 1000:
            espera = 60 - (agora - self._inicio_minuto)
            if espera > 0:
                print(f"⏳ Limite/min atingido. Aguardando {espera:.0f}s...")
                time.sleep(espera)
            self._requisicoes_minuto = 0
            self._inicio_minuto = time.time()

        self.ultima_requisicao = time.time()

    def _requisicao_com_retry(self, func, *args, max_retries=5, **kwargs):
        for tentativa in range(max_retries):
            try:
                self.aguardar_rate_limit()
                return func(*args, **kwargs)
            except BinanceAPIException as e:
                if e.status_code == 429:
                    espera = 2 ** (tentativa + 1)
                    print(f"⚠️ Rate limit 429. Aguardando {espera}s...")
                    time.sleep(espera)
                elif e.status_code == 418:
                    espera = 60 * (tentativa + 1)
                    print(f"🚫 IP banido 418. Aguardando {espera}s...")
                    time.sleep(espera)
                elif hasattr(e, 'code') and e.code == -1003:
                    espera = 2 ** (tentativa + 1)
                    print(f"⚠️ Muitas requisições. Aguardando {espera}s...")
                    time.sleep(espera)
                else:
                    print(f"❌ BinanceAPIException: {e}")
                    return None
            except BinanceRequestException as e:
                print(f"❌ Erro de conexão: {e}")
                time.sleep(2 ** tentativa)
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
                time.sleep(1)
        print("❌ Máximo de tentativas atingido.")
        return None

    # ============================================
    # CÁLCULO DO VALOR POR OPERAÇÃO (PERCENTUAL)
    # ============================================

    def calcular_valor_operacao(self):
        """
        Calcula o valor a investir por operação baseado no saldo atual.
        Usa PERCENTUAL_POR_OPERACAO % do saldo disponível.
        Garante que não passa do saldo livre (saldo - posições abertas).
        """
        # Saldo comprometido em posições abertas
        saldo_em_posicoes = sum(
            dados['valor_investido'] for dados in self.ativos.values()
        )
        saldo_livre = self.saldo - saldo_em_posicoes

        # Percentual do saldo livre
        valor = saldo_livre * PERCENTUAL_POR_OPERACAO

        # Mínimo absoluto para cobrir taxas da Binance ($11 USDT mínimo por ordem)
        MINIMO_BINANCE = 11.0 if not MODO_TESTE else 1.0

        if valor < MINIMO_BINANCE:
            return None, f"Valor calculado (${valor:.2f}) abaixo do mínimo (${MINIMO_BINANCE:.2f})"

        return round(valor, 2), None

    def saldo_acima_minimo(self):
        """Verifica se o saldo ainda está acima do mínimo configurado"""
        minimo = SALDO_INICIAL * SALDO_MINIMO_PCT
        return self.saldo >= minimo

    # ============================================
    # PREÇO
    # ============================================

    def get_preco(self, symbol):
        if MODO_TESTE or not self.client:
            import random
            bases = {"BTCUSDT": 85000, "ETHUSDT": 2000, "BNBUSDT": 600}
            base  = bases.get(symbol, 100)
            preco = base * (1 + random.uniform(-0.02, 0.02))
            print(f"📊 {symbol} [SIM]: ${preco:.2f}")
            return preco

        resultado = self._requisicao_com_retry(
            self.client.get_symbol_ticker, symbol=symbol
        )
        if resultado:
            preco = float(resultado['price'])
            print(f"📊 {symbol}: ${preco:.4f}")
            return preco
        return None

    # ============================================
    # COMPRA
    # ============================================

    def comprar(self, symbol):
        # Verifica saldo mínimo
        if not self.saldo_acima_minimo():
            minimo = SALDO_INICIAL * SALDO_MINIMO_PCT
            print(f"🛑 Saldo (${self.saldo:.2f}) abaixo do mínimo (${minimo:.2f}). Não opera.")
            return False

        # Calcula valor percentual
        valor_operacao, erro = self.calcular_valor_operacao()
        if erro:
            print(f"❌ {erro}")
            return False

        preco = self.get_preco(symbol)
        if not preco:
            return False

        qtd = valor_operacao / preco

        print(f"\n🟢 COMPRA: {symbol}")
        print(f"   Saldo atual: ${self.saldo:.2f}")
        print(f"   Valor ({PERCENTUAL_POR_OPERACAO*100:.0f}%): ${valor_operacao:.2f}")
        print(f"   Preço: ${preco:.4f} | Qtd: {qtd:.6f}")

        if not MODO_TESTE and self.client:
            resultado = self._requisicao_com_retry(
                self.client.order_market_buy,
                symbol=symbol,
                quantity=round(qtd, 6)
            )
            if not resultado:
                print("❌ Ordem de compra não executada.")
                return False
            preco = float(resultado['fills'][0]['price'])
            print(f"✅ ORDEM EXECUTADA @ ${preco:.4f}")

        self.ativos[symbol] = {
            "preco_compra":   preco,
            "qtd":            qtd,
            "topo":           preco,
            "valor_investido": valor_operacao
        }
        self.saldo -= valor_operacao
        print(f"💼 Saldo restante: ${self.saldo:.2f}")
        salvar_saldo(self.saldo)
        return True

    # ============================================
    # VENDA
    # ============================================

    def vender(self, symbol, motivo="TP/SL"):
        if symbol not in self.ativos:
            return False

        preco = self.get_preco(symbol)
        if not preco:
            return False

        dados = self.ativos[symbol]
        valor_recebido  = preco * dados["qtd"]
        valor_investido = dados["valor_investido"]
        lucro           = valor_recebido - valor_investido
        lucro_pct       = (lucro / valor_investido) * 100

        print(f"\n🔴 VENDA ({motivo}): {symbol}")
        print(f"   Comprado @ ${dados['preco_compra']:.4f} → Vendido @ ${preco:.4f}")
        print(f"   Investido: ${valor_investido:.2f} | Recebido: ${valor_recebido:.2f}")
        print(f"   Resultado: ${lucro:+.2f} ({lucro_pct:+.2f}%)")

        if not MODO_TESTE and self.client:
            resultado = self._requisicao_com_retry(
                self.client.order_market_sell,
                symbol=symbol,
                quantity=round(dados["qtd"], 6)
            )
            if not resultado:
                print("❌ Ordem de venda não executada.")
                return False
            print("✅ VENDA EXECUTADA")

        self.saldo += valor_recebido
        salvar_trade(symbol, dados["preco_compra"], preco, dados["qtd"])
        salvar_saldo(self.saldo)
        del self.ativos[symbol]

        print(f"💼 Novo saldo: ${self.saldo:.2f}")
        return True

    # ============================================
    # HELPERS
    # ============================================

    def get_saldo(self):
        return self.saldo

    def get_posicoes(self):
        return self.ativos


print("✅ Trader carregado! (Sistema percentual)")
