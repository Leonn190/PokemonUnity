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

# Essa função será chamada para cada jogador ativo, com a posição
def gerar_pokemon_para_player(loc, players_ativos, pokemons_ativos):
    code = random.randint(1, 1100)
    pokemon = df[df["Code"] == code]

    if pokemon.empty:
        return False

    info_serializavel = pokemon.iloc[0].to_dict()

    if info_serializavel['Raridade'] == "-":
        return False

    if random.randint(1, 11) > int(info_serializavel['Raridade']):
        
        MAX_TENTATIVAS = 20
        for _ in range(MAX_TENTATIVAS):
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(35, 60)

            dx = math.cos(angulo) * distancia
            dy = math.sin(angulo) * distancia

            X = int(loc[0] + dx)
            Y = int(loc[1] + dy)

            pos_valida = True

            # Verifica distância de outros players
            for other_code, other_data in players_ativos.items():
                if other_data["Loc"] != loc:
                    ox, oy = other_data["Loc"]
                    if math.dist((X, Y), (ox, oy)) < 36:
                        pos_valida = False
                        break

            # Verifica distância de outros pokémons ativos
            if pos_valida:
                for poke in pokemons_ativos:
                    px, py = poke["loc"]
                    if math.dist((X, Y), (px, py)) < 4:  # distância mínima entre pokémons
                        pos_valida = False
                        break

            if pos_valida:
                break
        else:
            return False
        
        info_serializavel["Nivel"] = int(random.betavariate(2, 5) * 50)

        info_serializavel["%1"] = max(0, info_serializavel["%1"] - int(random.betavariate(2, 4) * 70))
        info_serializavel["%2"] = max(0, info_serializavel["%2"] - int(random.betavariate(2, 4) * 70))
        info_serializavel["%3"] = max(0, info_serializavel["%3"] - int(random.betavariate(2, 4) * 70))

        P = {0: 1.2, 1: 1.05, 2: 0.9, 3: 0.7}.get(int(info_serializavel["Estagio"]), 1)

        def gerar_valor(base, fator_min, fator_max, P):
            vmin = int(base * fator_min)
            vmax = int(base * fator_max)
            vmax_real = int(vmax * P)
            valor = random.randint(vmin, vmax_real)
            valor = min(valor, int(base * fator_max))
            return valor, vmin, vmax

        atributos = ["Vida", "Atk", "Def", "SpA", "SpD", "Vel",
                    "Mag", "Per", "Ene", "EnR", "CrD", "CrC"]

        ivs = []
        for atributo in atributos:
            base = int(info_serializavel[atributo])
            valor, minimo, maximo = gerar_valor(base, 0.75, 1.25, P)
            iv = ((valor - minimo) / (maximo - minimo)) * 100
            iv = round(iv, 2)
            # Não altera o valor base, apenas armazena o IV
            info_serializavel[f"IV_{atributo}"] = iv
            ivs.append(iv)

        IV = round(sum(ivs) / len(ivs), 2)
        info_serializavel["IV"] = IV

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
        ID = f"{info_serializavel['Nome']}{random.randint(1,2000)}"
        info_serializavel["ID"] = ID
        string_comprimida = CompactarPokemon(info_serializavel)

        PokemonAtivo = {
            "info": string_comprimida,
            "loc": [X, Y],
            "id": ID,
            "extra": {
                "TamanhoMirando": 55 - info_serializavel["Nivel"] + random.randint(1, 8),
                "VelocidadeMirando": max(0.5, info_serializavel["IV"] / 10 + random.randint(-1, int(info_serializavel["Vel"] / 10)) - 4),
                "Dificuldade": info_serializavel["Total"] / 10 + random.randint(0, 20),
                "Frutas": 0
            }
        }
        

        return PokemonAtivo

def gerar_bau(loc, players_ativos, baus_ativos):
    MAX_BAUS = 50
    if len(baus_ativos) >= MAX_BAUS:
        return

    # Nova distribuição de raridade (6 níveis), em porcentagens cumulativas
    # Exemplo: 1 - comum (40%), 2 - incomum (25%), ..., 6 - mítica (2%)
    raridades = [
        (1, 40),   # Comum
        (2, 65),   # Incomum
        (3, 82),   # Raro
        (4, 92),   # Épico
        (5, 98),   # Lendário
        (6, 100),  # Mítico
    ]

    # Sorteia número de 1 a 100
    sorte = random.randint(1, 100)
    raridade_selecionada = None
    for r, limite in raridades:
        if sorte <= limite:
            raridade_selecionada = r
            break

    MAX_TENTATIVAS = 20
    DIST_MIN_JOGADOR = 40
    DIST_MIN_BAU = 10

    for _ in range(MAX_TENTATIVAS):
        dx = random.randint(-60, 60)
        dy = random.randint(-60, 60)
        X = loc[0] + dx
        Y = loc[1] + dy

        # Verifica distância de todos os jogadores
        pos_valida = True
        for other_data in players_ativos.values():
            ox, oy = other_data["Loc"]
            if math.dist((X, Y), (ox, oy)) < DIST_MIN_JOGADOR:
                pos_valida = False
                break

        if not pos_valida:
            continue

        # Verifica distância de outros baús
        for bau_data in baus_ativos.values():
            bx, by, _ = bau_data
            if math.dist((X, Y), (bx, by)) < DIST_MIN_BAU:
                pos_valida = False
                break

        if pos_valida:
            novo_id = random.randint(10000, 999999)
            while novo_id in baus_ativos:
                novo_id = random.randint(10000, 999999)

            baus_ativos[novo_id] = [X, Y, raridade_selecionada]
            return

    return
