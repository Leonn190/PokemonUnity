import pandas as pd

df_Habilidades = pd.read_csv("Habilidades.csv")
df_Equipaveis = pd.read_csv("Equipaveis.csv")

from LeitorAtaques import ExecuteAtaque
from HabilidadesFunções import HabDic
from ItensFunções import IteDic
import random

efeitos_positivos = [
    "Regeneração",
    "Abençoado",
    "Imortal",
    "Fortificado",
    "Reforçado",
    "Amplificado",
    "Aprimorado",
    "Voando",
    "Flutuando",
    "Imune",
    "Energizado",
    "Preparado",
    "Provocando",
    "Furtivo",
    "Ilimitado"
    "Encantado",
    "Refletido",
    "Evasivo",
    "Focado",
    "Imparavel"
]

efeitos_negativos = [
    "Queimado",
    "Dormindo",
    "Envenenado",
    "Intoxicado",
    "Paralisado",
    "Incapacitado",
    "Vampirico",       
    "Encharcado",      
    "Quebrado",
    "Fragilizado",
    "Enfraquecido",
    "Neutralizado",
    "Enfeitiçado",
    "Atordoado"
    "Confuso",
    "Congelado",
    "Descarregado",
    "Bloqueado",
    "Amaldiçoado",
    "Enraizado"
]

