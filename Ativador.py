from flask import Blueprint, request, jsonify
from GeradorPokemon import gerar_pokemon_para_player
import random
import math
import pandas as pd
import Variaveis as V

df = pd.read_csv("Pokemons.csv")

pokemons_bp = Blueprint('pokemons', __name__)

@pokemons_bp.route('/Verificar', methods=['POST'])
def Verificar():
    data = request.get_json()
    raio = data["Raio"]
    posX = data["X"]
    posY = data["Y"]
    code = str(data["Code"])

    V.PlayersAtivos[code] = {
        "loc": [posX, posY],
        "code": code,
    }

    # Lista de Pokémon próximos
    pokemons_proximos = []
    for pokemon in V.PokemonsAtivos:
        if not pokemon or not pokemon.get("loc"):
            continue
        px, py = pokemon["loc"]
        distancia = math.sqrt((px - posX) ** 2 + (py - posY) ** 2)
        if distancia <= raio:
            pokemons_proximos.append(pokemon)

    # Lista de jogadores próximos (exceto o próprio jogador)
    players_proximos = []
    for pid, player in V.PlayersAtivos.items():
        if not player or "Loc" not in player or pid == code:
            continue
        px, py = player["Loc"]
        distancia = math.sqrt((px - posX) ** 2 + (py - posY) ** 2)
        if distancia <= raio:
            players_proximos.append(player)

    # Geração de novo Pokémon
    Gerado = gerar_pokemon_para_player([posX, posY], V.PlayersAtivos, V.PokemonsAtivos)
    if Gerado:
        V.PokemonsAtivos.append(Gerado)

    # Remoção randômica
    if V.PokemonsAtivos and random.randint(15, 80) < len(V.PokemonsAtivos):
        V.PokemonsAtivos.pop(random.randint(0, len(V.PokemonsAtivos) - 1))

    return jsonify({
        "pokemons": pokemons_proximos,
        "players": players_proximos,
    })

@pokemons_bp.route('/Mapa', methods=['GET'])
def Mapa():
    return jsonify({
        "GridBiomas": V.GridBiomas,
        "GridObjetos": V.GridObjetos
    })
