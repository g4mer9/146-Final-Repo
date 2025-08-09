import pygame

speed = 500
radius = 20

def player_move(player_pos, dt):
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_pos.x -= speed * dt
    if keys[pygame.K_RIGHT]:
        player_pos.x += speed * dt
    if keys[pygame.K_UP]:
        player_pos.y -= speed * dt
    if keys[pygame.K_DOWN]:
        player_pos.y += speed * dt

def quit_check(running):
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        running = False
    return running