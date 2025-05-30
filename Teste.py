import time

class Pokemon:
    def __init__(self, Dados):

        self.Nome = Dados["nome"]
        self.Tipo = Dados["tipo"]
        self.VidaMax = Dados["vida"]
        self.Vida = Dados["vida"]
        
        self.Alcance = Dados["alcance"]
        self.Estilo = Dados["estilo"]
        self.Dano = Dados["dano"]

        self.Atk = Dados["atk"]
        self.SpAtk = Dados["spatk"]
        self.Def = Dados["def"]
        self.SpDef = Dados["spdef"]
        self.Vel = Dados["vel"]
        self.AtkVel = Dados["atkvel"]

        self.VarAtk = 0
        self.VarSpAtk = 0
        self.VarDef = 0
        self.VarSpDef = 0
        self.VarVel = 0
        self.VarAtkVel = 0

        self.Habilidades = []
        self.Efeitos = []

        self.Pos = 0
        self.Linha = 0

        self.Movimento = 0
        self.Vataque = 0
        self.Energia = 0
        self.GanhoEnergia = 10

        self.Alvo = None
        self.PodeMover = True
        self.Vivo = True
    
    def LevarDano():
        pass

    def TomarDano():
        pass

class Jogador:
    def __init__(self):
        
        self.Ouro = 5
        self.Ativos = []
        self.Banco = []
        self.Loja = []
        self.Nivel = 1

Tick = 0

def Batalha(player1, player2):

    for pokemon in player2.Ativos:
        pokemon.Pos = 12 - pokemon.Pos

    while True:
        Tick += 1

        for pokemon in player2.Ativos + player1.Ativos:
            pokemon.PodeMover = True
            for Habilidade in pokemon.Habilidades:
                if Tick == 1:
                    if Habilidade.estilo == "Inicial":
                        Habilidade.exe(pokemon)
                else:
                    if Habilidade.estilo == "Ativa":
                        if pokemon.Energia >= Habilidade.Custo:
                            pokemon.Energia -= Habilidade.Custo
                            Habilidade.exe(pokemon)


        for pokemon in player1.Ativos:
            pokemon.Alvo = None
            for dist in range(1, pokemon.alcance + 1):
                for inimigo in player2.Ativos:
                    if pokemon.Linha == inimigo.Linha and inimigo.Pos == pokemon.Pos - dist:
                        pokemon.Alvo = inimigo
                        break
                if pokemon.Alvo:
                    break

            if pokemon.Alvo is not None:
                if pokemon.Vataque >= 15:
                    pokemon.Vataque -= 15
                    pokemon.Atacar(pokemon.Alvo)
                    pokemon.Energia += pokemon.GanhoEnergia
                    for Habilidade in pokemon.Habilidades:
                        if Habilidade.Estilo == "Passiva":
                            if Habilidade.EstiloPassiva == "Ataque":
                                Habilidade.exe(pokemon)
                else:
                    pokemon.Vataque += pokemon.VelAtk
        

        for pokemon in player2.Ativos:
            pokemon.Alvo = None
            for dist in range(1, pokemon.alcance + 1):
                for inimigo in player1.Ativos:
                    if pokemon.Linha == inimigo.Linha and inimigo.Pos == pokemon.Pos - dist:
                        pokemon.Alvo = inimigo
                        break
                if pokemon.Alvo:
                    break

            if pokemon.Alvo is not None:
                if pokemon.Vataque >= 15:
                    pokemon.Vataque -= 15
                    pokemon.Atacar(pokemon.Alvo)
                    pokemon.Energia += pokemon.GanhoEnergia
                    for Habilidade in pokemon.Habilidades:
                        if Habilidade.Estilo == "Passiva":
                            if Habilidade.EstiloPassiva == "Ataque":
                                Habilidade.exe(pokemon)
                else:
                    pokemon.Vataque += pokemon.VelAtk

        for pokemon in player1.Ativos:
            for pokemonn in player1.Ativos:
                if pokemon.Pos + 1 == pokemonn.Pos:
                    if pokemon.Linha == pokemonn.Linha:
                        pokemon.PodeMover = False
            if pokemon.Alvo is not None and pokemon.PodeMover is True:
                pokemon.PodeMover = False
        
        for pokemon in player2.Ativos:
            for pokemonn in player2.Ativos:
                if pokemon.Pos - 1 == pokemonn.Pos:
                    if pokemon.Linha == pokemonn.Linha:
                        pokemon.PodeMover = False
            if pokemon.Alvo is not None and pokemon.PodeMover is True:
                pokemon.PodeMover = False


        for pokemon in player2.Ativos + player1.Ativos:
            if pokemon.PodeMover == True:
                pokemon.Movimento += pokemon.Vel
        
        for pokemon in player1.Ativos:
            if pokemon.Movimento >= 100:
                pokemon.Movimento -= 100
                if pokemon.PodeMover == True:
                    pokemon.Pos += 1

        for pokemon in player2.Ativos:
            if pokemon.Movimento >= 100:
                pokemon.Movimento -= 100
                if pokemon.PodeMover == True:
                    pokemon.Pos -= 1
        
        for pokemon1 in player1.Ativos:
            for pokemon2 in player2.Ativos:
                if pokemon1.Pos == pokemon2.Pos:
                    if pokemon1.Linha == pokemon2.Linha:
                        if pokemon1.Vel > pokemon2.Vel:
                            pokemon2.Pos += 1
                            pokemon2.Movimento += 100
                        elif pokemon1.Vel < pokemon2.Vel:
                            pokemon1.Pos -= 1
                            pokemon1.Movimento += 100
                        else:
                            if pokemon1.AtkVel > pokemon2.AtkVel:
                                pokemon2.Pos += 1
                                pokemon2.Movimento += 100
                            elif pokemon1.AtkVel < pokemon2.AtkVel:
                                pokemon1.Pos -= 1
                                pokemon1.Movimento += 100
                            else:
                                if pokemon1.Code > pokemon2.Code:
                                    pokemon2.Pos += 1
                                    pokemon2.Movimento += 100
                                else:
                                    pokemon1.Pos -= 1
                                    pokemon1.Movimento += 100
        
        for pokemon in player1.Ativos:
            if pokemon.Pos == 13:
                pokemon.Pontuar()
        
        for pokemon in player2.Ativos:
            if pokemon.Pos == 0:
                pokemon.Pontuar()
                    
        time.sleep(0.5)



        
        
        
