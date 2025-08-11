import pandas as pd
from AtaquesFunções import AtkDic
from HabilidadesFunções import HabDic
from ItensFunções import IteDic
import random

df_Ataques = pd.read_csv("Ataques.csv")

tabela_tipos = {
    "normal":   {"pedra": 0.5, "fantasma": 0.0, "metal": 0.5},
    "fogo":     {"fogo": 0.5, "agua": 0.5, "planta": 2.0, "gelo": 2.0, "inseto": 2.0, "pedra": 0.5, "dragao": 0.5, "metal": 2.0},
    "agua":     {"fogo": 2.0, "agua": 0.5, "planta": 0.5, "terrestre": 2.0, "dragao": 0.5},
    "eletrico": {"agua": 2.0, "eletrico": 0.5, "planta": 0.5, "terrestre": 0.0, "voador": 2.0, "dragao": 0.5, "sonoro": 2.0, "cosmico": 0.5},
    "planta":   {"fogo": 0.5, "agua": 2.0, "planta": 0.5, "venenoso": 0.5, "terrestre": 2.0, "voador": 0.5, "inseto": 0.5, "pedra": 2.0, "dragao": 0.5, "metal": 0.5},
    "gelo":     {"fogo": 0.5, "agua": 0.5, "planta": 2.0, "terrestre": 2.0, "voador": 2.0, "dragao": 2.0, "metal": 0.5},
    "lutador":  {"normal": 2.0, "gelo": 2.0, "pedra": 2.0, "sombrio": 2.0, "metal": 2.0, "venenoso": 0.5, "voador": 0.5, "psiquico": 0.5, "inseto": 0.5, "fantasma": 0.0, "fada": 0.5},
    "venenoso": {"planta": 2.0, "fada": 2.0, "venenoso": 0.5, "terrestre": 0.5, "pedra": 0.5, "fantasma": 0.5, "metal": 0.0},
    "terrestre":{"fogo": 2.0, "eletrico": 2.0, "venenoso": 2.0, "pedra": 2.0, "metal": 2.0, "planta": 0.5, "inseto": 0.5, "voador": 0.0},
    "voador":   {"eletrico": 0.5, "planta": 2.0, "lutador": 2.0, "inseto": 2.0, "pedra": 0.5, "metal": 0.5},
    "psiquico": {"lutador": 2.0, "venenoso": 2.0, "psiquico": 0.5, "metal": 0.5, "sombrio": 0.0},
    "inseto":   {"planta": 2.0, "psiquico": 2.0, "sombrio": 2.0, "fogo": 0.5, "lutador": 0.5, "venenoso": 0.5, "voador": 0.5, "fantasma": 0.5, "metal": 0.5, "fada": 0.5},
    "pedra":    {"fogo": 2.0, "gelo": 2.0, "voador": 2.0, "inseto": 2.0, "lutador": 0.5, "terrestre": 0.5, "metal": 0.5},
    "fantasma": {"fantasma": 2.0, "psiquico": 2.0, "normal": 0.0, "sombrio": 0.5, "sonoro": 0.5},
    "dragao":   {"dragao": 2.0, "metal": 0.5, "fada": 0.0},
    "sombrio":  {"psiquico": 2.0, "fantasma": 2.0, "lutador": 0.5, "sombrio": 0.5, "fada": 0.5, "cosmico": 2.0},
    "metal":    {"gelo": 2.0, "pedra": 2.0, "fada": 2.0, "fogo": 0.5, "agua": 0.5, "eletrico": 0.5, "metal": 0.5},
    "fada":     {"lutador": 2.0, "dragao": 2.0, "sombrio": 2.0, "fogo": 0.5, "venenoso": 0.5, "metal": 0.5},
    "sonoro":   {"inseto": 2.0, "gelo": 2.0, "planta": 0.5, "pedra": 0.5, "metal": 0.5},
    "cosmico":  {"psiquico": 2.0, "sonoro": 2.0, "agua": 2.0, "comico": 0.0, "fantasma": 0.5}
}

