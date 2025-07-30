from flask import Flask
from flask import request, jsonify
from flask_cors import CORS  # Importa do módulo externo
from Conta import conta_bp
from Ativador import pokemons_bp
import os
from CriaMapa import Mapa
import json
from ServerOperator import Operator_bp
import Variaveis

app = Flask(__name__)
CORS(app)

# Configuração do banco

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco com o app
Variaveis.db.init_app(app)

# Registra os Blueprints
app.register_blueprint(conta_bp)
app.register_blueprint(pokemons_bp)
app.register_blueprint(Operator_bp)

@app.route("/rotas")
def rotas():
    mapa = Mapa.query.first()  # pega o único mapa (ou o primeiro)
    if not mapa:
        return jsonify({'erro': 'Mapa não encontrado'}), 404
    
    return jsonify({
        'biomas': json.loads(mapa.biomas_json),
        'objetos': json.loads(mapa.objetos_json)
    }), 200

if __name__ == '__main__':
    with app.app_context():
        Variaveis.db.create_all()  # Cria as tabelas no SQLite
    app.run(debug=True)
