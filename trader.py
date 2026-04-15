"""
Trader v2.2 — Railway
Binance.com funciona no Railway (servidores fora dos EUA)
Fallback automático para Binance.US se necessário
"""
import time
from config import (
    MODO_TESTE, SALDO_INICIAL, BINANCE_TLD,
    PERCENTUAL_POR_OPERACAO, SALDO_MINIMO_PCT,
    MIN_INTERVALO, BINANCE_API_KEY, BINANCE_SECRET_KEY
)
from database import salvar_trade, salvar_saldo
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException


class Trader:
    def __init__(self):
        self.client  = None
        self.saldo   = SALDO_INICIAL
        self.ativos  = {}
        self.ultima_requisicao   = 0
        self._requisicoes_minuto = 0
        self._inicio_minuto      = time.time()

        if not MODO_TESTE:
            self.conectar_binance()
            print("🔴 MODO REAL ATIVADO - Operações serão executadas na Binance!")
        else:
            print("🔵 Modo SIMULAÇÃO ativo")

    # ============================================
    # CONEXÃO COM FALLBACK AUTOMÁTICO
    # ============================================

    def conectar_binance(self):
        """
        Tenta conectar na ordem: BINANCE_TLD definido → fallback automático.
        Railway usa servidores fora dos EUA, então Binance.com deve funcionar.
        Mas mantemos fallback para .us por segurança.
        """
        tlds = [BINANCE_TLD] if BINANCE_TLD else ["com", "us"]

        for tld in tlds:
            print(f"🔌 Conectando: api.binance.{tld} ...")
            for tentativa in range(3):
                try:
                    self.client = Client(
                        BINANCE_API_KEY,
                        BINANCE_SECRET_KEY,
                        tld=tld
                    )
                    status = self.client.get_system_status()
                    print(f"✅ Binance.{tld.upper()} conectada! Status: {status}")
                    self._sincronizar_saldo_real()
                    return True

                except BinanceAPIException as e:
                    msg = str(e).lower()
                    if "restricted location" in msg or "eligibility" in msg:
                        print(f"🌍 Binance.{tld} bloqueada nesta região → tentando próximo...")
                        break
                    print(f"❌ Tentativa {tentativa+1}/3 [{tld}]: {e}")
                    time.sleep(2 ** tentativa)

                except Exception as e:
                    print(f"❌ Tentativa {tentativa+1}/3 [{tld}]: {e}")
                    time.sleep(2 ** tentativa)

        print("❌ Falha crítica ao conectar à Binance. Verifique suas API Keys.")
        print("   O bot continuará em modo de monitoramento apenas.")
        self.client = None
        return False

    def _sincronizar_saldo_real(self):
        try:
            conta = self.client.get_account()
            for ativo in conta['balances']:
                if ativo['asset'] == 'USDT':
                    self.saldo = float(ativo['free'])
                    print(f"💰 Saldo USDT real: ${self.saldo:.4f}")
                    return
            print("⚠️ Nenhum saldo USDT encontrado.")
        except Exception as e:
            print(f"⚠️ Erro ao sincronizar saldo: {e}")

    # ============================================
    # RATE LIMITING ROBUSTO
    # ============================================

    def aguardar_rate_limit(self):
        agora = time.time()
        if agora - self.ultima_requisicao < MIN_INTERVALO:
            time.sleep(MIN_INTERVALO - (agora - self.ultima_requisicao))

        agora = time.time()
        if agora - self._inicio_minuto >= 60:
            self._requisicoes_minuto = 0
            self._inicio_minuto = agora

        self._requisicoes_minuto += 1
        if self._requisicoes_minuto >= 1000:
            espera = 60 - (agora - self._inicio_minuto)
            if espera > 0:
                print(f"⏳ Limite/min. Aguardando {espera:.0f}s...")
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
                    print(f"⚠️ 429 Rate limit. Aguardando {espera}s...")
                    time.sleep(espera)
                elif e.status_code == 418:
                    espera = 60 * (tentativa + 1)
                    print(f"🚫 418 IP banido. Aguardando {espera}s...")
                    time.sleep(espera)
                elif hasattr(e, 'code') and e.code == -1003:
                    espera = 2 ** (tentativa + 1)
                    print(f"⚠️ -1003 Muitas req. Aguardando {espera}s...")
                    time.sleep(espera)
                else:
                    print(f"❌ BinanceAPIException: {e}")
                    return None
            except BinanceRequestException as e:
                print(f"❌ Conexão: {e}")
                time.sleep(2 ** tentativa)
            except Exception as e:
                print(f"❌ Erro: {e}")
                time.sleep(1)
        print("❌ Máximo de tentativas atingido.")
        return None

    # ============================================
    # CÁLCULO PERCENTUAL
    # ============================================

    def calcular_valor_operacao(self):
        saldo_em_posicoes = sum(d['valor_investido'] for d in self.ativos.values())
        saldo_livre       = self.saldo - saldo_em_posicoes
        valor             = saldo_livre * PERCENTUAL_POR_OPERACAO

        MINIMO = 11.0 if not MODO_TESTE else 1.0
        if valor < MINIMO:
            return None, f"Valor ${valor:.2f} abaixo do mínimo ${MINIMO:.2f}"

        # Nunca arrisca mais de 50% do saldo livre por operação
        if valor > saldo_livre * 0.5:
            valor = saldo_livre * 0.5

        return round(valor, 4), None

    def saldo_acima_minimo(self):
        return self.saldo >= (SALDO_INICIAL * SALDO_MINIMO_PCT)

    # ============================================
    # PREÇO
    # ============================================

    def get_preco(self, symbol):
        if MODO_TESTE or not self.client:
            import random
            bases = {"BTCUSDT": 85000, "ETHUSDT": 2000, "BNBUSDT": 600}
            preco = bases.get(symbol, 100) * (1 + random.uniform(-0.01, 0.01))
            return preco

        r = self._requisicao_com_retry(self.client.get_symbol_ticker, symbol=symbol)
        if r:
            preco = float(r['price'])
            print(f"📊 {symbol}: ${preco:.4f}")
            return preco
        return None

    # ============================================
    # COMPRA
    # ============================================

    def comprar(self, symbol):
        if MODO_TESTE or not self.client:
            return self._comprar_simulado(symbol)

        if not self.saldo_acima_minimo():
            print(f"🛑 Saldo abaixo do mínimo de segurança.")
            return False

        valor_op, erro = self.calcular_valor_operacao()
        if erro:
            print(f"❌ {erro}")
            return False

        preco = self.get_preco(symbol)
        if not preco:
            return False

        qtd = round(valor_op / preco, 6)

        print(f"\n🟢 COMPRA REAL: {symbol}")
        print(f"   Valor ({PERCENTUAL_POR_OPERACAO*100:.0f}%): ${valor_op:.4f}")
        print(f"   Preço: ${preco:.4f} | Qtd: {qtd:.6f}")
        print(f"   ⚠️ EXECUTANDO ORDEM REAL...")

        r = self._requisicao_com_retry(
            self.client.order_market_buy,
            symbol=symbol,
            quantity=qtd
        )
        if not r:
            print("❌ Ordem de compra não executada.")
            return False

        preco_real = float(r['fills'][0]['price'])
        qtd_real   = float(r['executedQty'])
        valor_real = preco_real * qtd_real

        print(f"✅ COMPRA REAL EXECUTADA @ ${preco_real:.4f} | Qtd: {qtd_real:.6f}")

        self.ativos[symbol] = {
            "preco_compra":    preco_real,
            "qtd":             qtd_real,
            "topo":            preco_real,
            "valor_investido": valor_real
        }
        self.saldo -= valor_real
        salvar_saldo(self.saldo)
        print(f"💼 Saldo: ${self.saldo:.4f}")
        return True

    def _comprar_simulado(self, symbol):
        valor_op, erro = self.calcular_valor_operacao()
        if erro:
            print(f"❌ {erro}")
            return False

        preco = self.get_preco(symbol)
        if not preco:
            return False

        qtd = valor_op / preco
        print(f"\n🟢 COMPRA SIMULADA: {symbol} | ${valor_op:.4f} @ ${preco:.4f}")

        self.ativos[symbol] = {
            "preco_compra":    preco,
            "qtd":             qtd,
            "topo":            preco,
            "valor_investido": valor_op
        }
        self.saldo -= valor_op
        salvar_saldo(self.saldo)
        print(f"💼 Saldo: ${self.saldo:.4f}")
        return True

    # ============================================
    # VENDA
    # ============================================

    def vender(self, symbol, motivo="TP/SL"):
        if symbol not in self.ativos:
            return False

        if MODO_TESTE or not self.client:
            return self._vender_simulado(symbol, motivo)

        preco = self.get_preco(symbol)
        if not preco:
            return False

        dados = self.ativos[symbol]
        qtd   = round(dados["qtd"], 6)

        print(f"\n🔴 VENDA REAL ({motivo}): {symbol}")
        print(f"   Qtd: {qtd:.6f} | Preço: ${preco:.4f}")
        print(f"   ⚠️ EXECUTANDO VENDA REAL...")

        r = self._requisicao_com_retry(
            self.client.order_market_sell,
            symbol=symbol,
            quantity=qtd
        )
        if not r:
            print("❌ Ordem de venda não executada.")
            return False

        preco_real      = float(r['fills'][0]['price'])
        valor_recebido  = preco_real * qtd
        lucro           = valor_recebido - dados["valor_investido"]
        lucro_pct       = (lucro / dados["valor_investido"]) * 100

        print(f"✅ VENDA REAL EXECUTADA @ ${preco_real:.4f}")
        print(f"   Resultado: ${lucro:+.4f} ({lucro_pct:+.2f}%)")

        self.saldo += valor_recebido
        salvar_trade(symbol, dados["preco_compra"], preco_real, qtd, motivo)
        salvar_saldo(self.saldo)
        del self.ativos[symbol]
        print(f"💼 Novo saldo: ${self.saldo:.4f}")
        return True

    def _vender_simulado(self, symbol, motivo):
        dados = self.ativos[symbol]
        preco = self.get_preco(symbol)
        if not preco:
            return False

        valor_recebido = preco * dados["qtd"]
        lucro          = valor_recebido - dados["valor_investido"]
        lucro_pct      = (lucro / dados["valor_investido"]) * 100

        print(f"\n🔴 VENDA SIMULADA ({motivo}): {symbol}")
        print(f"   ${dados['preco_compra']:.4f} → ${preco:.4f} | {lucro:+.4f} ({lucro_pct:+.2f}%)")

        self.saldo += valor_recebido
        salvar_trade(symbol, dados["preco_compra"], preco, dados["qtd"], motivo)
        salvar_saldo(self.saldo)
        del self.ativos[symbol]
        print(f"💼 Novo saldo: ${self.saldo:.4f}")
        return True

    def get_saldo(self):
        return self.saldo

    def get_posicoes(self):
        return self.ativos


print("✅ Trader carregado!")