def AplicarFraquezaResistencia(tipos_ataque, tipos_defensor):
    multiplicador = 1.0

    for tipo_atk in tipos_ataque:
        for tipo_def in tipos_defensor:
            mult = tabela_tipos.get(tipo_atk, {}).get(tipo_def, 1.0)
            multiplicador *= mult

    return multiplicador

def ExecuteAtaque(Move, Partida):

    # --- Inicialização dos parâmetros principais ---
    Atacante = Move["agente"]
    Alvos = Move["alvo"]
    codigo_ataque = Move["ataque"]

    Log = {"Agente": Atacante, "Code Ataque": codigo_ataque}

    # --- Identificação de lado e times ---
    if Atacante in Partida.pokemons_jogador1:
        aliados = Partida.pokemons_jogador1
        inimigos = Partida.pokemons_jogador2
        player = 1
    elif Atacante in Partida.pokemons_jogador2:
        aliados = Partida.pokemons_jogador2
        inimigos = Partida.pokemons_jogador1
        player = 2
    else:
        aliados, inimigos, player = [], [], 0

    # ================================
    # 🔄 TROCA
    # ================================
    if codigo_ataque == "Troca":
        # Passivas ao sair
        if Atacante.PodeUsarPassivaItem:
            for item in Atacante.Itens:
                if item["Ativação"] == "AoTrocar":
                    Atacante = IteDic[str(item["Code"])](Atacante)
        if Atacante.PodeUsarHabilidade:
            for habilidade in Atacante.Habilidade:
                if habilidade["Ativação"] == "AoTrocar":
                    Atacante = HabDic[str(habilidade["Code"])](Atacante)

        # Troca em si
        Alvo = aliados[Alvos]
        Atacante.Ativo = False
        Alvo.Ativo = True
        Alvo.Local = Atacante.Local
        Atacante.Local = None

        # Passivas ao entrar
        if Alvo.PodeUsarPassivaItem:
            for item in Alvo.Itens:
                if item["Ativação"] == "AoEntrar":
                    Alvo, Atacante = IteDic[str(item["Code"])](Alvo, Atacante)
        if Alvo.PodeUsarHabilidade:
            for habilidade in Alvo.Habilidades:
                if habilidade["Ativação"] == "AoEntrar":
                    Alvo, Atacante = HabDic[str(habilidade["Code"])](Alvo, Atacante)

        Log["Troca"] = Alvos
        return Log

    # ================================
    # ❌ CANCELAMENTO (Pokémon morto)
    # ================================
    if not Atacante.vivo:
        Log["Morreu"] = True
        return

    # ================================
    # 🚶 MOVIMENTAÇÃO
    # ================================
    if codigo_ataque == "Mover":
        Atacante.Mover(Alvos, False)
        Log["Mover"] = Alvos
        return Log

    # ================================
    # 📦 LEITURA DOS DADOS DO ATAQUE
    # ================================
    Recuo = getattr(Atacante, "Recuo", False)
    ataque_df = df_Ataques[df_Ataques["Code"] == codigo_ataque]
    if ataque_df.empty:
        return

    ataque = ataque_df.iloc[0].to_dict()

    # ================================
    # ⚙️ Funções Irregulares (Pré-execução)
    # ================================
    if ataque["função"] in ["i", "im", "if", "imf"]:
        Recuo = AtkDic[str(codigo_ataque) + "i"](Atacante, Alvos, ataque, Partida, Log, Recuo)

    # ================================
    # 🎒 Ativação de Habilidades e Itens (Pré-Ataque)
    # ================================
    for item in Atacante.Items:
        if item["Ativação"] == "InicioAtaque" and Atacante.PodeUsarPassivaItem:
            Recuo = IteDic[str(item["Code"])](Atacante, Alvos, ataque, Partida, Log, Recuo)

    for habilidade in Atacante.Habilidades:
        if habilidade["Ativação"] == "InicioAtaque" and Atacante.PodeUsarHabilidade:
            Recuo = HabDic[str(habilidade["Code"])](Atacante, Alvos, ataque, Partida, Log, Recuo)

    if Atacante.Efeitos.get("Imparavel", 0) > 0:
        Recuo = False
    Log["Recuo"] = Recuo
    if Recuo:
        return Log

    # ================================
    # 🔋 Custo de energia
    # ================================
    custo_energia = ataque["Custo"]
    if Atacante.Efeitos.get("Encharcado", 0) > 0:
        Atacante.Energia -= custo_energia * 1.25
    else:
        Atacante.Energia -= custo_energia

    # ================================
    # 🔁 STEB (Sinergia por tipo)
    # ================================
    tipo = ataque["Tipo"]
    StebUsado = 0
    if player == 1 and len(Partida.StebP1) < 7:
        Partida.StebP1[tipo] += Atacante.Sinergia
        StebUsado = Partida.StebP1[tipo]
    elif player == 2 and len(Partida.StebP2) < 7:
        Partida.StebP2[tipo] += Atacante.Sinergia
        StebUsado = Partida.StebP2[tipo]

    # ================================
    # 🎯 Identificação de Alvos
    # ================================
    Alvos = [Alvos] if not isinstance(Alvos, list) else Alvos
    AlvosAliados, AlvosInimigos = [], []

    for alvo in Alvos:
        if len(alvo) < 2:
            continue
        campo, pos = alvo[0], alvo[1:]
        if campo == "A":
            AlvosAliados += [a for a in aliados if str(a.local) == pos]
        elif campo == "B":
            AlvosInimigos += [i for i in inimigos if str(i.local) == pos]

    Log.update({
        "Alvos Aliados": AlvosAliados,
        "Alvos Inimigos": AlvosInimigos,
        "Tipo": tipo,
        "Estilo": ataque["Estilo"],
        "Assertividade": ataque["Assertividade"]
    })

    poder_ataque = Atacante.atk if ataque["Estilo"] == "n" else (
                   Atacante.spA if ataque["Estilo"] == "e" else 0)

    # ================================
    # 💥 Função especial direta de ataque (estilo especial)
    # ================================
    if ataque["Estilo"] not in ["n", "e"]:
        AtkDic[str(codigo_ataque) + "s"](Atacante, AlvosInimigos, AlvosAliados, ataque, Partida, Log, Acertou)

    Log["SubLogs"] = []

    # ================================
    # 🧮 Processamento por Alvo
    # ================================
    for Alvo in AlvosInimigos:
        SubLog = {"Alvo": Alvo}
        Log["SubLogs"].append(SubLog)

        # Modificadores de assertividade
        assertividade = ataque["Assertividade"]
        if isinstance(assertividade, str):
            assertividade = int(assertividade.replace('%', ''))

        if Atacante.Efeitos.get("Cofuso", 0): assertividade *= 0.5
        if Alvo.Efeitos.get("Voando", 0): assertividade *= 0.5
        if Alvo.Efeitos.get("Flutuando", 0): assertividade *= 0.75
        if "sombrio" not in Atacante.Tipo:
            if Partida.clima == "Noite Densa": assertividade *= 0.75

        Acertou = random.randint(1, 100) <= assertividade
        Protegido = getattr(Alvo, "Protegido", False)

        # Crítico
        chance_critico = getattr(Atacante, "crC", 0)
        bonus_critico = getattr(Atacante, "crD", 0)
        critico = random.randint(1, 100) <= chance_critico

        # Defesa
        defesa_alvo = Alvo.defesa if ataque["Estilo"] == "n" else Alvo.spD

        # ================================
        # ⚙️ Função irregular do meio
        # ================================
        if ataque["função"] in ["m", "im", "mf", "imf"]:
            resultado = AtkDic[str(codigo_ataque) + "m"](
                Atacante, Alvo, AlvosAliados, ataque, Partida,
                poder_ataque, defesa_alvo, ataque["Dano"],
                critico, bonus_critico, Acertou, Protegido
            )
            if resultado:
                poder_ataque, defesa_alvo, critico, bonus_critico, Acertou, Protegido = resultado

        # ================================
        # 🧠 Ativação de habilidades e itens no meio da execução
        # ================================
        Grupos = []
        if Atacante.PodeUsarPassivaItem: Grupos.append(("item", Atacante.Itens))
        if Atacante.PodeUsarHabilidade: Grupos.append(("hab", Atacante.Habilidades))
        if Alvo.PodeUsarPassivaItem: Grupos.append(("item", Alvo.Itens))
        if Alvo.PodeUsarHabilidade: Grupos.append(("hab", Alvo.Habilidades))

        for grupo in Grupos:
            for efeito in grupo:
                ativacao = efeito["Ativação"]
                if ativacao in ["MeioAtaque", "DefesaInicio"]:
                    dic = IteDic if "item" in ativacao else HabDic
                    func = dic[str(efeito["Code"])]
                    resultado = func(Atacante, Alvos, ataque, Partida, Log,
                                     poder_ataque, defesa_alvo,
                                     critico, Acertou, bonus_critico, Protegido)
                    poder_ataque, defesa_alvo, critico, Acertou, bonus_critico, Protegido = resultado

        # ================================
        # 💥 Cálculo de dano final
        # ================================
        perfuracao = getattr(Atacante, "per", 0)
        defesa_efetiva = max(0, defesa_alvo - perfuracao)
        dano_bruto = poder_ataque * ataque["Dano"]
        dano_refinado = dano_bruto * (100 / (100 + defesa_efetiva))
        dano_semifinal = dano_refinado * (1 + bonus_critico / 100) if critico else dano_refinado

        MultiplicadorTipo = AplicarFraquezaResistencia(tipo, Alvo.Tipo)
        MultiplicadorSteb = 1 + (0.05 + StebUsado / 100) if tipo in Atacante.Tipo else 1
        dano_final = max(0, int(dano_semifinal * MultiplicadorTipo * MultiplicadorSteb))

        # ================================
        # 🧠 Execução de fim (função, habilidade, item)
        # ================================
        if ataque["função"] in ["f", "mf", "if", "imf"]:
            resultado = AtkDic[str(codigo_ataque) + "f"](Atacante, Alvo, AlvosAliados, ataque, Partida, Log, dano_final)
            if resultado: dano_final = resultado

        for grupo in Grupos:
            for efeito in grupo:
                ativacao = efeito["Ativação"]
                if ativacao in ["FimAtaque", "FimDefesa"]:
                    dic = IteDic if "item" in ativacao else HabDic
                    func = dic[str(efeito["Code"])]
                    dano_final = func(Atacante, Alvos, ataque, Partida, Log, dano_final)

        # ================================
        # 🩸 Aplicação do dano
        # ================================
        if Acertou and not Protegido:
            Alvo.TomarDano(dano_final, Partida, Atacante)

        SubLog.update({
            "Protegido": Protegido,
            "Critico": critico,
            "AumentoCritico": bonus_critico,
            "Defesa": defesa_alvo,
            "Perfuração": perfuracao,
            "Defesa Efetiva": defesa_efetiva,
            "Efetividade": MultiplicadorTipo,
            "Steb": StebUsado,
            "Multiplicador": MultiplicadorTipo * MultiplicadorSteb,
            "Dano Bruto": dano_bruto,
            "Dano Refinado": dano_refinado,
            "Dano SemiFinal": dano_semifinal,
            "Dano Final": dano_final
        })

    DanoTotal = 0
    for sub in Log["SubLogs"]:
        DanoTotal += sub["Dano Final"]
    Log["DanoTotal"] = DanoTotal

    return Log
