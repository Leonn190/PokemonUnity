from flask import Blueprint, request, jsonify
import flask 
from GeradorPokemon import gerar_pokemon_para_player
import random
import math
import pandas as pd
import time
import threading

df = pd.read_csv("Pokemons.csv")

pokemons_bp = Blueprint('pokemons', __name__)

pokemons_ativos = []
players_ativos = {}

lock = threading.Lock()

@pokemons_bp.route('/Verificar', methods=['POST'])
def Verificar():
    data = request.get_json()
    posX = 0
    posY = 0
    code = str(data["Code"])

    with lock:
        players_ativos[code] = {
            "loc": [posX, posY],
            "code": code,
            "atividade": 100
        }

    raio = 60
    pokemons_proximos = []

    with lock:
        for pokemon in pokemons_ativos:
            if not pokemon or not pokemon.get("loc"):
                continue
            px, py = pokemon["loc"]
            distancia = math.sqrt((px - posX) ** 2 + (py - posY) ** 2)
            if distancia <= raio:
                pokemons_proximos.append(pokemon)

        # 👇 Força a geração de Pokémon na chamada
        Gerado = gerar_pokemon_para_player([posX, posY], players_ativos, pokemons_ativos)
        if Gerado:
            pokemons_ativos.append(Gerado)
        
        if pokemons_ativos and random.randint(15, 80) < len(pokemons_ativos):
                    pokemons_ativos.pop(random.randint(0, len(pokemons_ativos) - 1))

    return jsonify({
        "pokemons": pokemons_proximos,
        "Ativos": pokemons_ativos
    })
