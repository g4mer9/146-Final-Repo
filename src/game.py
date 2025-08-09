import pygame
import player
import tiles

# INITIALIZATIONS ====================================================================================================================================

pygame.init()
# screen dimensions
flags = pygame.SCALED | pygame.FULLSCREEN
screen = pygame.display.set_mode((848, 480), flags)
clock = pygame.time.Clock()
running = True

# delta time, used for frame-rate independent physics
dt = 0

# player spawn in middle of screen on startup
player_pos = pygame.Vector2(screen.get_width() // 2, screen.get_height() // 2)

sprite_group = pygame.sprite.Group()

tmx_data, sprite_group = tiles.load_tileset('./data/tmx/untitled.tmx', 16)

# tiles.debug_tileset(tmx_data)

# MAIN LOOP =========================================================================================================================================

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # wipe previous frame
    screen.fill((0, 0, 0))

    #draw background
    sprite_group.draw(screen)
    tiles.draw_background(screen, tmx_data)

    # draw player at current player_pos
    pygame.draw.circle(screen, (255, 0, 0), player_pos, player.radius)

    # quit game check
    running = player.quit_check(running)
    # move player based on input
    player.player_move(player_pos, dt)

    # draw new frame
    pygame.display.flip()

    # FPS cap, also updates delta time for physics
    dt = clock.tick(60) / 1000

pygame.quit()