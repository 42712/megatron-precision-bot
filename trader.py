"""
Módulo de Execução de Trades
"""
import time
from config import *
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
        
        if not MODO_TESTE:
            self.conectar_binance()
    
    def conectar_binance(self):
        """Conecta à API da Binance"""
        try:
            self.client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
            status = self.client.get_system_status()
            print("✅ Conectado à Binance")
            return True
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            return False
    
    def aguardar_rate_limit(self):
        """Respeita os limites da API"""
        agora = time.time()
        tempo_decorrido = agora - self.ultima_requisicao
        if tempo_decorrido < MIN_INTERVALO:
            time.sleep(MIN_INTERVALO - tempo_decorrido)
        self.ultima_requisicao = time.time()
    
    def get_preco(self, symbol):
        """Obtém preço atual"""
        if MODO_TESTE or not self.client:
            # Simulação
            import random
            preco_base = {
                "BTC/USDT": 50000,
                "ETH/USDT": 3000,
                "BNB/USDT": 400
            }.get(symbol, 100)
            
            variacao = random.uniform(-0.02, 0.02)
            preco = preco_base * (1 + variacao)
            print(f"📊 {symbol} (SIM): R$ {preco:.2f}")
            return preco
        
        # Modo real
        for tentativa in range(3):
            try:
                self.aguardar_rate_limit()
                symbol_formatted = symbol.replace("/", "").upper()
                ticker = self.client.get_symbol_ticker(symbol=symbol_formatted)
                return float(ticker['price'])
            except BinanceAPIException as e:
                if e.code == -1003:
                    print(f"⏳ Rate limit ({tentativa+1}/3)")
                    time.sleep(1)
                else:
                    print(f"⚠️ Erro: {e}")
                    return None
            except Exception as e:
                print(f"⚠️ Erro: {e}")
                time.sleep(0.5)
        return None
    
    def comprar(self, symbol):
        """Executa compra"""
        if self.saldo < VALOR_COMPRA:
            print(f"❌ Saldo insuficiente: R$ {self.saldo:.2f}")
            return False
        
        preco = self.get_preco(symbol)
        if not preco:
            return False
        
        qtd = VALOR_COMPRA / preco
        
        print(f"\n🟢 COMPRA: {symbol} @ R$ {preco:.4f}")
        print(f"   Quantidade: {qtd:.6f} | Valor: R$ {VALOR_COMPRA:.2f}")
        
        # Modo real (descomente para usar)
        if not MODO_TESTE and self.client:
            try:
                self.aguardar_rate_limit()
                order = self.client.order_market_buy(
                    symbol=symbol.replace("/", "").upper(),
                    quantity=round(qtd, 6)
                )
                preco = float(order['fills'][0]['price'])
                print(f"✅ ORDEM REAL EXECUTADA")
            except Exception as e:
                print(f"❌ Erro: {e}")
                return False
        
        self.ativos[symbol] = {
            "preco_compra": preco,
            "qtd": qtd,
            "topo": preco
        }
        
        self.saldo -= VALOR_COMPRA
        print(f"💼 Saldo: R$ {self.saldo:.2f}")
        return True
    
    def vender(self, symbol, motivo="TP/SL"):
        """Executa venda"""
        if symbol not in self.ativos:
            return False
        
        preco = self.get_preco(symbol)
        if not preco:
            return False
        
        dados = self.ativos[symbol]
        valor = preco * dados["qtd"]
        lucro = valor - VALOR_COMPRA
        lucro_percentual = (lucro / VALOR_COMPRA) * 100
        
        print(f"\n🔴 VENDA ({motivo}): {symbol} @ R$ {preco:.4f}")
        print(f"   Lucro: R$ {lucro:.2f} ({lucro_percentual:+.2f}%)")
        
        # Modo real (descomente para usar)
        if not MODO_TESTE and self.client:
            try:
                self.aguardar_rate_limit()
                order = self.client.order_market_sell(
                    symbol=symbol.replace("/", "").upper(),
                    quantity=round(dados["qtd"], 6)
                )
                print(f"✅ VENDA REAL EXECUTADA")
            except Exception as e:
                print(f"❌ Erro: {e}")
                return False
        
        self.saldo += valor
        
        # Salva no banco
        salvar_trade(symbol, dados["preco_compra"], preco, dados["qtd"])
        salvar_saldo(self.saldo)
        
        del self.ativos[symbol]
        return True
    
    def get_saldo(self):
        return self.saldo
    
    def get_posicoes(self):
        return self.ativos

print("✅ Módulo Trader carregado com sucesso!")