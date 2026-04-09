"""
Módulo de Execução de Trades — com rate limiting robusto
"""
import time
from config import (
    MODO_TESTE, SALDO_INICIAL, VALOR_COMPRA,
    MIN_INTERVALO, BINANCE_API_KEY, BINANCE_SECRET_KEY
)
from database import salvar_trade, salvar_saldo
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException


# ============================================
# CONEXÃO COM A BINANCE
# ============================================
class Trader:
    def __init__(self):
        self.client = None
        self.saldo = SALDO_INICIAL
        self.ativos = {}
        self.ultima_requisicao = 0
        self._requisicoes_no_minuto = 0
        self._inicio_minuto = time.time()

        if not MODO_TESTE:
            self.conectar_binance()

    def conectar_binance(self):
        """Conecta à API da Binance com retry"""
        for tentativa in range(3):
            try:
                self.client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
                status = self.client.get_system_status()
                print(f"✅ Conectado à Binance | Status: {status}")
                return True
            except Exception as e:
                print(f"❌ Tentativa {tentativa+1}/3 falhou: {e}")
                time.sleep(2 ** tentativa)
        print("❌ Não foi possível conectar à Binance.")
        return False

    def aguardar_rate_limit(self):
        """
        Controle de rate limit em duas camadas:
        1. Intervalo mínimo entre requisições (MIN_INTERVALO)
        2. Contador de requisições por minuto (máx 1000 para segurança)
        """
        # Camada 1: tempo mínimo entre requisições
        agora = time.time()
        decorrido = agora - self.ultima_requisicao
        if decorrido < MIN_INTERVALO:
            time.sleep(MIN_INTERVALO - decorrido)

        # Camada 2: limite por minuto
        agora = time.time()
        if agora - self._inicio_minuto >= 60:
            self._requisicoes_no_minuto = 0
            self._inicio_minuto = agora

        self._requisicoes_no_minuto += 1
        if self._requisicoes_no_minuto >= 1000:
            espera = 60 - (agora - self._inicio_minuto)
            if espera > 0:
                print(f"⏳ Limite por minuto atingido. Aguardando {espera:.0f}s...")
                time.sleep(espera)
            self._requisicoes_no_minuto = 0
            self._inicio_minuto = time.time()

        self.ultima_requisicao = time.time()

    def _requisicao_com_retry(self, func, *args, max_retries=5, **kwargs):
        """
        Executa uma requisição com backoff exponencial em caso de erro.
        Trata especialmente os erros 429 (rate limit) e 418 (IP banido).
        """
        for tentativa in range(max_retries):
            try:
                self.aguardar_rate_limit()
                return func(*args, **kwargs)

            except BinanceAPIException as e:
                # 429: Too Many Requests
                if e.status_code == 429:
                    espera = 2 ** (tentativa + 1)  # 2, 4, 8, 16, 32 segundos
                    print(f"⚠️  Rate limit 429! Aguardando {espera}s... (tentativa {tentativa+1}/{max_retries})")
                    time.sleep(espera)

                # 418: IP banido temporariamente — espera mais longa
                elif e.status_code == 418:
                    espera = 60 * (tentativa + 1)  # 60, 120, 180... segundos
                    print(f"🚫 IP banido (418)! Aguardando {espera}s... (tentativa {tentativa+1}/{max_retries})")
                    time.sleep(espera)

                # -1003: Muitas requisições (erro interno Binance)
                elif hasattr(e, 'code') and e.code == -1003:
                    espera = 2 ** (tentativa + 1)
                    print(f"⚠️  Muitas requisições (-1003). Aguardando {espera}s...")
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

        print(f"❌ Máximo de tentativas atingido para a requisição.")
        return None

    # ============================================
    # OPERAÇÕES DE MERCADO
    # ============================================

    def get_preco(self, symbol):
        """Obtém preço atual com retry automático"""
        if MODO_TESTE or not self.client:
            import random
            precos_base = {
                "BTCUSDT": 85000,
                "ETHUSDT": 2000,
                "BNBUSDT": 600,
            }
            base = precos_base.get(symbol, 100)
            preco = base * (1 + random.uniform(-0.02, 0.02))
            print(f"📊 {symbol} [SIM]: ${preco:.2f}")
            return preco

        resultado = self._requisicao_com_retry(
            self.client.get_symbol_ticker,
            symbol=symbol
        )
        if resultado:
            preco = float(resultado['price'])
            print(f"📊 {symbol}: ${preco:.4f}")
            return preco
        return None

    def comprar(self, symbol):
        """Executa compra com tratamento de erros"""
        if self.saldo < VALOR_COMPRA:
            print(f"❌ Saldo insuficiente: ${self.saldo:.2f}")
            return False

        preco = self.get_preco(symbol)
        if not preco:
            return False

        qtd = VALOR_COMPRA / preco

        print(f"\n🟢 COMPRA: {symbol} @ ${preco:.4f}")
        print(f"   Quantidade: {qtd:.6f} | Valor: ${VALOR_COMPRA:.2f}")

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
            print(f"✅ ORDEM REAL EXECUTADA @ ${preco:.4f}")

        self.ativos[symbol] = {
            "preco_compra": preco,
            "qtd": qtd,
            "topo": preco
        }
        self.saldo -= VALOR_COMPRA
        print(f"💼 Saldo restante: ${self.saldo:.2f}")
        return True

    def vender(self, symbol, motivo="TP/SL"):
        """Executa venda com tratamento de erros"""
        if symbol not in self.ativos:
            return False

        preco = self.get_preco(symbol)
        if not preco:
            return False

        dados = self.ativos[symbol]
        valor = preco * dados["qtd"]
        lucro = valor - VALOR_COMPRA
        lucro_pct = (lucro / VALOR_COMPRA) * 100

        print(f"\n🔴 VENDA ({motivo}): {symbol} @ ${preco:.4f}")
        print(f"   Lucro: ${lucro:.2f} ({lucro_pct:+.2f}%)")

        if not MODO_TESTE and self.client:
            resultado = self._requisicao_com_retry(
                self.client.order_market_sell,
                symbol=symbol,
                quantity=round(dados["qtd"], 6)
            )
            if not resultado:
                print("❌ Ordem de venda não executada.")
                return False
            print(f"✅ VENDA REAL EXECUTADA")

        self.saldo += valor
        salvar_trade(symbol, dados["preco_compra"], preco, dados["qtd"])
        salvar_saldo(self.saldo)
        del self.ativos[symbol]
        return True

    def get_saldo(self):
        return self.saldo

    def get_posicoes(self):
        return self.ativos


print("✅ Módulo Trader carregado com sucesso!")
