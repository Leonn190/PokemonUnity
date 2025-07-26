from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy  # importe o SQLAlchemy

from Conta import conta_bp
from Ativador import pokemons_bp

app = Flask(__name__)
CORS(app)

# Configurações do banco (arquivo SQLite local 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cria a instância do banco ligada ao app
db = SQLAlchemy(app)

# Registra os Blueprints
app.register_blueprint(conta_bp)
app.register_blueprint(pokemons_bp)

if __name__ == '__main__':
    app.run(debug=True)
