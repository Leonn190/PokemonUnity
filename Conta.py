from flask import Blueprint
from Variaveis import db, Ligado, Ativo # Importa a instância compartilhada
from flask import request, jsonify
import json

conta_bp = Blueprint('conta', __name__)
Ativos = []

# Modelo Player para salvar os dados no banco
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(100), unique=True, nullable=False)
    dados = db.Column(db.Text, nullable=False)  # JSON serializado

    def to_dict(self):
        return {
            "codigo": self.codigo,
            "dados": json.loads(self.dados)
        }

@conta_bp.route('/acessar', methods=['POST'])
def acessar_conta():
    global Ativo, Ligado  # Garante acesso às variáveis globais
    data = request.get_json()
    
    if not data or 'codigo' not in data:
        return jsonify({'erro': 'É necessário enviar um código'}), 400

    if not Ativo:
        return jsonify({'mensagem': 'Servidor não esta ativado'}), 503

    if not Ligado:
        return jsonify({'mensagem': 'Servidor está desligado'}), 504

    codigo = data['codigo']

    if codigo not in Ativos:
        player = Player.query.filter_by(codigo=codigo).first()
        if player:
            Ativos.append(codigo)
            return jsonify({
                'mensagem': 'Conta acessada com sucesso',
                'ativos': Ativos,
                'conta': player.to_dict()
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

    player = Player.query.filter_by(codigo=codigo).first()
    if player:
        player.dados = json.dumps(data)
        db.session.commit()
        return jsonify({'mensagem': 'Conta atualizada com sucesso'}), 200
    
    novo_player = Player(codigo=codigo, dados=json.dumps(data))
    db.session.add(novo_player)
    db.session.commit()
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
