import random
from collections import deque
import Variaveis as V
import json
from sqlalchemy import Column, Text, Integer

class Mapa(V.db.Model):
    __tablename__ = "mapa"
    id = Column(Integer, primary_key=True)  # <-- ESSENCIAL
    biomas_json = Column(Text, nullable=False)
    objetos_json = Column(Text, nullable=False)
    
def GeradorGridBiomasAvancado(largura, altura, seed=None):
    if seed is not None:
        random.seed(seed)

    total_celulas = largura * altura

    biomas_percentuais = [
        ("oceano", 0.25),
        ("praia", 0.05),
        ("campo", 0.16),
        ("floresta", 0.145),
        ("deserto", 0.095),
        ("neve", 0.085),
        ("rochoso", 0.065),
        ("pantano", 0.06),
        ("terra morta", 0.045),
        ("terreno encantado", 0.045),
    ]

    # Calcular a quantidade de células por bioma
    biomas_com_contagem = []
    soma = 0
    for nome, p in biomas_percentuais:
        quantidade = int(p * total_celulas)
        biomas_com_contagem.append([nome, quantidade])
        soma += quantidade

    # Corrigir diferença de arredondamento
    diferenca = total_celulas - soma
    if diferenca != 0:
        biomas_com_contagem[0][1] += diferenca

    grid = [[None for _ in range(largura)] for _ in range(altura)]
    celulas_livres = {(x, y) for x in range(largura) for y in range(altura)}

    def vizinhos(x, y):
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < largura and 0 <= ny < altura:
                yield (nx, ny)

    mapa_biomas = {nome: qtd for nome, qtd in biomas_com_contagem}

    def espalha_bioma(nome_bioma, quantidade, fontes=None, condicao_vizinho=None, forcar=False):
        colocados = 0
        if not fontes:
            fontes = [random.choice(list(celulas_livres))]
        fila = deque(fontes)

        while fila and colocados < quantidade:
            x, y = fila.popleft()
            if (x, y) not in celulas_livres:
                continue

            if condicao_vizinho and not any(grid[vy][vx] == condicao_vizinho for vx, vy in vizinhos(x, y)):
                if not forcar:
                    continue

            grid[y][x] = nome_bioma
            celulas_livres.remove((x, y))
            colocados += 1

            for viz in vizinhos(x, y):
                if viz in celulas_livres:
                    fila.append(viz)

        return colocados

    # 1. Oceano
    centro_oceano = random.choice(list(celulas_livres))
    colocados = espalha_bioma("oceano", mapa_biomas["oceano"], fontes=[centro_oceano])
    mapa_biomas["oceano"] -= colocados

    # 2. Praia (sempre ao lado do oceano)
    candidatos_praia = [(x, y) for x, y in celulas_livres if any(grid[vy][vx] == "oceano" for vx, vy in vizinhos(x, y))]
    random.shuffle(candidatos_praia)
    colocados = espalha_bioma("praia", mapa_biomas["praia"], fontes=candidatos_praia, condicao_vizinho="oceano", forcar=True)
    mapa_biomas["praia"] -= colocados

    # 3. Demais biomas
    for nome in [b[0] for b in biomas_com_contagem if b[0] not in ("oceano", "praia")]:
        if mapa_biomas[nome] > 0:
            espalha_bioma(nome, mapa_biomas[nome])

    # 4. Preencher qualquer célula restante com o bioma mais comum (ajuste final)
    mais_comum = max(biomas_com_contagem, key=lambda b: b[1])[0]
    for x, y in list(celulas_livres):
        grid[y][x] = mais_comum

    return grid

def GeradorGridObjetos(grid_biomas, seed=None):
    if seed is not None:
        random.seed(seed)

    altura = len(grid_biomas)
    largura = len(grid_biomas[0]) if altura > 0 else 0

    grid_objetos = [[None for _ in range(largura)] for _ in range(altura)]

    for y in range(altura):
        for x in range(largura):
            bioma = grid_biomas[y][x]

            # Não cria nada em água/oceano
            if bioma == "oceano" or bioma == "agua":
                grid_objetos[y][x] = None
                continue

            # Chance base para criar árvore ou pedra
            # Você pode ajustar essas probabilidades para cada bioma se quiser
            chance_arvore = 0.15
            chance_pedra = 0.10

            r = random.random()
            if r < chance_arvore:
                grid_objetos[y][x] = "arvore"
            elif r < chance_arvore + chance_pedra:
                grid_objetos[y][x] = "pedra"
            else:
                grid_objetos[y][x] = None

    return grid_objetos

def gerar_e_salvar_mapa(largura, altura, seed=None):
    # Gerar as grids
    grid_biomas = GeradorGridBiomasAvancado(largura, altura, seed=seed)
    grid_objetos = GeradorGridObjetos(grid_biomas, seed=seed)

    # Serializar para JSON
    biomas_json = json.dumps(grid_biomas)
    objetos_json = json.dumps(grid_objetos)

    # Verifica se já existe o único mapa (por simplicidade)
    mapa_existente = Mapa.query.first()
    if mapa_existente:
        mapa_existente.biomas_json = biomas_json
        mapa_existente.objetos_json = objetos_json
    else:
        novo_mapa = Mapa(biomas_json=biomas_json, objetos_json=objetos_json)
        V.db.session.add(novo_mapa)

    V.db.session.commit()
    