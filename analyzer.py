"""
Módulo de Análise de Mercado e Estratégia
"""
import time
from collections import deque
from config import PARES, RSI_PERIOD, EMA_FAST, EMA_SLOW
from indicators import analisar_mercado
from database import salvar_indicador

class Analyzer:
    def __init__(self, trader):
        self.trader = trader
        self.historico = {par: deque(maxlen=100) for par in PARES}
        self.ultima_analise = 0
    
    def atualizar_historico(self, symbol, preco):
        """Atualiza histórico de preços"""
        if symbol in self.historico:
            self.historico[symbol].append(preco)
    
    def analisar(self, symbol):
        """
        Analisa o mercado e retorna se deve comprar/vender
        
        Returns:
            dict: {'acao': 'COMPRA'/'VENDA'/'AGUARDAR', 'motivo': str}
        """
        if len(self.historico[symbol]) < max(RSI_PERIOD, EMA_SLOW):
            return {'acao': 'AGUARDAR', 'motivo': 'Dados insuficientes'}
        
        # Obtém preço atual
        preco_atual = self.trader.get_preco(symbol)
        if not preco_atual:
            return {'acao': 'AGUARDAR', 'motivo': 'Erro ao obter preço'}
        
        # Atualiza histórico
        self.atualizar_historico(symbol, preco_atual)
        
        # Análise técnica
        analise = analisar_mercado(list(self.historico[symbol]))
        
        # Salva indicadores no banco
        salvar_indicador(symbol, analise['rsi'], analise['ema_fast'], 
                        analise['ema_slow'], analise['sinal'])
        
        # Exibe análise
        print(f"\n📈 ANÁLISE {symbol}:")
        print(f"   RSI: {analise['rsi']}")
        print(f"   EMA{EMA_FAST}: {analise['ema_fast']:.2f}")
        print(f"   EMA{EMA_SLOW}: {analise['ema_slow']:.2f}")
        print(f"   Tendência: {analise['tendencia']}")
        print(f"   Sinal: {analise['sinal']}")
        
        # Verifica se já tem posição aberta
        tem_posicao = symbol in self.trader.get_posicoes()
        
        # Decisões baseadas na análise
        if analise['sinal'] == 'COMPRA' and not tem_posicao:
            return {'acao': 'COMPRA', 'motivo': f"RSI={analise['rsi']}"}
        
        if analise['sinal'] == 'VENDA' and tem_posicao:
            return {'acao': 'VENDA', 'motivo': f"RSI={analise['rsi']}"}
        
        # Gerenciamento de risco para posições abertas
        if tem_posicao:
            dados = self.trader.get_posicoes()[symbol]
            preco_compra = dados['preco_compra']
            
            # Take Profit e Stop Loss
            if preco_atual >= preco_compra * TAKE_PROFIT:
                return {'acao': 'VENDA', 'motivo': 'TAKE PROFIT'}
            
            if preco_atual <= preco_compra * STOP_LOSS:
                return {'acao': 'VENDA', 'motivo': 'STOP LOSS'}
        
        return {'acao': 'AGUARDAR', 'motivo': 'Sem sinal claro'}
    
    def monitorar_todos(self):
        """Monitora todos os pares configurados"""
        resultados = []
        
        for par in PARES:
            print(f"\n{'='*40}")
            print(f"Analisando {par}...")
            
            # Atualiza preço
            preco = self.trader.get_preco(par)
            if preco:
                self.atualizar_historico(par, preco)
            
            # Analisa
            analise = self.analisar(par)
            resultados.append((par, analise))
            
            time.sleep(1)  # Delay entre análises
        
        return resultados

print("✅ Módulo Analyzer carregado com sucesso!")