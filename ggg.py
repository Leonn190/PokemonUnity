import pygame, math

pygame.init()
tela = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Jogador
player_pos = pygame.Vector2(200, 300)
player_vel = pygame.Vector2(0, 0)
speed = 5

# Obstáculo circular
obst_pos = pygame.Vector2(400, 300)
obst_radius = 60

def aplicar_colisao(player_pos, player_vel, obst_pos, obst_radius):
    dist = player_pos.distance_to(obst_pos)
    
    if dist < obst_radius * 1.5:  # dentro da zona de colisão expandida
        # Direção do empurrão (normalizada)
        direcao = (player_pos - obst_pos).normalize()
        
        # Profundidade relativa (0 fora, 1 no centro)
        intensidade = 1 - (dist / (obst_radius * 1.5))
        
        # Reduz velocidade proporcionalmente
        player_vel *= (1 - intensidade * 0.7)
        
        # Aplica empurrão para fora
        player_vel += direcao * intensidade * 2

    return player_vel

rodando = True
while rodando:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False

    # Movimento básico com teclado
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]: player_vel.y -= 0.3
    if keys[pygame.K_s]: player_vel.y += 0.3
    if keys[pygame.K_a]: player_vel.x -= 0.3
    if keys[pygame.K_d]: player_vel.x += 0.3

    # Aplica colisão
    player_vel = aplicar_colisao(player_pos, player_vel, obst_pos, obst_radius)

    # Atualiza posição
    player_pos += player_vel
    player_vel *= 0.9  # atrito natural

    # Desenho
    tela.fill((30, 30, 30))
    pygame.draw.circle(tela, (100, 0, 0), obst_pos, int(obst_radius * 1.5), 1)
    pygame.draw.circle(tela, (200, 0, 0), obst_pos, obst_radius)
    pygame.draw.circle(tela, (0, 200, 200), player_pos, 15)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()