import random
import math
import pandas as pd

df = pd.read_csv("Pokemons.csv")
 
CAMPOS_POKEMON = [
    "Nome",
    "Vida", "Atk", "Def", "SpA", "SpD", "Vel",
    "Mag", "Per", "Ene", "EnR", "CrD", "CrC",
    "Sinergia", "Habilidades", "Equipaveis", "Total",
    "Poder R1", "Poder R2", "Poder R3",
    "Tipo1", "%1", "Tipo2", "%2", "Tipo3", "%3",
    "Altura", "Peso", "Raridade", "Estagio", "FF", "Code",
    "Nivel",
    "IV",
    "IV_Vida", "IV_Atk", "IV_Def", "IV_SpA", "IV_SpD", "IV_Vel",
    "IV_Mag", "IV_Per", "IV_Ene", "IV_EnR", "IV_CrD", "IV_CrC", "ID"
]

def CompactarPokemon(info):
    valores = []
    for campo in CAMPOS_POKEMON:
        valor = info.get(campo, "")
        # Converter para string e substituir vírgulas internas se houver
        valor_str = str(valor).replace(",", ";")  # para não quebrar o csv
        valores.append(valor_str)
    return ",".join(valores)

def GerarPokemon(players_ativos, pokemons_ativos):
    """
    Para cada player ativo:
      - escolhe um Pokémon aleatório válido
      - respeita raridade
      - tenta posicionar no anel [18, 36] do player dono
      - não pode ficar a < 18 de qualquer player
      - não pode ficar a < 4 de qualquer Pokémon ativo
      - limite de 40 pokémons no anel de cada player
    Não retorna nada; adiciona itens em pokemons_ativos.
    """
    RAIO_VISAO = 18
    MIN_DIST_POKES = 4
    MAX_TENTATIVAS_POS = 20
    LIMITE_POKES_ANEL = 40

    locs_players = [(data["Loc"][0], data["Loc"][1]) for _, data in players_ativos.items()]

    for _, pdata in players_ativos.items():
        owner_loc = pdata["Loc"]
        ox0, oy0 = owner_loc

        # --- contar pokémons já no anel do player ---
        count_anel = 0
        for p in pokemons_ativos:
            dist = math.dist(owner_loc, p["loc"])
            if RAIO_VISAO <= dist <= RAIO_VISAO * 2:
                count_anel += 1
        if count_anel >= LIMITE_POKES_ANEL:
            continue  # não gera mais para este player

        # --- sorteia Pokémon válido pela Dex / raridade ---
        code = random.randint(1, 1100)
        pokemon = df[df["Code"] == code]
        if pokemon.empty:
            continue

        info = pokemon.iloc[0].to_dict()
        if info.get('Raridade', "-") == "-":
            continue

        try:
            rar = int(info['Raridade'])
        except:
            continue
        if random.randint(1, 11) <= rar:
            continue

        # --- tentar posicionamento no anel ---
        colocado = False
        for _ in range(MAX_TENTATIVAS_POS):
            ang = random.uniform(0, 2 * math.pi)
            dist = random.uniform(RAIO_VISAO, RAIO_VISAO * 2)  # [18, 36]
            X = int(ox0 + math.cos(ang) * dist)
            Y = int(oy0 + math.sin(ang) * dist)

            perto_de_player = any(math.dist((X, Y), lp) < RAIO_VISAO for lp in locs_players)
            if perto_de_player:
                continue

            perto_de_poke = any(math.dist((X, Y), (p["loc"][0], p["loc"][1])) < MIN_DIST_POKES for p in pokemons_ativos)
            if perto_de_poke:
                continue

            colocado = True
            break

        if not colocado:
            continue

        # --- gerar atributos, IVs e extras ---
        info_serializavel = info.copy()
        info_serializavel["Nivel"] = int(random.betavariate(2, 5) * 50)

        info_serializavel["%1"] = max(0, info_serializavel["%1"] - int(random.betavariate(2, 4) * 70))
        info_serializavel["%2"] = max(0, info_serializavel["%2"] - int(random.betavariate(2, 4) * 70))
        info_serializavel["%3"] = max(0, info_serializavel["%3"] - int(random.betavariate(2, 4) * 70))

        P = {0: 1.2, 1: 1.05, 2: 0.9, 3: 0.7}.get(int(info_serializavel.get("Estagio", 0)), 1)

        def gerar_valor(base, fator_min, fator_max, Pescala):
            vmin = int(base * fator_min)
            vmax = int(base * fator_max)
            vmax_real = int(vmax * Pescala)
            valor = random.randint(vmin, max(vmin, vmax_real))
            valor = min(valor, vmax)
            return valor, vmin, vmax

        atributos = ["Vida", "Atk", "Def", "SpA", "SpD", "Vel",
                     "Mag", "Per", "Ene", "EnR", "CrD", "CrC"]

        ivs = []
        for atributo in atributos:
            base = int(info_serializavel[atributo])
            valor, minimo, maximo = gerar_valor(base, 0.75, 1.25, P)
            iv = 0.0 if maximo == minimo else round(((valor - minimo) / (maximo - minimo)) * 100, 2)
            info_serializavel[f"IV_{atributo}"] = iv
            ivs.append(iv)

        info_serializavel["IV"] = round(sum(ivs) / len(ivs), 2)

        soma_atributos = sum([
            info_serializavel["Atk"],
            info_serializavel["Def"],
            info_serializavel["SpA"],
            info_serializavel["SpD"],
            info_serializavel["Vel"],
            info_serializavel["Mag"],
            info_serializavel["Per"],
            info_serializavel["Ene"],
            info_serializavel["EnR"] * 2,
            info_serializavel["CrD"] * 1.5,
            info_serializavel["CrC"] * 1.5
        ])

        total = (
            soma_atributos * 2 +
            info_serializavel["Vida"] +
            info_serializavel.get("Sinergia", 0) * 10 +
            (info_serializavel.get("Habilidades", 0) + info_serializavel.get("Equipaveis", 0)) * 20
        )
        info_serializavel["Total"] = int(total)

        ID = f"{info_serializavel['Nome']}{random.randint(1, 2000)}"
        info_serializavel["ID"] = ID

        string_comprimida = CompactarPokemon(info_serializavel)

        PokemonAtivo = {
            "info": string_comprimida,
            "loc": [X, Y],
            "id": ID,
            "extra": {
                "TamanhoMirando": 50 - info_serializavel["Nivel"] + random.randint(-5, 10),
                "VelocidadeMirando": max(
                    0.8,
                    info_serializavel["IV"] / 10 + random.randint(0, int(max(1, info_serializavel["Vel"]) / 10)) - 1
                ),
                "Dificuldade": info_serializavel["Total"] * info_serializavel["Nivel"] / 100 + random.randint(0, 30),
                "Frutas": 0
            }
        }

        pokemons_ativos.append(PokemonAtivo)

