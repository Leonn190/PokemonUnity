from flask import Blueprint, request, jsonify
from GeradorPokemon import gerar_pokemon_para_player, gerar_bau
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
        "Selecionado": dados["Selecionado"],
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
    if V.PokemonsAtivos and random.randint(20, 100) < len(V.PokemonsAtivos):
        V.PokemonsAtivos.pop(random.randint(0, len(V.PokemonsAtivos) - 1))

    gerar_bau([posX, posY], V.PlayersAtivos,V.BausAtivos)

    # Baús próximos
    baus_proximos = []
    for bau_id, bau_data in V.BausAtivos.items():
        bx, by, raridade = bau_data
        distancia = math.sqrt((bx - posX) ** 2 + (by - posY) ** 2)
        if distancia <= raio:
            baus_proximos.append({
                "ID": bau_id,
                "X": bx,
                "Y": by,
                "Raridade": raridade
            })

    return jsonify({
        "pokemons": pokemons_proximos,
        "players": players_proximos,
        "baus": baus_proximos
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

@pokemons_bp.route('/remover-bau', methods=['POST'])
def remover_bau():
    dados = request.get_json()
    bau_id = dados.get("id")

    if bau_id is None:
        return jsonify({"erro": "ID do baú não fornecido"}), 400

    if bau_id not in V.BausAtivos:
        return jsonify({"erro": "Baú não encontrado"}), 404

    del V.BausAtivos[bau_id]

    return jsonify({"mensagem": f"Baú {bau_id} removido com sucesso"}), 200

@pokemons_bp.route('/remover-pokemon', methods=['POST'])
def remover_pokemon():
    dados = request.get_json()
    pokemon_id = dados.get("id")

    if pokemon_id is None:
        return jsonify({"erro": "ID do pokemon não fornecido"}), 400

    # Procurar o índice do Pokémon com esse ID
    indice_remover = None
    for i, pokemon in enumerate(V.PokemonsAtivos):
        if pokemon.get("id") == pokemon_id:
            indice_remover = i
            break

    if indice_remover is None:
        return jsonify({"erro": "Pokémon não encontrado"}), 404

    # Remover o Pokémon encontrado
    removido = V.PokemonsAtivos.pop(indice_remover)

    return jsonify({"mensagem": f"Pokémon {removido['id']} removido com sucesso"}), 200

