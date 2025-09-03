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
    id = Column(Integer, primary_key=True)  # <-- ESSENCIAL
    dificuldade = Column(int, nullable=False)
