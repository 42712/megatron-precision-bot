"""
MÃ³dulo de AnÃ¡lise de Mercado e EstratÃ©gia
"""
import time
from collections import deque
from config import PARES, RSI_PERIOD, EMA_FAST, EMA_SLOW, TAKE_PROFIT, STOP_LOSS, DELAY_ENTRE_PARES
from indicators import analisar_mercado
from database import salvar_indicador


class Analyzer:
    def __init__(self, trader):
        self.trader = trader
        self.historico = {par: deque(maxlen=100) for par in PARES}

    def atualizar_historico(self, symbol, preco):
        """Atualiza histÃ³rico de preÃ§os"""
        if symbol in self.historico:
            self.historico[symbol].append(preco)

    def analisar(self, symbol, preco_atual=None):
        """
        Analisa o mercado para um par.
        Aceita preco_atual como parÃ¢metro para evitar chamadas duplicadas Ã  API.

        Returns:
            dict: {'acao': 'COMPRA'/'VENDA'/'AGUARDAR', 'motivo': str}
        """
        # Usa preÃ§o jÃ¡ obtido ou busca novo (evita requisiÃ§Ã£o dupla)
        if preco_atual is None:
            preco_atual = self.trader.get_preco(symbol)

        if not preco_atual:
            return {'acao': 'AGUARDAR', 'motivo': 'Erro ao obter preÃ§o'}

        # Atualiza histÃ³rico com o preÃ§o atual
        self.atualizar_historico(symbol, preco_atual)

        # Aguarda dados suficientes para os indicadores
        if len(self.historico[symbol]) < max(RSI_PERIOD, EMA_SLOW):
            faltam = max(RSI_PERIOD, EMA_SLOW) - len(self.historico[symbol])
            return {'acao': 'AGUARDAR', 'motivo': f'Coletando dados ({faltam} ciclos restantes)'}

        # AnÃ¡lise tÃ©cnica
        analise = analisar_mercado(list(self.historico[symbol]))

        # Salva indicadores no banco
        salvar_indicador(
            symbol,
            analise['rsi'],
            analise['ema_fast'],
            analise['ema_slow'],
            analise['sinal']
        )

        # Exibe anÃ¡lise
        print(f"\nðŸ“ˆ ANÃLISE {symbol}:")
        print(f"   PreÃ§o: ${preco_atual:.4f}")
        print(f"   RSI: {analise['rsi']}")
        print(f"   EMA{EMA_FAST}: {analise['ema_fast']:.4f}")
        print(f"   EMA{EMA_SLOW}: {analise['ema_slow']:.4f}")
        print(f"   TendÃªncia: {analise['tendencia']}")
        print(f"   Sinal: {analise['sinal']}")

        tem_posicao = symbol in self.trader.get_posicoes()

        # Gerenciamento de risco para posiÃ§Ãµes abertas (prioridade mÃ¡xima)
        if tem_posicao:
            dados = self.trader.get_posicoes()[symbol]
            preco_compra = dados['preco_compra']

            if preco_atual >= preco_compra * TAKE_PROFIT:
                return {'acao': 'VENDA', 'motivo': 'TAKE PROFIT'}

            if preco_atual <= preco_compra * STOP_LOSS:
                return {'acao': 'VENDA', 'motivo': 'STOP LOSS'}

        # Sinais tÃ©cnicos
        if analise['sinal'] == 'COMPRA' and not tem_posicao:
            return {'acao': 'COMPRA', 'motivo': f"RSI={analise['rsi']} | EMA cruzamento ALTA"}

        if analise['sinal'] == 'VENDA' and tem_posicao:
            return {'acao': 'VENDA', 'motivo': f"RSI={analise['rsi']} | EMA cruzamento BAIXA"}

        return {'acao': 'AGUARDAR', 'motivo': 'Sem sinal claro'}

    def monitorar_todos(self):
        """
        Monitora todos os pares configurados.
        ObtÃ©m o preÃ§o UMA VEZ por par e reutiliza na anÃ¡lise (menos requisiÃ§Ãµes).
        """
        resultados = []

        for par in PARES:
            print(f"\n{'='*40}")
            print(f"ðŸ” Analisando {par}...")

            # ObtÃ©m preÃ§o uma Ãºnica vez e passa para analisar()
            preco = self.trader.get_preco(par)

            if preco:
                # Passa o preÃ§o jÃ¡ obtido â€” evita 2Âª chamada desnecessÃ¡ria
                analise = self.analisar(par, preco_atual=preco)
            else:
                analise = {'acao': 'AGUARDAR', 'motivo': 'PreÃ§o indisponÃ­vel'}

            resultados.append((par, analise))

            # Delay entre pares para nÃ£o sobrecarregar a API
            time.sleep(DELAY_ENTRE_PARES)

        return resultados


print("âœ… MÃ³dulo Analyzer carregado com sucesso!")
