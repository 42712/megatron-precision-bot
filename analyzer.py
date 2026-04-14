def monitorar_todos(self):
    resultados = []  # ← sempre inicializado como lista
    
    if self.bot_pausado:
        # ... código ...
        return resultados  # ← retorna lista vazia, não None
    
    for par in PARES:
        # ... código ...
        resultados.append((par, analise))
    
    return resultados  # ← sempre retorna a lista
