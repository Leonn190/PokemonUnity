import pygame
import sys

pygame.init()
LARGURA, ALTURA = 800, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
clock = pygame.time.Clock()

# Fonte
fonte = pygame.font.SysFont("arial", 24)

# Estado global dos botões
estado_global = {}

# Câmera
zoom = 1.0
offset_x, offset_y = 0, 0
arrastando = False
ultimo_mouse = (0, 0)

# Mundo (maior que a tela)
world_w, world_h = 1600, 1200
fundo = pygame.Surface((world_w, world_h))
fundo.fill((50, 50, 70))  # fundo básico

# Criar alguns botões de teste (em coords do mundo)
botoes = [
    {"texto": "Botão 1", "rect": pygame.Rect(200, 200, 200, 80)},
    {"texto": "Botão 2", "rect": pygame.Rect(600, 400, 200, 80)},
    {"texto": "Botão 3", "rect": pygame.Rect(1000, 800, 200, 80)},
]

# ---- SUA FUNÇÃO BOTÃO ----
def Botao_Selecao(
    tela, texto, espaço, Fonte,
    cor_fundo, cor_borda_normal,
    cor_borda_esquerda=None, cor_borda_direita=None,
    cor_passagem=None, id_botao=None,
    estado_global=None, eventos=None,
    funcao_esquerdo=None, funcao_direito=None,
    desfazer_esquerdo=None, desfazer_direito=None,
    tecla_esquerda=None, tecla_direita=None,
    grossura=5, som=None,
    branco=False
):
    x, y, largura, altura = espaço
    mouse = pygame.mouse.get_pos()
    clique = pygame.mouse.get_pressed()
    mouse_sobre = x <= mouse[0] <= x + largura and y <= mouse[1] <= y + altura

    if "selecionado_esquerdo" not in estado_global:
        estado_global["selecionado_esquerdo"] = None
    if "selecionado_direito" not in estado_global:
        estado_global["selecionado_direito"] = None

    modo_selecionado = None
    if estado_global["selecionado_esquerdo"] == id_botao:
        modo_selecionado = "esquerdo"
    elif estado_global["selecionado_direito"] == id_botao:
        modo_selecionado = "direito"

    cor_borda_atual = cor_borda_normal
    if modo_selecionado == "esquerdo" and cor_borda_esquerda:
        cor_borda_atual = cor_borda_esquerda
    elif modo_selecionado == "direito" and cor_borda_direita:
        cor_borda_atual = cor_borda_direita
    elif mouse_sobre and cor_passagem:
        cor_borda_atual = cor_passagem

    # fundo
    if cor_fundo is not None:
        pygame.draw.rect(tela, cor_fundo, (x, y, largura, altura))
    pygame.draw.rect(tela, cor_borda_atual, (x, y, largura, altura), grossura)

    cor_texto = (255, 255, 255) if branco else (0, 0, 0)
    texto_render = Fonte.render(texto, True, cor_texto)
    texto_rect = texto_render.get_rect(center=(x + largura // 2, y + altura // 2))
    tela.blit(texto_render, texto_rect)

    clicou = False
    if eventos:
        for evento in eventos:
            if evento.type == pygame.MOUSEBUTTONDOWN and mouse_sobre:
                if evento.button == 1:  # esquerdo
                    clicou = True
                elif evento.button == 3:  # direito
                    clicou = True
    return mouse_sobre, clicou


# ---- LOOP PRINCIPAL ----
while True:
    eventos = pygame.event.get()
    for evento in eventos:
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Scroll para zoom
        if evento.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            old_zoom = zoom
            zoom *= 1.1 if evento.y > 0 else 0.9
            zoom = max(0.5, min(zoom, 3))

            offset_x = mx - (mx - offset_x) * (zoom / old_zoom)
            offset_y = my - (my - offset_y) * (zoom / old_zoom)

        # Drag com botão direito
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 3:
            arrastando = True
            ultimo_mouse = pygame.mouse.get_pos()

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 3:
            arrastando = False

        if evento.type == pygame.MOUSEMOTION and arrastando:
            mx, my = evento.pos
            dx, dy = mx - ultimo_mouse[0], my - ultimo_mouse[1]
            offset_x += dx
            offset_y += dy
            ultimo_mouse = (mx, my)

    # ---- DESENHO ----
    tela.fill((0, 0, 0))

    # fundo (sempre cobrindo tudo)
    scaled_fundo = pygame.transform.smoothscale(fundo, (int(world_w * zoom), int(world_h * zoom)))
    tela.blit(scaled_fundo, (offset_x, offset_y))

    # desenhar botões (ajustar pela câmera!)
    mouse_sobre_algum = False
    for i, b in enumerate(botoes):
        world_rect = b["rect"]

        # converter coord do mundo -> tela
        x = int(world_rect.x * zoom + offset_x)
        y = int(world_rect.y * zoom + offset_y)
        w = int(world_rect.width * zoom)
        h = int(world_rect.height * zoom)

        sobre, clicou = Botao_Selecao(
            tela, b["texto"], (x, y, w, h), fonte,
            (200, 200, 200), (0, 0, 0),
            cor_borda_esquerda=(0, 200, 0),
            cor_borda_direita=(200, 0, 0),
            cor_passagem=(100, 100, 255),
            id_botao=i, estado_global=estado_global, eventos=eventos
        )
        if sobre:
            mouse_sobre_algum = True

    # Se mouse está sobre botão, não arrasta câmera
    if mouse_sobre_algum and pygame.mouse.get_pressed()[2]:
        arrastando = False

    pygame.display.flip()
    clock.tick(60)
