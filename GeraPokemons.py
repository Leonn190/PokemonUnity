from flask import Blueprint, request, jsonify
import random
import math
import pandas as pd

df = pd.read_csv("Pokemons.csv")

pokemons_bp = Blueprint('pokemons', __name__)

pokemons_ativos = []

@pokemons_bp.route('/Gerar', methods=['POST'])
def Gerar():
    code = random.randint(1, 1100)
    pokemon = df[df["Code"] == code]

    if pokemon.empty:
        return jsonify({"status": "erro", "mensagem": "Código não encontrado no CSV"}), 400

    info_serializavel = pokemon.iloc[0].to_dict()

    if info_serializavel['Raridade'] == "-":
        return jsonify({"status": "ok", "mensagem": "Nada gerado (proibição)", "TentouGerar": info_serializavel['Nome']})

    if random.randint(1, 11) > int(info_serializavel['Raridade']):
        X = random.randint(1, 2000)
        Y = random.randint(1, 2000)
        info_serializavel["Nivel"] = int(random.betavariate(2, 5) * 50)

        if int(info_serializavel["Estagio"]) == 0:
            P = 1.2
        elif int(info_serializavel["Estagio"]) == 1:
            P = 1.05
        elif int(info_serializavel["Estagio"]) == 2:
            P = 0.9
        elif int(info_serializavel["Estagio"]) == 3:
            P = 0.7
        else:
            P = 1

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
            if atributo not in ["CrD", "CrC"]:
                valor = valor * (1 + (info_serializavel["Nivel"] * 0.01))
            ivs.append(iv)

        IV = round(sum(ivs) / len(ivs), 2)
        info_serializavel["ivs"] = ivs
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

        PokemonAtivo = {
            "info": info_serializavel,
            "loc": [X, Y]
        }

        pokemons_ativos.append(PokemonAtivo)

        # Limpeza aleatória se tiver muitos
        if random.randint(10, 60) < len(pokemons_ativos):
            pokemons_ativos.pop(random.randint(0, len(pokemons_ativos)-1))

        return jsonify({"status": "ok", "mensagem": "Pokémon gerado com sucesso", "Pokemon": info_serializavel['Nome'], "loc": PokemonAtivo["loc"]})
    else:
        return jsonify({"status": "ok", "mensagem": "Nada gerado (Raridade)", "TentouGerar": info_serializavel['Nome']})



@pokemons_bp.route('/Verificar', methods=['POST'])
def Verificar():
    data = request.get_json()
    posX = data["X"]
    posY = data["Y"]

    raio = 350
    pokemons_proximos = []

    for pokemon in pokemons_ativos:
        px, py = pokemon["loc"]
        distancia = math.sqrt((px - posX)**2 + (py - posY)**2)

        if distancia <= raio:
            pokemons_proximos.append(pokemon)

    return jsonify(pokemons_proximos)
