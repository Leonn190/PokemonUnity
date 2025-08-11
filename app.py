from flask import Flask
from flask_cors import CORS
from Conta import conta_bp
from Ativador import pokemons_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(conta_bp)
app.register_blueprint(pokemons_bp)

if __name__ == '__main__':
    app.run(debug=True)