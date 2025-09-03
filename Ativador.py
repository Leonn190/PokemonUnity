from flask import Blueprint, request, jsonify
from GeradorPokemon import GerarPokemon, GerarBau
import random
import math
import pandas as pd
import json
import Variaveis as V
from CriaMapa import Mapa

df = pd.read_csv("Pokemons.csv")

pokemons_bp = Blueprint('pokemons', __name__)

RAIO_VISAO = 18

def VerificarServer():
    """
    Roda apenas uma vez por ciclo (invocada pelo último player).
    - Gera novos pokémons e baús
    - Marca 'Fugiu' aleatoriamente
    - Incrementa e remove pokémons 'Fugiu'/'Capturado' após 20
    - Move pokémons (10% de chance, passo 2..4, em X ou Y)
    - Remove baús que não estejam no raio de visão (18) de nenhum player
    """
    # 1) Geração de novos pokémons (usa a função já criada)
    if len(V.PokemonsAtivos) < 100:
        GerarPokemon(V.PlayersAtivos, V.PokemonsAtivos)

    # 2) Chance de marcar alguém como 'Fugiu'
    if V.PokemonsAtivos and random.randint(0, 10) > 2:
        if random.randint(35, 80) < len(V.PokemonsAtivos):
            idx = random.randint(0, len(V.PokemonsAtivos) - 1)
            V.PokemonsAtivos[idx]["extra"]["Fugiu"] = V.PokemonsAtivos[idx]["extra"].get("Fugiu", 1)

    # 3) Incrementar contadores de Fugiu/Capturado e remover ao atingir 20
    novos_pokes = []
    for poke in V.PokemonsAtivos:
        if not poke:
            continue
        fugiu = poke["extra"].get("Fugiu", 0)
        capt = poke["extra"].get("Capturado", 0)
        if fugiu or capt:
            # incrementa 1 por verificação de server
            if fugiu:
                poke["extra"]["Fugiu"] = fugiu + 1
            if capt:
                poke["extra"]["Capturado"] = capt + 1
            # remove se atingir 20
            if poke["extra"].get("Fugiu", 0) >= 30 or poke["extra"].get("Capturado", 0) >= 30:
                continue  # não mantém
        novos_pokes.append(poke)
    V.PokemonsAtivos = novos_pokes

    # 4) Movimento aleatório dos pokémons (10% de chance cada)
    for poke in V.PokemonsAtivos:
        if not poke or not poke.get("loc"):
            continue
        if poke["extra"].get["Irritado"]:
            chanc = 0.14
        else:
            chanc = 0.07
        if random.random() < chanc:
            # movimento no eixo X
            if random.choice([True, False]):
                step_x = random.randint(1, 3) * random.choice([-1, 1])
                poke["loc"][0] += step_x
            # movimento no eixo Y
            if random.choice([True, False]):
                step_y = random.randint(1, 3) * random.choice([-1, 1])
                poke["loc"][1] += step_y

    # 5) Geração de baús baseada nos players (usar loc do "último" processado não faz sentido aqui)
    #    A estratégia simples: escolher 1 player aleatório como origem da tentativa de gerar um baú
    if V.PlayersAtivos:
        GerarBau(V.PlayersAtivos, V.BausAtivos)

    # 6) Remoção de baús: nunca remover os que estiverem no raio 18 de QUALQUER player
    #    Remover com pequena chance (5%) os demais, para evitar poluição
    if V.BausAtivos:
        # precomputar locs dos players
        locs_players = [tuple(p["Loc"]) for p in V.PlayersAtivos.values() if p and "Loc" in p]
        remover_ids = []
        for bau_id, (bx, by, raridade) in list(V.BausAtivos.items()):
            perto_de_algum = False
            for (px, py) in locs_players:
                if math.dist((bx, by), (px, py)) <= RAIO_VISAO * 2:
                    perto_de_algum = True
                    break
            if not perto_de_algum:
                # baú fora da visão de todos — pode ser removido com chance
                if random.random() < 0.1:
                    remover_ids.append(bau_id)
        for bid in remover_ids:
            V.BausAtivos.pop(bid, None)

