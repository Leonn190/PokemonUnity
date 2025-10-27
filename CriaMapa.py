from collections import deque, defaultdict
import Variaveis as V
import numpy as np
from sqlalchemy import Column, Text, Integer

class Mapa(V.db.Model):
    __tablename__ = "mapa"
    id = Column(Integer, primary_key=True)  # <-- ESSENCIAL
    biomas_json = Column(Text, nullable=False)
    objetos_json = Column(Text, nullable=False)
    blocos_json = Column(Text, nullable=False)

class ServerConfig(V.db.Model):
    __tablename__ = "config"
    id = V.db.Column(V.db.Integer, primary_key=True)  # <- certo
    dificuldade = V.db.Column(V.db.Integer, nullable=False)