def GerarBau(players_ativos, baus_ativos):
    """
    Para cada player ativo:
      - sorteia a raridade do baú
      - tenta posicionar UM baú no anel [18, 36] ao redor do player
      - não pode ficar a < 18 de QUALQUER player
      - não pode ficar a < 10 de outro baú
      - respeita LIMITE_BAUS_ANEL por player (no anel dele)
    Não retorna nada; apenas muta baus_ativos (dict {id: [x, y, raridade]}).
    """
    RAIO_VISAO = 18
    ANEL_MAX = RAIO_VISAO * 2  # 36
    MAX_TENTATIVAS_POS = 20
    MIN_DIST_BAU = 10
    LIMITE_BAUS_ANEL = 10  # <- ajuste aqui se quiser outro teto por anel

    # distribuição cumulativa (1..6)
    raridades = [
        (1, 40),   # Comum
        (2, 65),   # Incomum
        (3, 82),   # Raro
        (4, 92),   # Épico
        (5, 98),   # Lendário
        (6, 100),  # Mítico
    ]

    if not players_ativos:
        return

    # cache de locs de players para checks rápidos
    locs_players = [(p["Loc"][0], p["Loc"][1]) for p in players_ativos.values() if p and "Loc" in p]

    for _, pdata in players_ativos.items():
        if not pdata or "Loc" not in pdata:
            continue
        owner_loc = tuple(pdata["Loc"])

        # 1) contar baús já no anel do player
        count_anel = 0
        for bx, by, _rar in baus_ativos.values():
            d = math.dist(owner_loc, (bx, by))
            if RAIO_VISAO <= d <= ANEL_MAX:
                count_anel += 1
        if count_anel >= LIMITE_BAUS_ANEL:
            continue  # anel do dono já está no limite

        # 2) sorteio de raridade
        s = random.randint(1, 100)
        raridade = 1
        for r, limite in raridades:
            if s <= limite:
                raridade = r
                break

        # 3) tentar posicionamento no anel [18, 36] do dono
        colocado = False
        for _ in range(MAX_TENTATIVAS_POS):
            ang = random.uniform(0, 2 * math.pi)
            dist = random.uniform(RAIO_VISAO, ANEL_MAX)  # [18, 36]
            X = int(owner_loc[0] + math.cos(ang) * dist)
            Y = int(owner_loc[1] + math.sin(ang) * dist)

            # (a) não pode estar a < 18 de NENHUM player
            if any(math.dist((X, Y), lp) < RAIO_VISAO for lp in locs_players):
                continue

            # (b) manter distância mínima de outros baús
            if any(math.dist((X, Y), (bx, by)) < MIN_DIST_BAU for (bx, by, _r) in baus_ativos.values()):
                continue

            # posição válida
            colocado = True
            break

        if not colocado:
            continue

        # 4) gerar ID único e registrar
        novo_id = random.randint(10000, 999999)
        while novo_id in baus_ativos:
            novo_id = random.randint(10000, 999999)

        baus_ativos[novo_id] = [X, Y, raridade]