@pokemons_bp.route('/Verificar', methods=['POST'])
def Verificar():
    data = request.get_json()
    raio = data["Raio"]
    posX = data["X"]
    posY = data["Y"]
    code = str(data["Code"])
    dados = data["Dados"]

    # --- Atualiza dados do jogador ---
    if code not in V.PlayersAtivos:
        return '', 204
    V.PlayersAtivos[code].update({"Loc": [posX, posY]})
    V.PlayersAtivos[code].setdefault("Conta", {})
    V.PlayersAtivos[code]["Conta"].update({
        "DadosPassageiros": {
            "Nome": dados["Nome"],
            "Skin": dados["Skin"],
            "Nivel": dados["Nivel"],
            "Velocidade": dados["Velocidade"],
            "Loc": dados["Loc"],
            "Selecionado": dados["Selecionado"],
            "Angulo": dados["Angulo"],
            "ID": dados["ID"]
        }
    })

    # --- Listas próximas ---
    # Pokémons
    pokemons_proximos = []
    for pokemon in V.PokemonsAtivos:
        if not pokemon or not pokemon.get("loc"):
            continue
        px, py = pokemon["loc"]
        if math.dist((px, py), (posX, posY)) <= raio:
            pokemons_proximos.append(pokemon)

    # Players (exceto o próprio)
    players_proximos = []
    for pid, player in V.PlayersAtivos.items():
        if not player or "Loc" not in player or pid == code:
            continue
        px, py = player["Loc"]
        if math.dist((px, py), (posX, posY)) <= raio:
            dados_passageiros = player.get("Conta", {}).get("DadosPassageiros")
            if dados_passageiros:
                players_proximos.append(dados_passageiros)

    # Baús próximos
    baus_proximos = []
    for bau_id, bau_data in V.BausAtivos.items():
        bx, by, raridade = bau_data
        if math.dist((bx, by), (posX, posY)) <= raio:
            baus_proximos.append({
                "ID": bau_id,
                "X": bx,
                "Y": by,
                "Raridade": raridade
            })

    # --- Apenas o último player chama o VerificarServer (if/else simples) ---
    # último = maior Code; Codes são strings numéricas
    # Pega a última chave do dicionário
    ultima_chave = next(reversed(V.PlayersAtivos))
    if ultima_chave == code:
        VerificarServer()

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
        'objetos': json.loads(mapa.objetos_json),
        'blocos': json.loads(mapa.blocos_json)
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

@pokemons_bp.route('/atualizar-pokemon', methods=['POST'])
def atualizar_pokemon():
    dados = request.get_json()

    if not dados:
        return jsonify({"erro": "JSON inválido ou vazio"}), 400

    # Espera-se que o JSON contenha pelo menos "id" e "extra", e possivelmente "Dados"
    pokemon_id = dados.get("id")
    extras = dados.get("extra")
    dados_compactados = dados.get("Dados")  # pode ser None se não enviado

    if pokemon_id is None:
        return jsonify({"erro": "ID do pokemon não fornecido"}), 400

    # Buscar o Pokémon na lista
    pokemon_encontrado = None
    for pokemon in V.PokemonsAtivos:
        if pokemon.get("id") == pokemon_id:
            pokemon_encontrado = pokemon
            break

    if pokemon_encontrado is None:
        return jsonify({"erro": "Pokémon não encontrado"}), 404

    # Atualiza o campo "info" com os dados compactados (se vierem no json)
    if dados_compactados is not None:
        pokemon_encontrado["info"] = dados_compactados

    # Atualiza o dicionário "extra" — atualiza/insere as chaves recebidas
    if isinstance(extras, dict):
        pokemon_encontrado_extra = pokemon_encontrado.get("extra", {})
        pokemon_encontrado_extra.update(extras)
        pokemon_encontrado["extra"] = pokemon_encontrado_extra
    else:
        return jsonify({"erro": "'extra' deve ser um dicionário"}), 400

    return jsonify({"mensagem": f"Pokémon {pokemon_id} atualizado com sucesso"}), 200
