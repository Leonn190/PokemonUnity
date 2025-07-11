from flask import Blueprint, request, jsonify
from Registros import Registros

conta_bp = Blueprint('conta', __name__)
Ativos = []

@conta_bp.route('/acessar', methods=['POST'])
def acessar_conta():
    data = request.get_json()
    
    if not data or 'codigo' not in data:
        return jsonify({'erro': 'É necessário enviar um código'}), 400

    codigo = data['codigo']

    if codigo not in Ativos:
        for Registro in Registros:
            if codigo == Registro["codigo"]:
                Ativos.append(codigo)
                return jsonify({
                    'mensagem': 'Conta acessada com sucesso',
                    'ativos': Ativos,
                    'conta': Registro
                }), 201
        return jsonify({'mensagem': 'Conta ainda não registrada', 'ativos': Ativos}), 202
    else:
        return jsonify({'mensagem': 'Conta já estava ativa', 'ativos': Ativos}), 200

@conta_bp.route('/salvar', methods=['POST'])
def salvar_conta():
    data = request.get_json()

    if not data or 'codigo' not in data:
        return jsonify({'erro': 'É necessário enviar um código'}), 400
    
    codigo = data['codigo']

    for i, Registro in enumerate(Registros):
        if codigo == Registro["codigo"]:
            Registros[i] = data
            return jsonify({'mensagem': 'Conta atualizada com sucesso'}), 200
    
    Registros.append(data)
    return jsonify({'mensagem': 'Conta registrada com sucesso'}), 201

@conta_bp.route('/sair', methods=['POST'])
def sair_conta():
    data = request.get_json()

    if not data or 'codigo' not in data:
        return jsonify({'erro': 'É necessário enviar um código'}), 400
    
    codigo = data['codigo']

    if codigo in Ativos:
        Ativos.remove(codigo)
        return jsonify({'mensagem': 'Conta desconectada', 'ativos': Ativos}), 200
    else:
        return jsonify({'mensagem': 'Conta não estava ativa'}), 202
    