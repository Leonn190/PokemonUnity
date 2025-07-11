from flask import Blueprint, request, jsonify
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
Rodando = False  # Flag global para controlar o loop

def iniciar_loop_geracao():
    global Rodando
    if Rodando:
        return  # Já está rodando, não inicie outro

    Rodando = True

    def loop():
        global Rodando

        while True:
            ativos = [p for p in players_ativos.values() if p["atividade"] > 0]

            if not ativos:
                Rodando = False
                break  # Encerra o loop se ninguém estiver ativo

            for player in ativos:
                player["atividade"] -= 1
                Gerado = gerar_pokemon_para_player(player["loc"],players_ativos)
                if Gerado is not False:
                    pokemons_ativos.append(Gerado)  # Função auxiliar com a posição do player
            
                # Limpeza aleatória
            if random.randint(15, 70) < len(pokemons_ativos):
                pokemons_ativos.pop(random.randint(0, len(pokemons_ativos) - 1))

            time.sleep(0.2)  # 5 vezes por segundo

    threading.Thread(target=loop, daemon=True).start()

# Essa rota continua recebendo os dados do player
@pokemons_bp.route('/Verificar', methods=['POST'])
def Verificar():
    data = request.get_json()
    posX = data["X"]
    posY = data["Y"]
    code = data["Code"]

    players_ativos[code] = {
        "loc": [posX, posY],
        "code": code,
        "atividade": 100
    }

    # Inicia o loop de geração se ainda não estiver rodando
    iniciar_loop_geracao()

    raio = 70
    pokemons_proximos = []

    for pokemon in pokemons_ativos:
        px, py = pokemon["loc"]
        distancia = math.sqrt((px - posX) ** 2 + (py - posY) ** 2)

        if distancia <= raio:
            pokemons_proximos.append(pokemon)

    return jsonify({"pokemons": pokemons_proximos})
