from flask import Blueprint, request, jsonify
from sqlalchemy import inspect
import Variaveis as V
import json

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
    global V
    if not V.Ativo:
        from CriaMapa import gerar_e_salvar_mapa
        V.db.create_all()
        gerar_e_salvar_mapa(1000,1000)
        V.Ativo = True
        return jsonify({"status": "ok", "mensagem": "Servidor ativado. Tabelas criadas."}), 200
    else:
        return jsonify({"status": "ok", "mensagem": "Servidor já estava ativo."}), 201

@Operator_bp.route('/ligar-desligar', methods=['POST'])
def ligar_desligar():
    global V
    dados = request.get_json()
    comando = dados.get("ligar")  # True ou False
    from CriaMapa import Mapa

    if comando is True:
        V.Ligado = True

        # Buscar o mapa existente no banco de dados
        mapa_existente = V.db.session.query(Mapa).first()

        if mapa_existente:
            # Desserializar os JSONs
            V.GridBiomas = json.loads(mapa_existente.biomas_json)
            V.GridObjetos = json.loads(mapa_existente.objetos_json)
        else:
            return jsonify({"erro": "Nenhum mapa encontrado no banco de dados."}), 500

        return jsonify({"ligado": True, "mensagem": "Servidor ligado"}), 200

    elif comando is False:
        V.Ligado = False
        V.GridBiomas = None
        V.GridObjetos = None
        return jsonify({"ligado": False, "mensagem": "Servidor desligado"}), 200

    else:
        return jsonify({"erro": "Comando inválido. Use true ou false no campo 'ligar'."}), 400

@Operator_bp.route('/estado-server', methods=['GET'])
def verifica_estado():
    return jsonify({"ligado": V.Ligado, "ativo": V.Ativo})

@Operator_bp.route('/resetar-servidor', methods=['POST'])
def resetar_servidor():
    global V
    if V.Ativo:
        V.db.drop_all()     # Apaga todas as tabelas
        V.Ativo = False     # Marca o servidor como desativado
        V.Ligado = False
        return jsonify({"status": "ok", "mensagem": "Servidor resetado. Todas as tabelas foram removidas."}), 200
    else:
        return jsonify({"status": "aviso", "mensagem": "Servidor já estava desativado. Nenhuma tabela foi removida."}), 202

@Operator_bp.route('/verifica-servidor-ativo', methods=['GET'])
def VerificaServerAtivo():
    global V

    inspetor = inspect(V.db.engine)
    tabelas_existentes = inspetor.get_table_names()

    if len(tabelas_existentes) > 0:
        V.Ativo = True
        return jsonify({"status": "ok", "mensagem": "Servidor ativo. Tabelas detectadas."}), 200
    else:
        V.Ativo = False
        return jsonify({"status": "erro", "mensagem": "Servidor inativo. Nenhuma tabela encontrada."}), 503
    