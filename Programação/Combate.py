from flask import Blueprint, request, jsonify

from LogicaCombate import ExecuteRodada, ExecutePartida, AtualizaDados

Combate_bp = Blueprint('combate', __name__)
salas_de_combate = {}

@Combate_bp.route('/Gerar', methods=['POST'])
def IniciandoCombate():
    data = request.get_json()

    code_jogador = data.get("meu_code")
    code_oponente = data.get("code_oponente")
    pokemons_recebidos = data.get("pokemons")  # lista de 6 dicionários

    if not code_jogador or not code_oponente or not isinstance(pokemons_recebidos, list) or len(pokemons_recebidos) != 6:
        return jsonify({"erro": "Dados inválidos (code ou pokemons)"}), 400

    sala_id = "-".join(sorted([str(code_jogador), str(code_oponente)]))

    # Se sala não existe, criar e registrar jogador1 e seus Pokémon
    if sala_id not in salas_de_combate:
        salas_de_combate[sala_id] = {
            "jogador1": code_jogador,
            "pokemons_jogador1": pokemons_recebidos,
            "jogador2": None,
            "pokemons_jogador2": None,
            "status": "aguardando"
        }
        return jsonify({"mensagem": "Sala criada, aguardando oponente", "sala": sala_id})

    sala = salas_de_combate[sala_id]

    # Se é o segundo jogador entrando na sala
    if sala["jogador1"] != code_jogador and sala["jogador2"] is None:
        sala["jogador2"] = code_jogador
        sala["pokemons_jogador2"] = pokemons_recebidos
        sala["status"] = "pronto"
        ExecutePartida(sala)
        return jsonify({"mensagem": "Combate pronto para iniciar", "sala": sala_id})

    # Se jogador já está na sala, apenas atualiza seus Pokémon se ainda não estiverem salvos
    if code_jogador == sala["jogador1"] and sala["pokemons_jogador1"] is None:
        sala["pokemons_jogador1"] = pokemons_recebidos

    if code_jogador == sala["jogador2"] and sala["pokemons_jogador2"] is None:
        sala["pokemons_jogador2"] = pokemons_recebidos


    return jsonify({"mensagem": "Você já está na sala", "sala": sala_id, "status": sala["status"]})

@Combate_bp.route('/Inicio', methods=['POST'])
def Inicio():
    data = request.get_json()

    code_jogador = data.get("meu_code")
    sala_id = data.get("sala")
    ativos = data.get("ativos")  # lista de dicts com "pokemon" e "local"

    if not code_jogador or not sala_id or not isinstance(ativos, list):
        return jsonify({"erro": "Dados inválidos"}), 400

    if sala_id not in salas_de_combate:
        return jsonify({"erro": "Sala não encontrada"}), 404

    sala = salas_de_combate[sala_id]
    partida = sala.get("partida")

    if not partida:
        return jsonify({"erro": "Partida ainda não iniciada"}), 400

    # Verifica quem é o jogador
    if code_jogador == partida.jogador1:
        lista_pokemons = partida.pokemons_jogador1
    elif code_jogador == partida.jogador2:
        lista_pokemons = partida.pokemons_jogador2
    else:
        return jsonify({"erro": "Jogador não pertence à sala"}), 403

    # Marca os pokémons ativos
    for entrada in ativos:
        idx = entrada.get("pokemon")
        local = entrada.get("local")

        if idx is None or local is None or not (0 <= idx < len(lista_pokemons)):
            return jsonify({"erro": f"Dados inválidos no ativo: {entrada}"}), 400

        pokemon = lista_pokemons[idx]
        pokemon.ativo = True
        pokemon.local = local

    # Atualiza status da sala
    if sala["status"] == "pronto":
        sala["status"] = "aguardando"
    elif sala["status"] == "aguardando":
        AtualizaDados(sala)
        sala["status"] = "rodando"

    return jsonify({"mensagem": "Pokémons posicionados com sucesso", "status": sala["status"]})

@Combate_bp.route('/VerificarInicio', methods=['POST'])
def VerificarInicio():
    data = request.get_json()
    sala_id = data.get("sala")

    if not sala_id:
        return jsonify({"erro": "ID da sala não fornecido"}), 400

    if sala_id not in salas_de_combate:
        return jsonify({"erro": "Sala não encontrada"}), 404

    sala = salas_de_combate[sala_id]
    status = sala.get("status", "indefinido")

    return jsonify({"status": status})

