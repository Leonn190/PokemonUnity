import random
from collections import deque
import Variaveis as V
import json
import math
from sqlalchemy import Column, Text, Integer

class Mapa(V.db.Model):
    __tablename__ = "mapa"
    id = Column(Integer, primary_key=True)  # <-- ESSENCIAL
    biomas_json = Column(Text, nullable=False)
    objetos_json = Column(Text, nullable=False)
    
def GeraGridBiomas(largura, altura, seed=None):
    if seed is not None:
        random.seed(seed)
    
    total_celulas = largura * altura
    
    # Biomas, índices e proporções
    biomas = {
        0: 0.22,  # campo
        1: 0.40,  # oceano
        2: 0.18,  # floresta
        3: 0.10,  # neve
        4: 0.10   # deserto
    }
    
    # Quantidade de células por bioma (inteiro)
    quantidades = {b: int(p * total_celulas) for b, p in biomas.items()}
    
    # Corrige arredondamento
    soma = sum(quantidades.values())
    diferenca = total_celulas - soma
    if diferenca != 0:
        # Ajusta o bioma de índice 1 (oceano) para compensar
        quantidades[1] += diferenca
    
    # Inicializa grid vazio com -1 (vazio)
    grid = [[-1 for _ in range(largura)] for _ in range(altura)]
    celulas_livres = {(x, y) for x in range(largura) for y in range(altura)}
    
    def vizinhos(x, y):
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < largura and 0 <= ny < altura:
                yield (nx, ny)
    
    def espalhar_bioma(bioma, quantidade):
        # Começa com uma fonte aleatória disponível
        if not celulas_livres:
            return 0
        fonte = random.choice(list(celulas_livres))
        fila = deque([fonte])
        colocados = 0
        
        while fila and colocados < quantidade:
            x, y = fila.popleft()
            if (x, y) not in celulas_livres:
                continue
            grid[y][x] = bioma
            celulas_livres.remove((x, y))
            colocados += 1
            # Adiciona vizinhos livres à fila para expandir
            for viz in vizinhos(x, y):
                if viz in celulas_livres:
                    fila.append(viz)
        return colocados
    
    # Espalha cada bioma com sua quantidade
    for b, qtd in quantidades.items():
        espalhar_bioma(b, qtd)
    
    # Se sobrar células livres (por alguma razão), preenche com bioma 1 (oceano)
    for x, y in list(celulas_livres):
        grid[y][x] = 1
        celulas_livres.remove((x, y))
    
    return grid

def GeraGridObjetos(grid_biomas, prob_objeto=0.01, distancia_minima=5, seed=None):
    if seed is not None:
        random.seed(seed)
    
    altura = len(grid_biomas)
    largura = len(grid_biomas[0]) if altura > 0 else 0
    
    grid_objetos = [[0 for _ in range(largura)] for _ in range(altura)]

    def tem_objeto_proximo(x, y):
        for dy in range(-distancia_minima, distancia_minima + 1):
            for dx in range(-distancia_minima, distancia_minima + 1):
                nx = x + dx
                ny = y + dy
                if 0 <= nx < largura and 0 <= ny < altura:
                    if grid_objetos[ny][nx] != 0:
                        # Usa distância euclidiana real
                        distancia = math.sqrt(dx ** 2 + dy ** 2)
                        if distancia < distancia_minima:
                            return True
        return False

    for y in range(altura):
        for x in range(largura):
            bioma = grid_biomas[y][x]

            # Não gera objeto no oceano (bioma 1)
            if bioma == 1:
                continue

            if random.random() < prob_objeto and not tem_objeto_proximo(x, y):
                grid_objetos[y][x] = random.choice([1, 2, 3])
    
    return grid_objetos

def gerar_e_salvar_mapa(largura, altura, seed=None):
    # Gerar as grids
    grid_biomas = GeraGridBiomas(largura, altura, seed=seed)
    grid_objetos = GeraGridObjetos(grid_biomas, seed=seed)

    # Serializar para JSON
    biomas_json = json.dumps(grid_biomas)
    objetos_json = json.dumps(grid_objetos)

    # Apaga todos os mapas existentes antes de salvar o novo
    V.db.session.query(Mapa).delete()

    # Cria o novo mapa
    novo_mapa = Mapa(biomas_json=biomas_json, objetos_json=objetos_json)
    V.db.session.add(novo_mapa)

    V.db.session.commit()
    