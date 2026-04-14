def bot_loop():
    print("🤖 Bot TURBINADO v2.1 iniciado!")
    contador = 0
    while True:
        try:
            saldo = trader.get_saldo()
            resultado_total = saldo - SALDO_INICIAL
            print(f"\n{'='*50}")
            print(f"🔁 Ciclo #{contador} — {datetime.now().strftime('%H:%M:%S')}")
            print(f"💰 Saldo: ${saldo:.4f} ({resultado_total:+.4f}) | Posições: {len(trader.get_posicoes())}")

            resultados = analyzer.monitorar_todos()
            
            # 🔧 CORREÇÃO: verifica se resultados é válido
            if resultados is None:
                print("⚠️ Nenhum resultado retornado, pulando ciclo...")
                time.sleep(30)
                contador += 1
                continue

            for par, resultado in resultados:
                acao = resultado.get('acao')
                motivo = resultado.get('motivo', '')

                if acao == 'COMPRA':
                    print(f"\n🚀 COMPRANDO {par}!")
                    print(f"   {motivo}")
                    trader.comprar(par)

                elif acao == 'VENDA':
                    print(f"\n📉 VENDENDO {par}!")
                    print(f"   {motivo}")
                    saldo_antes = trader.get_saldo()
                    trader.vender(par, motivo)
                    saldo_depois = trader.get_saldo()
                    lucro = saldo_depois - saldo_antes
                    analyzer.registrar_resultado(lucro)

            contador += 1
            print(f"\n⏳ Próxima análise em 30s...")
            time.sleep(30)

        except Exception as e:
            print(f"❌ Erro no ciclo: {e}")
            import traceback
            traceback.print_exc()  # 🔧 Mostra mais detalhes do erro
            time.sleep(60)
