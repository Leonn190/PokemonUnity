from flask import Blueprint, request, jsonify
from GeradorPokemon import gerar_pokemon_para_player
import random
import math
import pandas as pd
import json
import Variaveis as V
from CriaMapa import Mapa

df = pd.read_csv("Pokemons.csv")

pokemons_bp = Blueprint('pokemons', __name__)

@pokemons_bp.route('/Verificar', methods=['POST'])
def Verificar():
    data = request.get_json()
    raio = data["Raio"]
    posX = data["X"]
    posY = data["Y"]
    code = str(data["Code"])
    dados = data["Dados"]

    V.PlayersAtivos[code].update({"Loc": [posX,posY]})
    V.PlayersAtivos[code]["Conta"].update({"DadosPassageiros": {
        "Nome": dados["Nome"],
        "Skin": dados["Skin"],
        "Nivel": dados["Nivel"],
        "Loc": dados["Loc"],
        "Esquerda": dados["Esquerda"],
        "Direita": dados["Direita"],
        "Angulo": dados["Angulo"]
        }})

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
            dados_passageiros = player.get("Conta", {}).get("DadosPassageiros")
            if dados_passageiros:
                players_proximos.append(dados_passageiros)

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
def pegar_mapa():
    mapa = Mapa.query.first()  # pega o único mapa (ou o primeiro)
    if not mapa:
        return jsonify({'erro': 'Mapa não encontrado'}), 405
    
    return jsonify({
        'biomas': json.loads(mapa.biomas_json),
        'objetos': json.loads(mapa.objetos_json)
    }), 200

