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
    "IV_Mag", "IV_Per", "IV_Ene", "IV_EnR", "IV_CrD", "IV_CrC"
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

        info_serializavel["%1"] = max(0,info_serializavel["%1"] - int(random.betavariate(2, 4) * 70))
        info_serializavel["%2"] = max(0,info_serializavel["%2"] - int(random.betavariate(2, 4) * 70))
        info_serializavel["%3"] = max(0,info_serializavel["%3"] - int(random.betavariate(2, 4) * 70))

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
            info_serializavel[atributo] = int(valor)
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
            info_serializavel["EnR"],
            info_serializavel["CrD"],
            info_serializavel["CrC"]
        ])

        total = (
            soma_atributos * 2 +
            info_serializavel["Vida"] +
            info_serializavel.get("Sinergia", 0) * 10 +
            (info_serializavel.get("Habilidades", 0) + info_serializavel.get("Equipaveis", 0)) * 20
        )

        info_serializavel["Total"] = int(total)
        string_comprimida = CompactarPokemon(info_serializavel)

        ID = f"{info_serializavel["Nome"]}-{random.randint(1,200)}"

        PokemonAtivo = {
            "info": string_comprimida,
            "loc": [X, Y],
            "id": ID
        }

        return PokemonAtivo
    