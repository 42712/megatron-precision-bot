"""
Módulo de Execução de Trades — MODO REAL
Operações reais na Binance
"""
import time
from config import (
    MODO_TESTE, SALDO_INICIAL,
    PERCENTUAL_POR_OPERACAO, SALDO_MINIMO_PCT,
    MIN_INTERVALO, BINANCE_API_KEY, BINANCE_SECRET_KEY
)
from database import salvar_trade, salvar_saldo

# Importa a Binance apenas se for modo real
if not MODO_TESTE:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceRequestException


class Trader:
    def __init__(self):
        self.client = None
        self.saldo = SALDO_INICIAL
        self.ativos = {}
        self.ultima_requisicao = 0

        if not MODO_TESTE:
            self.conectar_binance()
            print("🔴 MODO REAL ATIVADO - Operações serão executadas na Binance!")
        else:
            print("🔵 Modo SIMULAÇÃO ativo")

    def conectar_binance(self):
        """Conecta à Binance em modo REAL"""
        for tentativa in range(3):
            try:
                self.client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
                # Testa a conexão
                status = self.client.get_system_status()
                print(f"✅ Binance conectada com sucesso! Status: {status}")
                # Sincroniza saldo real
                self._sincronizar_saldo_real()
                return True
            except Exception as e:
                print(f"❌ Tentativa {tentativa+1}/3 falhou: {e}")
                time.sleep(2 ** tentativa)
        
        print("❌ Falha crítica ao conectar à Binance. Verifique suas API Keys.")
        print("   O bot continuará em modo de monitoramento apenas.")
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

    def aguardar_rate_limit(self):
        """Respeita limite de requisições da Binance"""
        agora = time.time()
        decorrido = agora - self.ultima_requisicao
        if decorrido < MIN_INTERVALO:
            time.sleep(MIN_INTERVALO - decorrido)
        self.ultima_requisicao = time.time()

    def calcular_valor_operacao(self):
        """Calcula valor baseado no saldo atual (percentual)"""
        saldo_em_posicoes = sum(dados['valor_investido'] for dados in self.ativos.values())
        saldo_livre = self.saldo - saldo_em_posicoes
        valor = saldo_livre * PERCENTUAL_POR_OPERACAO
        
        # Mínimo da Binance para ordem
        MINIMO_BINANCE = 11.0
        
        if valor < MINIMO_BINANCE:
            return None, f"Valor ${valor:.2f} abaixo do mínimo (${MINIMO_BINANCE:.2f})"
        
        # Limite máximo de segurança (não arriscar mais que 50% do saldo livre)
        if valor > saldo_livre * 0.5:
            valor = saldo_livre * 0.5
            
        return round(valor, 2), None

    def saldo_acima_minimo(self):
        """Verifica se saldo está acima do mínimo de segurança"""
        minimo = SALDO_INICIAL * SALDO_MINIMO_PCT
        return self.saldo >= minimo

    def get_preco(self, symbol):
        """Obtém preço atual do símbolo"""
        if MODO_TESTE or not self.client:
            # Simulação
            import random
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
        """Executa ordem de COMPRA real na Binance"""
        if MODO_TESTE or not self.client:
            return self._comprar_simulado(symbol)
        
        # Verifica saldo mínimo
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
        
        # Ajusta quantidade para 6 casas decimais (padrão Binance)
        qtd = round(qtd, 6)

        print(f"\n🟢 COMPRA REAL: {symbol}")
        print(f"   Valor ({PERCENTUAL_POR_OPERACAO*100:.0f}%): ${valor_operacao:.2f}")
        print(f"   Preço: ${preco:.4f} | Qtd: {qtd:.6f}")
        print(f"   ⚠️ CONFIRMANDO ORDEM REAL...")

        try:
            self.aguardar_rate_limit()
            resultado = self.client.order_market_buy(
                symbol=symbol,
                quantity=qtd
            )
            
            # Extrai preço real da execução
            preco_real = float(resultado['fills'][0]['price'])
            qtd_real = float(resultado['executedQty'])
            valor_real = preco_real * qtd_real
            
            print(f"✅ COMPRA REAL EXECUTADA!")
            print(f"   Preço: ${preco_real:.4f} | Quantidade: {qtd_real:.6f}")
            print(f"   Valor gasto: ${valor_real:.2f}")
            
            self.ativos[symbol] = {
                "preco_compra": preco_real,
                "qtd": qtd_real,
                "topo": preco_real,
                "valor_investido": valor_real
            }
            self.saldo -= valor_real
            salvar_saldo(self.saldo)
            return True
            
        except Exception as e:
            print(f"❌ ERRO NA COMPRA REAL: {e}")
            return False

    def _comprar_simulado(self, symbol):
        """Compra simulada para testes"""
        valor_operacao, erro = self.calcular_valor_operacao()
        if erro:
            print(f"❌ {erro}")
            return False

        preco = self.get_preco(symbol)
        if not preco:
            return False

        qtd = valor_operacao / preco

        print(f"\n🟢 COMPRA SIMULADA: {symbol}")
        print(f"   Valor: ${valor_operacao:.2f} | Preço: ${preco:.4f}")

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
        """Executa ordem de VENDA real na Binance"""
        if symbol not in self.ativos:
            return False

        if MODO_TESTE or not self.client:
            return self._vender_simulado(symbol, motivo)

        preco = self.get_preco(symbol)
        if not preco:
            return False

        dados = self.ativos[symbol]
        qtd = round(dados["qtd"], 6)

        print(f"\n🔴 VENDA REAL ({motivo}): {symbol}")
        print(f"   Quantidade: {qtd:.6f} | Preço atual: ${preco:.4f}")
        print(f"   ⚠️ EXECUTANDO VENDA REAL...")

        try:
            self.aguardar_rate_limit()
            resultado = self.client.order_market_sell(
                symbol=symbol,
                quantity=qtd
            )
            
            preco_real = float(resultado['fills'][0]['price'])
            valor_recebido = preco_real * qtd
            valor_investido = dados["valor_investido"]
            lucro = valor_recebido - valor_investido
            lucro_pct = (lucro / valor_investido) * 100

            print(f"✅ VENDA REAL EXECUTADA!")
            print(f"   Vendido @ ${preco_real:.4f}")
            print(f"   Resultado: ${lucro:+.2f} ({lucro_pct:+.2f}%)")

            self.saldo += valor_recebido
            salvar_trade(symbol, dados["preco_compra"], preco_real, qtd, motivo)
            salvar_saldo(self.saldo)
            del self.ativos[symbol]

            print(f"💼 Novo saldo: ${self.saldo:.2f}")
            return True
            
        except Exception as e:
            print(f"❌ ERRO NA VENDA REAL: {e}")
            return False

    def _vender_simulado(self, symbol, motivo):
        """Venda simulada para testes"""
        dados = self.ativos[symbol]
        preco = self.get_preco(symbol)
        
        if not preco:
            return False

        valor_recebido = preco * dados["qtd"]
        valor_investido = dados["valor_investido"]
        lucro = valor_recebido - valor_investido
        lucro_pct = (lucro / valor_investido) * 100

        print(f"\n🔴 VENDA SIMULADA ({motivo}): {symbol}")
        print(f"   Comprado @ ${dados['preco_compra']:.4f} → Vendido @ ${preco:.4f}")
        print(f"   Resultado: ${lucro:+.2f} ({lucro_pct:+.2f}%)")

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


print("✅ Trader carregado - MODO REAL!")