class Pokemon:
    def __init__(self, dados: dict, dono: str):
        self.nome = dados.get("nome")
        self.jogador = dono
        self.estagio = dados.get("Estagio")
        self.raridade = dados.get("Raridade")
        self.Altura = dados.get("Altura")
        self.Peso = dados.get("Peso")

        self.Tipo1 = dados.get("Tipo1")
        self.Tipo2 = dados.get("Tipo2")
        self.Tipo3 = dados.get("Tipo3")

        self.FTipo1 = dados.get("%1")
        self.FTipo2 = dados.get("%2")
        self.FTipo3 = dados.get("%3")

        self.Tipo = [self.Tipo1,self.Tipo2,self.Tipo3]
        self.FTipo = [self.FTipo1,self.FTipo2,self.FTipo3]

        # --- Valores base (origem) ---
        self.base_vida = dados.get("vida")
        self.base_atk = dados.get("atk")
        self.base_def = dados.get("def")
        self.base_spA = dados.get("SpA")
        self.base_spD = dados.get("SpD")
        self.base_vel = dados.get("Vel")
        self.base_mag = dados.get("Mag")
        self.base_per = dados.get("Per")
        self.base_ene = dados.get("Ene")
        self.base_enR = dados.get("EnR")
        self.base_crD = dados.get("CrD")
        self.base_crC = dados.get("CrC")

        # --- Variação permanente (buffs/debuffs fixos) ---
        self.var_per_atk = 0
        self.var_per_def = 0
        self.var_per_spA = 0
        self.var_per_spD = 0
        self.var_per_vel = 0
        self.var_per_mag = 0
        self.var_per_per = 0
        self.var_per_ene = 0
        self.var_per_enR = 0
        self.var_per_crD = 0
        self.var_per_crC = 0

        # --- Variação temporária (status temporários) ---
        self.var_temp_vida = 0
        self.var_temp_atk = 0
        self.var_temp_def = 0
        self.var_temp_spA = 0
        self.var_temp_spD = 0
        self.var_temp_vel = 0
        self.var_temp_mag = 0
        self.var_temp_per = 0
        self.var_temp_ene = 0
        self.var_temp_enR = 0
        self.var_temp_crD = 0
        self.var_temp_crC = 0

        # --- Valor real (base + var_per + var_temp) ---
        self.vida = dados.get("Vida")
        self.atk = dados.get("Atk")
        self.Def = dados.get("Def")
        self.spA = dados.get("SpA")
        self.spD = dados.get("SpD")
        self.vel = dados.get("Vel")
        self.mag = dados.get("Mag")
        self.per = dados.get("Per")
        self.ene = dados.get("Ene")
        self.enR = dados.get("EnR")
        self.crD = dados.get("CrD")
        self.crC = dados.get("CrC")

        # -- Constrói as habilidades como dicionários --
        self.Habilidades = []
        for chave in ["Habilidade1", "Habilidade2", "Habilidade3"]:
            code = dados.get(chave)
            if code:
                linha = df_Habilidades[df_Habilidades["Code"] == code]
                if not linha.empty:
                    self.Habilidades.append(linha.iloc[0].to_dict())

        # -- Constrói os itens como dicionários --
        self.Itens = []
        for chave in ["Item1", "Item2", "Item3"]:
            code = dados.get(chave)
            if code:
                linha = df_Equipaveis[df_Equipaveis["Code"] == code]
                if not linha.empty:
                    self.Itens.append(linha.iloc[0].to_dict())

        self.local = None
        self.ativo = False

        self.DanoTurno = 0
        self.AtacouTurno = []

        self.Energia = self.ene / 2
        self.Sinergia = dados.get("Sinergia")
        self.vivo = True
        self.nivel = dados.get("Nivel", 0)
        self.ivs = dados.get("ivs", [])
        self.iv_total = dados.get("IV", 0)

        self.Efeitos = {}

        self.PodeUsarHabilidade = True
        self.PodeUsarPassivaItem = True
        self.Recuo = False
        self.Protegido = False
    
    def TomarDano(self, dano, Partida, atacante=None):
        
        if atacante is not None:
            if Partida.clima == "Chuva":
                if "fogo" in atacante.Tipo:
                    dano = dano * 0.7
                if "agua" in atacante.Tipo:
                    dano = dano * 1.3
            if Partida.clima == "Sol Forte":
                if "agua" in atacante.Tipo:
                    dano = dano * 0.7
                if "fogo" in atacante.Tipo:
                    dano = dano * 1.3

        # --- Efeito: Evasivo ---
        if self.Efeitos.get("Evasivo", 0) > 0:
            self.Efeitos["Evasivo"] = 0  # remove o efeito
            return  # desvia do dano completamente

        if self.PodeUsarHabilidade:
            for habilidade in self.Habilidades:
                if habilidade["Ativação"] == "AoTomarDano":
                    self, dano, atacante = HabDic[str(habilidade["Code"])](self, dano, atacante)
            
        if self.PodeUsarPassivaItem:
            for item in self.Itens:
                if item["Ativação"] == "AoTomarDano":
                    self, dano, atacante = IteDic[str(item["Code"])](self, dano, atacante)

        if self.Efeitos.get("Congelado", 0) > 0:
            dano = dano * 0.7

        # --- Efeito: Preparado ---
        elif self.Efeitos.get("Preparado", 0) > 0:
            self.Efeitos["Preparado"] = 0
            dano_original = dano
            dano = int(dano * 0.6)
            if atacante is not None:
                retribuicao = int(self.vel * 0.4)
                atacante.TomarDano(retribuicao, Partida, atacante=self)

        # --- Efeito: Refletido ---
        elif self.Efeitos.get("Refletido", 0) > 0:
            self.Efeitos["Refletido"] = 0
            dano_refletido = int(dano * 0.75)
            dano = int(dano * 0.25)
            if atacante is not None:
                atacante.TomarDano(dano_refletido, Partida, atacante=self)

        if self.Efeitos.get("Dormindo", 0) > 0:
            self.Efeitos["Dormindo"] = 0

        if atacante is not None:
            if self.Efeitos.get("Vampirico", 0) > 0:
                Vampirismo = dano * 0.25
                if atacante is not None:
                    atacante.ReceberCura(Vampirismo)
            
            self.AtacouTurno.append(atacante)
        
        self.DanoTurno += dano

        self.vida -= dano
        if self.vida < 0:
            self.vida = 0
        if self.vida == 0:
            if self.Efeitos.get("Imortal", 0) > 0:
                self.Efeitos["Imortal"] = 0
                self.vida = 1
                return  # Impede a morte, finaliza aqui

            self.vida = 0

            if self.PodeUsarHabilidade:
                for habilidade in self.Habilidades:
                    if habilidade["Ativação"] == "AoMorrer":
                        self, dano, atacante = HabDic[str(habilidade["Code"])](self, dano, atacante)
            
            if self.PodeUsarPassivaItem:
                for item in self.Itens:
                    if item["Ativação"] == "AoMorrer":
                        self, dano, atacante = IteDic[str(item["Code"])](self, dano, atacante)

            self.vivo = False
            self.local = None
            self.ativo = False
    
    def Curar(self, cura, alvo):

        if self.PodeUsarHabilidade:
            for habilidade in self.Habilidades:
                if habilidade["Ativação"] == "AoCurar":
                    cura, alvo = HabDic[str(habilidade["Code"])](cura, alvo)
            
        if self.PodeUsarPassivaItem:
            for item in self.Itens:
                if item["Ativação"] == "AoCurar":
                    cura, alvo = IteDic[str(item["Code"])](cura, alvo)

        alvo.ReceberCura(cura)
    
    def ReceberCura(self, cura):

        if self.Efeitos.get("Abençoado", 0) > 0:
            cura = int(cura * 1.3)

        if self.PodeUsarHabilidade:
            for habilidade in self.Habilidades:
                if habilidade["Ativação"] == "AoReceberCura":
                    cura = HabDic[str(habilidade["Code"])](cura)
                
        if self.PodeUsarPassivaItem:
            for item in self.Itens:
                if item["Ativação"] == "AoReceberCura":
                    cura = IteDic[str(item["Code"])](cura)
            
        self.vida = min(self.base_vida, self.vida + cura)

    def ModificarStatus(self, Status, Alteração):
        if Alteração < 0:
            if self.PodeUsarHabilidade:
                for habilidade in self.Habilidades:
                    if habilidade["Ativação"] == "AoPerderStatus":
                        self, Status, Alteração = HabDic[str(habilidade["Code"])](self, Status, Alteração)
                
            if self.PodeUsarPassivaItem:
                for item in self.Itens:
                    if item["Ativação"] == "AoPerderStatus":
                        self, Status, Alteração = IteDic[str(item["Code"])](self, Status, Alteração)
        elif Alteração > 0:
            if self.PodeUsarHabilidade:
                for habilidade in self.Habilidades:
                    if habilidade["Ativação"] == "AoGanharStatus":
                        self, Status, Alteração = HabDic[str(habilidade["Code"])](self, Status, Alteração)
                
            if self.PodeUsarPassivaItem:
                for item in self.Itens:
                    if item["Ativação"] == "AoGanharStatus":
                        self, Status, Alteração = IteDic[str(item["Code"])](self, Status, Alteração)
        if self.PodeUsarHabilidade:
                for habilidade in self.Habilidades:
                    if habilidade["Ativação"] == "AoMutarStatus":
                        self, Status, Alteração = HabDic[str(habilidade["Code"])](self, Status, Alteração)
                
        if self.PodeUsarPassivaItem:
            for item in self.Itens:
                if item["Ativação"] == "AoMutarStatus":
                    self, Status, Alteração = IteDic[str(item["Code"])](self, Status, Alteração)

        valor_atual = getattr(self, Status)
        setattr(self, Status, valor_atual + Alteração)

    def AplicarEfeito(self, efeito, alvo):
        
        turnos = max(1, self.mag // 10)

        if self.PodeUsarPassivaItem:
            if efeito in efeitos_positivos:
                for item in self.Itens:
                    if item["Ativação"] == "AplicarEfeitoPositivo":
                        self, turnos, efeito, alvo = IteDic[str(item["Code"])](self, turnos, efeito, alvo)
                        
        if self.PodeUsarPassivaItem:
            if efeito in efeitos_negativos:
                for item in self.Itens:
                    if item["Ativação"] == "AplicarEfeitoNegativo":
                        self, turnos, efeito, alvo = IteDic[str(item["Code"])](self, turnos, efeito, alvo)
        
        if self.PodeUsarHabilidade:
            if efeito in efeitos_positivos:
                for habilidade in self.Habilidades:
                    if habilidade["Ativação"] == "AplicarEfeitoPositivo":
                        self, turnos, efeito, alvo = HabDic[str(habilidade["Code"])](self, turnos, efeito, alvo)
                        
        if self.PodeUsarHabilidade:
            if efeito in efeitos_negativos:
                for habilidade in self.Habilidades:
                    if habilidade["Ativação"] == "AplicarEfeitoNegativo":
                        self, turnos, efeito, alvo = HabDic[str(habilidade["Code"])](self, turnos, efeito, alvo)

        alvo.ReceberEfeito(efeito, turnos)

    def ReceberEfeito(self, efeito, turnos):
        if self.Efeitos["Imune"] > 0 and efeito in efeitos_negativos:
            return
        if self.Efeitos["Bloqueado"] > 0 and efeito in efeitos_positivos:
            return
        if self.Efeitos["Amaldiçoado"] > 0 and efeito in efeitos_positivos:
            turnos *= 2
        
        Defesaturnos = self.mag // 10
        
        if self.PodeUsarPassivaItem:
            if efeito in efeitos_positivos:
                for item in self.Itens:
                    if item["Ativação"] == "ReceberEfeitoPositivo":
                        self, turnos, efeito, Defesaturnos = IteDic[str(item["Code"])](self, turnos, efeito, Defesaturnos)
                        
        if self.PodeUsarPassivaItem:
            if efeito in efeitos_negativos:
                for item in self.Itens:
                    if item["Ativação"] == "ReceberEfeitoNegativo":
                        self, turnos, efeito, Defesaturnos = IteDic[str(item["Code"])](self, turnos, efeito, Defesaturnos)
        
        if self.PodeUsarHabilidade:
            if efeito in efeitos_positivos:
                for habilidade in self.Habilidades:
                    if habilidade["Ativação"] == "ReceberEfeitoPositivo":
                        self, turnos, efeito, Defesaturnos = HabDic[str(habilidade["Code"])](self, turnos, efeito, Defesaturnos)
                        
        if self.PodeUsarHabilidade:
            if efeito in efeitos_negativos:
                for habilidade in self.Habilidades:
                    if habilidade["Ativação"] == "ReceberEfeitoNegativo":
                        self, turnos, efeito, Defesaturnos = HabDic[str(habilidade["Code"])](self, turnos, efeito, Defesaturnos)

        TurnosReal = max(1,turnos - Defesaturnos)

        if efeito not in self.Efeitos:
            self.Efeitos[efeito] = 0

        self.Efeitos[efeito] += TurnosReal
        if self.Efeitos[efeito] < 0:
            self.Efeitos[efeito] = 0

    def GanharEnergia(self):

        if self.Efeitos.get("Descarregado", 0) > 0:
            self.Energia += self.enR * 0.5
        elif self.Efeitos.get("Energizado", 0) > 0:
            self.Energia += self.enR * 1.5
        else:
            self.Energia += self.enR
        self.Energia = min([self.Energia, self.ene])
    
    def Mover(self, local, forçado):

        if forçado and self.Efeitos.get("Imparavel", 0) > 0:
            return

        if self.Efeitos.get("Enraizado", 0) > 0:
            return

        if self.PodeUsarPassivaItem:
            for item in self.Itens:
                if item["Ativação"] == "AoMover":
                    local, self, forçado = IteDic[str(item["Code"])](self, local, forçado)
        if self.PodeUsarHabilidade:
            for habilidade in self.Habilidades:
                if habilidade["Ativação"] == "AoMover":
                    local, self, forçado = HabDic[str(habilidade["Code"])](self, local, forçado)
        
        self.Local = local

    def FimTurno(self, Partida):

        self.PodeUsarHabilidade = True
        self.PodeUsarPassivaItem = True
        self.Recuo = False
        self.Protegido = False
        self.DanoTurno = 0
        self.AtacouTurno = []

        if Partida.clima == "Chuva":
            if self.Efeitos.get("Queimado", 0) > 0:
                self.Efeitos["Queimado"] -= 1
            if self.Efeitos.get("Encharcado", 0) > 0:
                self.Efeitos["Encharcado"] += 2
            if "gelo" in self.Tipo:
                self.ReceberCura(self.base_vida/20)
        elif Partida.clima == "Sol Forte":
            if self.Efeitos.get("Queimado", 0) > 0:
                self.Efeitos["Queimado"] += 2
            if self.Efeitos.get("Encharcado", 0) > 0:
                self.Efeitos["Encharcado"] -= 1
            if "gelo" in self.Tipo:
                self.TomarDano(self.base_vida/10, Partida)
        elif Partida.clima == "Tempestade de Areia":
            if bool(set(["metal", "pedra", "terrestre"]) & set(self.Tipo)) is False:
                self.TomarDano(self.base_vida/20, Partida)
        elif Partida.clima == "Chuva Acida":
            if "venenoso" in self.Tipo:
                self.ReceberCura(self.base_vida * 0.07)
            else:
                self.TomarDano(self.base_vida * 0.07, Partida)
            if self.Efeitos.get("Envenenado", 0) > 0:
                self.Efeitos["Envenenado"] += 2
        elif Partida.clima == "Gravidade Anomala":
            if self.Efeitos.get("Flutuando", 0) > 0 or self.Efeitos.get("Voando", 0) > 0:
                self.TomarDano(self.base_vida * 0.08, Partida)
        if Partida.clima == "Tempestade de Raios":
            if "eletrico" in self.Tipo:
                if self.Efeitos.get("Energizado", 0) > 0:
                    self.Efeitos["Energizado"] += 1
                else:
                    self.Efeitos["Energizado"] = 2

        if self.PodeUsarHabilidade:
            for habilidade in self.Habilidades:
                if habilidade["Ativação"] == "FimTurno":
                    self, Partida = HabDic[str(habilidade["Code"])](self, Partida)
            
        if self.PodeUsarPassivaItem:
            for item in self.Itens:
                if item["Ativação"] == "FimTurno":
                    self, Partida = IteDic[str(item["Code"])](self, Partida)
        
        if self.Efeitos.get("Queimado", 0) > 0:
            dano = int(self.vida * 0.05)
            self.TomarDano(dano, Partida)  # Sem atacante definido
            self.Efeitos["Queimado"] -= 1

        if self.Efeitos.get("Envenenado", 0) > 0:
            dano = int(self.vida * 0.08)
            self.TomarDano(dano, Partida)
            self.Efeitos["Envenenado"] -= 1

        if self.Efeitos.get("Intoxicado", 0) > 0:
            dano = int(self.vida * 0.12)
            self.TomarDano(dano, Partida)
            self.Efeitos["Intoxicado"] -= 1

            # Determina aliados com base no dono
            if self.jogador == Partida.jogador1:
                aliados = Partida.pokemons_jogador1
            else:
                aliados = Partida.pokemons_jogador2

            # Afeta aliados adjacentes
            PokemonsAdjacentes = adjacentes(self, aliados)
            for pokemon in PokemonsAdjacentes:
                dano_aliado = int(pokemon.vida * 0.08)
                pokemon.TomarDano(dano_aliado, Partida)
        
        # --- Regeneração e Abençoado ---
        vida_perdida = self.base_vida - self.vida
        if vida_perdida > 0:
            if self.Efeitos.get("Regeneração", 0) > 0:
                cura = int(vida_perdida * 0.15)
                self.ReceberCura(cura)

            if self.Efeitos.get("Abençoado", 0) > 0:
                cura = int(vida_perdida * 0.05)
                self.ReceberCura(cura)

        pokemon.GanharEnergia()
    
    def Verifica(self, Partida):

        self.var_temp_vida = 0
        self.var_temp_atk = 0
        self.var_temp_def = 0
        self.var_temp_spA = 0
        self.var_temp_spD = 0
        self.var_temp_vel = 0
        self.var_temp_mag = 0
        self.var_temp_per = 0
        self.var_temp_ene = 0
        self.var_temp_enR = 0
        self.var_temp_crD = 0
        self.var_temp_crC = 0

        if Partida.clima == "Nevasca":
            if "gelo" in self.Tipo:
                self.var_temp_def += self.base_def * 0.4
        elif Partida.clima == "Tempestade de Areia":
            if "terrestre" in self.Tipo:
                self.var_temp_vel += self.base_vel * 0.2
        elif Partida.clima == "Nevoa":
            if "fantasma" in self.Tipo:
                self.var_temp_vel += self.base_vel * 0.3
        elif Partida.clima == "Gravidade Anomola":
            if "cosmico" in self.Tipo:
                self.var_temp_vel += self.base_vel * 0.15
                multiplicador = round(self.Peso / 100)
                self.var_temp_def += self.base_def * 0.03 * multiplicador
                self.var_temp_def += self.base_spD * 0.03 * multiplicador
        elif Partida.clima == "Noite Densa":
            if "sombrio" in self.Tipo:
                self.var_temp_vel += self.base_vel * 0.25

            # --- Efeitos de Buff Temporário ---
        if self.Efeitos.get("Fortificado", 0) > 0:
            valor = int((self.base_def + self.var_per_def) * 0.5)
            self.var_temp_def += valor

        if self.Efeitos.get("Reforçado", 0) > 0:
            valor = int((self.base_spD + self.var_per_spD) * 0.5)
            self.var_temp_spD += valor

        if self.Efeitos.get("Amplificado", 0) > 0:
            valor = int((self.base_atk + self.var_per_atk) * 0.5)
            self.var_temp_atk += valor

        if self.Efeitos.get("Aprimorado", 0) > 0:
            valor = int((self.base_spA + self.var_per_spA) * 0.5)
            self.var_temp_spA += valor
        
        if self.Efeitos.get("Encantado", 0) > 0:
            valor = int((self.base_mag + self.var_per_mag) * 0.5)
            self.var_temp_mag += valor

            # --- Efeitos de Debuff Temporário ---
        if self.Efeitos.get("Quebrado", 0) > 0:
            valor = int((self.base_def + self.var_per_def) * 0.5)
            self.var_temp_def -= valor

        if self.Efeitos.get("Fragilizado", 0) > 0:
            valor = int((self.base_spD + self.var_per_spD) * 0.5)
            self.var_temp_spD -= valor

        if self.Efeitos.get("Enfraquecido", 0) > 0:
            valor = int((self.base_atk + self.var_per_atk) * 0.5)
            self.var_temp_atk -= valor

        if self.Efeitos.get("Neutralizado", 0) > 0:
            valor = int((self.base_spA + self.var_per_spA) * 0.5)
            self.var_temp_spA -= valor
        
        if self.Efeitos.get("Enfeitiçado", 0) > 0:
            valor = int((self.base_mag + self.var_per_mag) * 0.5)
            self.var_temp_mag -= valor

        if self.Efeitos.get("Incapacitado", 0) > 0:
            self.PodeUsarHabilidade = False
        
        if self.Efeitos.get("Atordoado", 0) > 0:
            self.PodeUsarPassivaItem = False

        if self.PodeUsarHabilidade:
            for habilidade in self.Habilidades:
                if habilidade["Ativação"] == "Verificação":
                    self = HabDic[str(habilidade["Code"])](self)
            
        if self.PodeUsarPassivaItem:
            for item in self.Itens:
                if item["Ativação"] == "Verificação":
                    self = IteDic[str(item["Code"])](self)
        
        self.atk = self.base_atk + self.var_per_atk + self.var_temp_atk
        self.Def = self.base_def + self.var_per_def + self.var_temp_def
        self.spA = self.base_spA + self.var_per_spA + self.var_temp_spA
        self.spD = self.base_spD + self.var_per_spD + self.var_temp_spD
        self.vel = self.base_vel + self.var_per_vel + self.var_temp_vel
        self.mag = self.base_mag + self.var_per_mag + self.var_temp_mag
        self.per = self.base_per + self.var_per_per + self.var_temp_per
        self.ene = self.base_ene + self.var_per_ene + self.var_temp_ene
        self.enR = self.base_enR + self.var_per_enR + self.var_temp_enR
        self.crD = self.base_crD + self.var_per_crD + self.var_temp_crD
        self.crC = self.base_crC + self.var_per_crC + self.var_temp_crC

    def ToDic(self):
        return {

            # Atributos reais atuais (valor real = base + var_per + var_temp)
            "Vida": self.vida,
            "Atk": self.atk,
            "Defesa": self.defesa,
            "SpA": self.spA,
            "SpD": self.spD,
            "Vel": self.vel,
            "Mag": self.mag,
            "Per": self.per,
            "Ene": self.ene,
            "EnR": self.enR,
            "CrD": self.crD,
            "CrC": self.crC,

            "local": self.local,
            "Energia": self.Energia,
            "Efeitos": list(self.efeitos),  # copiando a lista de status para o dicionário

        }

class Partida:
    def __init__(self, code_jogador1, code_jogador2, pokemons_jogador1, pokemons_jogador2):
        self.jogador1 = code_jogador1
        self.jogador2 = code_jogador2
        self.turno = 0
        self.historico = []
        self.clima = None

        self.StebsP1 = {}
        self.StebsP2 = {}

        self.ArenaP1 = [None,None,None,None,None,None,None,None,None]
        self.ArenaP2 = [None,None,None,None,None,None,None,None,None]

        # Cria instâncias da classe Pokemon
        self.pokemons_jogador1 = [Pokemon(p, dono=code_jogador1) for p in pokemons_jogador1]
        self.pokemons_jogador2 = [Pokemon(p, dono=code_jogador2) for p in pokemons_jogador2]
    
    def ToDic(self):
        return {
            "Turno": self.turno,
            "Clima": self.clima,
            "StebsP1": self.StebsP1,
            "StebsP2": self.StebsP2,
            "ArenaP1": self.ArenaP1,
            "ArenaP2": self.ArenaP2
        }

def adjacentes(pokemon, lista_pokemons):
    # Remove o próprio Pokémon da lista
    lista = [p for p in lista_pokemons if p != pokemon]

    # Mapa de adjacência no tabuleiro 3x3
    adjacencia = {
        1: [2, 4, 5],
        2: [1, 3, 5],
        3: [2, 5, 6],
        4: [1, 5, 7],
        5: [1, 2, 3, 4, 6, 7, 8, 9],
        6: [3, 5, 9],
        7: [4, 5, 8],
        8: [5, 7, 9],
        9: [5, 6, 8]
    }

    local = pokemon.local if isinstance(pokemon.local, int) else int(pokemon.local)
    posicoes_adj = adjacencia.get(local, [])

    # Retorna os pokémons que estão em posições adjacentes
    return [p for p in lista if int(p.local) in posicoes_adj]

def OrdenarJogadasPorVelocidade(sala):
    jogadas_raw = sala["jogada_jogador1"] + sala["jogada_jogador2"]
    jogadas_ordenadas = []

    for jogada in jogadas_raw:
        jogador = jogada["jogador"]
        idx = jogada["agente"]

        if jogador == "jogador1":
            agente = sala["partida"].pokemons_jogador1[idx]
        else:
            agente = sala["partida"].pokemons_jogador2[idx]

        jogada["agente"] = agente
        jogadas_ordenadas.append((agente.vel, jogada))

    # Ordenar por velocidade (maior primeiro)
    jogadas_ordenadas.sort(key=lambda x: x[0], reverse=True)

    # Extrair só as jogadas, já ordenadas
    return [jogada for _, jogada in jogadas_ordenadas]

def AtualizaDados(sala):

    for i, pokemon in enumerate(sala["partida"].pokemons_jogador1):
        dados_atualizados = pokemon.ToDic()
        for chave, valor in dados_atualizados.items():
            sala["pokemons_jogador1"][i][chave] = valor

    for i, pokemon in enumerate(sala["partida"].pokemons_jogador2):
        dados_atualizados = pokemon.ToDic()
        for chave, valor in dados_atualizados.items():
            sala["pokemons_jogador2"][i][chave] = valor
    
    sala["partidaDic"] = sala["partida"].ToDic()

def ExecutePartida(sala):
    partida = Partida(
        code_jogador1=sala["jogador1"],
        code_jogador2=sala["jogador2"],
        pokemons_jogador1=sala["pokemons_jogador1"],
        pokemons_jogador2=sala["pokemons_jogador2"]
    )
    
    sala["partida"] = partida  # Agora a sala tem um objeto real controlando a lógica
    sala["partidaDic"] = None
    sala["log"] = None  # Pode ser usado para log inicial
    sala["status_jogador1"] = "preparando"
    sala["status_jogador2"] = "preparando"
    sala["jogada_jogador1"] = None
    sala["jogada_jogador2"] = None

def ExecuteRodada(sala):
    sala["partida"].turno += 1
    sala["Log"] = []

    if sala["partida"].clima == "Tempestade de Raios":
        raios = [random.randint(1,9),random.randint(1,9)]
        sala["Raios"] = raios

    for pokemon in sala["partida"].pokemons_jogador1 + sala["partida"].pokemons_jogador2:
        
        if pokemon.PodeUsarHabilidade:
            for habilidade in pokemon.Habilidades:
                if habilidade["Ativação"] == "InicioTurno":
                    pokemon, sala["partida"] = HabDic[str(habilidade["Code"])](pokemon, sala["partida"])
            
        if pokemon.PodeUsarPassivaItem:
            for item in pokemon.Itens:
                if item["Ativação"] == "InicioTurno":
                    pokemon, sala["partida"] = IteDic[str(item["Code"])](pokemon, sala["partida"])

    jogadas_em_ordem = OrdenarJogadasPorVelocidade(sala)

    for move in jogadas_em_ordem:
        Log = ExecuteAtaque(move, sala["partida"])
        sala["Log"].append(Log)
        for pokemon in sala["partida"].pokemons_jogador1 + sala["partida"].pokemons_jogador2:
            pokemon.Verifica()

    for pokemon in sala["partida"].pokemons_jogador1 + sala["partida"].pokemons_jogador2:
        pokemon.FimTurno(sala["partida"])
        if sala["partida"].clima == "Tempestade de Raios":
            for raio in raios:
                if pokemon.Local == raio:
                    pokemon.TomarDano(int(pokemon.vida / 2), sala["partida"])

    AtualizaDados(sala)