@Combate_bp.route('/FazerJogada', methods=['POST'])
def FazerJogada():
    data = request.get_json()

    code_jogador = data.get("meu_code")
    sala_id = data.get("sala")
    jogada = data.get("jogada")

    if not code_jogador or not sala_id or not jogada:
        return jsonify({"erro": "Dados inválidos"}), 400

    if sala_id not in salas_de_combate:
        return jsonify({"erro": "Sala inexistente"}), 404

    sala = salas_de_combate[sala_id]

    if code_jogador == sala.get("jogador1"):
        sala["jogada_jogador1"] = jogada
        sala["status_jogador1"] = "pronto"
    elif code_jogador == sala.get("jogador2"):
        sala["jogada_jogador2"] = jogada
        sala["status_jogador2"] = "pronto"
    else:
        return jsonify({"erro": "Jogador não pertence à sala"}), 403

    # Verifica se ambos já fizeram a jogada
    if sala.get("status_jogador1") == "pronto" and sala.get("status_jogador2") == "pronto":
        ExecuteRodada(salas_de_combate[sala_id])

    return jsonify({"mensagem": "Jogada registrada com sucesso"})

@Combate_bp.route('/VerificarJogada', methods=['POST'])
def VerificarJogada():
    data = request.get_json()
    sala_id = data.get("sala")
    code_jogador = data.get("meu_code")

    if not sala_id or not code_jogador:
        return jsonify({"erro": "Dados incompletos"}), 400

    if sala_id not in salas_de_combate:
        return jsonify({"erro": "Sala não encontrada"}), 404

    sala = salas_de_combate[sala_id]

    resposta = {
        "pokemons_jogador1": sala.get("pokemons_jogador1", []),
        "pokemons_jogador2": sala.get("pokemons_jogador2", []),
        "partida": sala.get("partidaDic", None)
    }

    log = sala.get("log")
    if log is not None:
        resposta["status"] = "ok"
        resposta["log"] = log

        # Marca que o jogador recebeu o log
        if code_jogador == sala.get("jogador1"):
            sala["status_jogador1"] = "recebido"
        elif code_jogador == sala.get("jogador2"):
            sala["status_jogador2"] = "recebido"

        # Se ambos já receberam, reinicia o turno
        if sala.get("status_jogador1") == "recebido" and sala.get("status_jogador2") == "recebido":
            sala["log"] = None
            sala["status_jogador1"] = "preparando"
            sala["status_jogador2"] = "preparando"
            sala["jogada_jogador1"] = None
            sala["jogada_jogador2"] = None
    else:
        resposta["status"] = "aguardando"

    return jsonify(resposta)

@Combate_bp.route('/VerificarEstado', methods=['POST'])

def VerificarEstado():
    data = request.get_json()
    sala_id = data.get("sala")

    if not sala_id:
        return jsonify({"erro": "ID da sala não fornecido"}), 400

    if sala_id not in salas_de_combate:
        return jsonify({"erro": "Sala não encontrada"}), 404

    sala = salas_de_combate[sala_id]

    # Verifica se já há um vencedor
    if "vencedor" in sala and "perdedor" in sala:
        resultado = {
            "vencedor": sala["vencedor"],
            "perdedor": sala["perdedor"]
        }
        # Apaga a sala após segunda verificação
        del salas_de_combate[sala_id]
        return jsonify(resultado)

    # Obtém as listas de pokémons
    pok1 = sala.get("pokemons_jogador1", [])
    pok2 = sala.get("pokemons_jogador2", [])

    # Verifica se todos estão com vida <= 0
    derrotado1 = all(pok.get("vida", 1) <= 0 for pok in pok1)
    derrotado2 = all(pok.get("vida", 1) <= 0 for pok in pok2)

    if derrotado1 and not derrotado2:
        sala["vencedor"] = sala["jogador2"]
        sala["perdedor"] = sala["jogador1"]
        return jsonify({"vencedor": sala["vencedor"], "perdedor": sala["perdedor"]})

    if derrotado2 and not derrotado1:
        sala["vencedor"] = sala["jogador1"]
        sala["perdedor"] = sala["jogador2"]
        return jsonify({"vencedor": sala["vencedor"], "perdedor": sala["perdedor"]})

    if derrotado1 and derrotado2:
        # Empate
        sala["vencedor"] = "empate"
        sala["perdedor"] = "empate"
        return jsonify({"vencedor": "empate", "perdedor": "empate"})

    # Ninguém perdeu ainda
    return jsonify({"status": "em andamento"})
