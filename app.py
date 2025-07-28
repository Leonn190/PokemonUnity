from flask import Flask
from flask_cors import CORS  # Importa do módulo externo
from Conta import conta_bp
from Ativador import pokemons_bp
import os
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

if __name__ == '__main__':
    with app.app_context():
        Variaveis.db.create_all()  # Cria as tabelas no SQLite
    app.run(debug=True)