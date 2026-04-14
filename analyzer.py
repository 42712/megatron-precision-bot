"""
Analyzer TURBINADO v2.1 — Sistema Percentual
"""
import time
from collections import deque
from config import (
    PARES, EMA_FAST, EMA_SLOW, EMA_TREND,
    TAKE_PROFIT, STOP_LOSS, TRAILING_STOP,
    TAKE_PROFIT_PCT, STOP_LOSS_PCT, TRAILING_STOP_PCT,
    MAX_POSICOES, MAX_PERDA_DIARIA_PCT, COOLDOWN_APOS_STOP,
    MIN_CONFLUENCIA, DELAY_ENTRE_PARES, SALDO_INICIAL
)
from indicators import calcular_confluencia
from database import salvar_indicador


class Analyzer:
    def __init__(self, trader):
        self.trader = trader
        self.historico_precos = {par: deque(maxlen=200) for par in PARES}
        self.historico_volumes = {par: deque(maxlen=200) for par in PARES}
        self.cooldown = {par: 0 for par in PARES}
        self.perda_diaria = 0.0
        self.bot_pausado = False

    def registrar_resultado(self, lucro):
        if lucro < 0:
            self.perda_diaria += abs(lucro)
            limite = SALDO_INICIAL * MAX_PERDA_DIARIA_PCT
            pct = (self.perda_diaria / limite) * 100
            print(f"   📊 Perda diária: ${self.perda_diaria:.2f} / ${limite:.2f} ({pct:.0f}%)")
            if self.perda_diaria >= limite:
                self.bot_pausado = True
                print(f"\n🛑 LIMITE DE PERDA DIÁRIA ATINGIDO! Bot pausado.")

    def aplicar_cooldown(self, symbol):
        self.cooldown[symbol] = COOLDOWN_APOS_STOP
        print(f"⏸️ {symbol} bloqueado por {COOLDOWN_APOS_STOP} ciclos")

    def atualizar_historico(self, symbol, preco, volume=None):
        if symbol in self.historico_precos:
            self.historico_precos[symbol].append(preco)
        if volume and symbol in self.historico_volumes:
            self.historico_volumes[symbol].append(volume)

    def analisar(self, symbol, preco_atual=None):
        if preco_atual is None:
            preco_atual = self.trader.get_preco(symbol)
        if not preco_atual:
            return {'acao': 'AGUARDAR', 'motivo': 'Preço indisponível'}

        self.atualizar_historico(symbol, preco_atual)
        precos = list(self.historico_precos[symbol])
        volumes = list(self.historico_volumes[symbol])
        analise = calcular_confluencia(precos, volumes if volumes else None)

        if analise.get('faltam_dados', 0) > 0:
            return {'acao': 'AGUARDAR', 'motivo': f"Coletando dados ({analise['faltam_dados']} ciclos)", 'analise': analise}

        self._log_analise(symbol, preco_atual, analise)
        salvar_indicador(symbol, analise['rsi'], analise['ema_fast'], analise['ema_slow'], analise['sinal'])

        tem_posicao = symbol in self.trader.get_posicoes()

        if tem_posicao:
            dados = self.trader.get_posicoes()[symbol]
            preco_compra = dados['preco_compra']
            topo = dados.get('topo', preco_compra)

            if preco_atual > topo:
                dados['topo'] = preco_atual
                topo = preco_atual

            variacao = ((preco_atual / preco_compra) - 1) * 100
            print(f"   📍 Posição: entrada ${preco_compra:.4f} → atual ${preco_atual:.4f} ({variacao:+.2f}%)")

            if preco_atual >= preco_compra * TAKE_PROFIT:
                return {'acao': 'VENDA', 'motivo': f'✅ TAKE PROFIT +{TAKE_PROFIT_PCT*100:.1f}%', 'analise': analise}

            if preco_atual <= topo * (1 - TRAILING_STOP):
                queda = ((topo - preco_atual) / topo) * 100
                return {'acao': 'VENDA', 'motivo': f'📉 TRAILING STOP (caiu {queda:.1f}% do topo)', 'analise': analise}

            if preco_atual <= preco_compra * STOP_LOSS:
                self.aplicar_cooldown(symbol)
                return {'acao': 'VENDA', 'motivo': f'🛑 STOP LOSS -{STOP_LOSS_PCT*100:.1f}%', 'analise': analise}

            if analise['sinal'] == 'VENDA' and analise['pontos_venda'] >= MIN_CONFLUENCIA:
                return {'acao': 'VENDA', 'motivo': f"📊 Confluência VENDA ({analise['pontos_venda']}/5)", 'analise': analise}

        if not tem_posicao:
            if len(self.trader.get_posicoes()) >= MAX_POSICOES:
                return {'acao': 'AGUARDAR', 'motivo': f'Máx posições ({MAX_POSICOES})', 'analise': analise}

            if not self.trader.saldo_acima_minimo():
                return {'acao': 'AGUARDAR', 'motivo': 'Saldo abaixo do mínimo', 'analise': analise}

            if analise['sinal'] == 'COMPRA' and analise['pontos_compra'] >= MIN_CONFLUENCIA:
                return {
                    'acao': 'COMPRA',
                    'motivo': f"🚀 Confluência ({analise['pontos_compra']}/5): " + " | ".join(analise['detalhes_compra']),
                    'analise': analise
                }

        return {
            'acao': 'AGUARDAR',
            'motivo': f"Aguardando confluência (C:{analise['pontos_compra']}/V:{analise['pontos_venda']} | mín:{MIN_CONFLUENCIA})",
            'analise': analise
        }

    def _log_analise(self, symbol, preco, a):
        print(f"\n📊 {symbol} @ ${preco:.4f} | Tendência: {a['tendencia_maior']}")
        print(f"   RSI: {a['rsi']} | MACD hist: {a['macd_hist']:.6f}")
        print(f"   🎯 C:{a['pontos_compra']}/5 | V:{a['pontos_venda']}/5 | Sinal: {a['sinal']}")

    def monitorar_todos(self):
        resultados = []

        if self.bot_pausado:
            limite = SALDO_INICIAL * MAX_PERDA_DIARIA_PCT
            print(f"\n🛑 Bot PAUSADO — perda diária: ${self.perda_diaria:.2f} / ${limite:.2f}")
            for par in PARES:
                resultados.append((par, {'acao': 'AGUARDAR', 'motivo': 'Bot pausado'}))
            return resultados

        for par in PARES:
            print(f"\n{'='*45}")
            if self.cooldown[par] > 0:
                self.cooldown[par] -= 1
                print(f"⏸️ {par} cooldown ({self.cooldown[par]} restantes)")
                resultados.append((par, {'acao': 'AGUARDAR', 'motivo': 'Cooldown'}))
                time.sleep(0.5)
                continue

            print
