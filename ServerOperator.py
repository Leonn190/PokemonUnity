from flask import Blueprint, request, jsonify
from Variaveis import db
from sqlalchemy import inspect
import Variaveis

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
    global Variaveis
    if not Variaveis.Ativo:
        db.create_all()
        Variaveis.Ativo = True
        return jsonify({"status": "ok", "mensagem": "Servidor ativado. Tabelas criadas."}), 200
    else:
        return jsonify({"status": "ok", "mensagem": "Servidor já estava ativo."}), 201


@Operator_bp.route('/ligar-desligar', methods=['POST'])
def ligar_desligar():
    global Variaveis
    dados = request.get_json()
    comando = dados.get("ligar")  # True ou False

    if comando is True:
        Variaveis.Ligado = True
        return jsonify({"ligado": True, "mensagem": "Servidor ligado"}), 200
    elif comando is False:
        Variaveis.Ligado = False
        return jsonify({"ligado": False, "mensagem": "Servidor desligado"}), 200
    else:
        return jsonify({"erro": "Comando inválido. Use true ou false no campo 'ligar'."}), 400

@Operator_bp.route('/estado-server', methods=['GET'])
def verifica_estado():
    return jsonify({"ligado": Variaveis.Ligado, "ativo": Variaveis.Ativo})

@Operator_bp.route('/resetar-servidor', methods=['POST'])
def resetar_servidor():
    global Variaveis
    if Variaveis.Ativo:
        db.drop_all()     # Apaga todas as tabelas
        Variaveis.Ativo = False     # Marca o servidor como desativado
        Variaveis.Ligado = False
        return jsonify({"status": "ok", "mensagem": "Servidor resetado. Todas as tabelas foram removidas."}), 200
    else:
        return jsonify({"status": "aviso", "mensagem": "Servidor já estava desativado. Nenhuma tabela foi removida."}), 202

@Operator_bp.route('/verifica-servidor-ativo', methods=['GET'])
def VerificaServerAtivo():
    global Variaveis

    inspetor = inspect(db.engine)
    tabelas_existentes = inspetor.get_table_names()

    if len(tabelas_existentes) > 0:
        Variaveis.Ativo = True
        return jsonify({"status": "ok", "mensagem": "Servidor ativo. Tabelas detectadas."}), 200
    else:
        Variaveis.Ativo = False
        return jsonify({"status": "erro", "mensagem": "Servidor inativo. Nenhuma tabela encontrada."}), 503
    