from flask import Blueprint
import Variaveis as V # Importa a instância compartilhada
from flask import request, jsonify
from CriaMapa import Mapa
import json

conta_bp = Blueprint('conta', __name__)

# Modelo Player para salvar os dados no banco
class Player(V.db.Model):
    id = V.db.Column(V.db.Integer, primary_key=True)
    codigo = V.db.Column(V.db.String(100), unique=True, nullable=False)
    dados = V.db.Column(V.db.Text, nullable=False)  # JSON serializado

    def to_dict(self):
        return {
            "codigo": self.codigo,
            "dados": json.loads(self.dados)
        }

@conta_bp.route('/acessar', methods=['POST'])
def acessar_conta():
    global V
    data = request.get_json()

    if not data or 'codigo' not in data:
        return jsonify({'erro': 'É necessário enviar um código'}), 400

    if not V.Ativo:
        return jsonify({'mensagem': 'Servidor não está ativado'}), 503

    if not V.Ligado:
        return jsonify({'mensagem': 'Servidor está desligado'}), 504

    codigo = data['codigo']

    if codigo not in V.PlayersAtivos:
        player = Player.query.filter_by(codigo=codigo).first()
        if player:
            Conteudo = player.to_dict()
            V.PlayersAtivos[codigo] = {
                "Code": codigo,
                "Conta": Conteudo,
                "Loc": Conteudo["dados"]["personagem"]["Loc"]
            }
            return jsonify({
                'mensagem': 'Conta acessada com sucesso',
                'ativos': list(V.PlayersAtivos.keys()),
                'conta': player.to_dict()
            }), 201
        return jsonify({'mensagem': 'Conta ainda não registrada', 'ativos': list(V.PlayersAtivos.keys())}), 202
    else:
        return jsonify({
            'mensagem': 'Conta já estava ativa',
            'ativos': list(V.PlayersAtivos.keys()),
            'conta': V.PlayersAtivos[codigo]["Conteudo"]
        }), 200

@conta_bp.route('/salvar', methods=['POST'])
def salvar_conta():
    data = request.get_json()

    if not data or 'codigo' not in data:
        return jsonify({'erro': 'É necessário enviar um código'}), 400
    
    codigo = data['codigo']

    player = Player.query.filter_by(codigo=codigo).first()
    if player:
        player.dados = json.dumps(data)
        V.db.session.commit()
        return jsonify({'mensagem': 'Conta atualizada com sucesso'}), 200
    
    novo_player = Player(codigo=codigo, dados=json.dumps(data))
    V.db.session.add(novo_player)
    V.db.session.commit()
    return jsonify({'mensagem': 'Conta registrada com sucesso'}), 201

@conta_bp.route('/sair', methods=['POST'])
def sair_conta():
    data = request.get_json()

    if not data or 'codigo' not in data:
        return jsonify({'erro': 'É necessário enviar um código'}), 400

    codigo = data['codigo']

    if codigo in V.PlayersAtivos:
        del V.PlayersAtivos[codigo]  # Remove a entrada do dicionário
        return jsonify({'mensagem': 'Conta desconectada', 'ativos': list(V.PlayersAtivos.keys())}), 200
    else:
        return jsonify({'mensagem': 'Conta não estava ativa'}), 202
    
@conta_bp.route('/contas', methods=['GET'])
def listar_contas():
    contas = Player.query.all()
    contas_dict = [conta.to_dict() for conta in contas]
    return jsonify({'contas': contas_dict}), 200

@conta_bp.route('/mapaa', methods=['GET'])
def pegar_mapa():
    mapa = Mapa.query.first()  # pega o único mapa (ou o primeiro)
    if not mapa:
        return jsonify({'erro': 'Mapa não encontrado'}), 404
    
    return jsonify({
        'biomas': json.loads(mapa.biomas_json),
        'objetos': json.loads(mapa.objetos_json)
    }), 200
