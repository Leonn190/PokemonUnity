from flask import Blueprint, request, jsonify
from Variaveis import db, Ligado, Ativo

Operator_bp = Blueprint('operator', __name__)

OperatorCode = 1900

@Operator_bp.route('/verificar-operador', methods=['POST'])
def verificar_operador():
    dados = request.get_json()
    codigo = dados.get("codigo")

    if str(codigo) == str(OperatorCode):
        return jsonify({"operador": True}), 200
    else:
        return jsonify({"operador": False}), 200


@Operator_bp.route('/ativar-servidor', methods=['GET'])
def ativar_servidor():
    global Ativo
    if not Ativo:
        db.create_all()
        Ativo = True
        return jsonify({"status": "ok", "mensagem": "Servidor ativado. Tabelas criadas."}), 200
    else:
        return jsonify({"status": "ok", "mensagem": "Servidor já estava ativo."}), 201


@Operator_bp.route('/ligar-desligar', methods=['POST'])
def ligar_desligar():
    global Ligado
    dados = request.get_json()
    comando = dados.get("ligar")  # True ou False

    if comando is True:
        Ligado = True
        return jsonify({"ligado": True, "mensagem": "Servidor ligado"}), 200
    elif comando is False:
        Ligado = False
        return jsonify({"ligado": False, "mensagem": "Servidor desligado"}), 200
    else:
        return jsonify({"erro": "Comando inválido. Use true ou false no campo 'ligar'."}), 400

@Operator_bp.route('/estado-server', methods=['GET'])
def ligar_desligar():
    return jsonify({"ligado": Ligado, "ativo": Ativo})
