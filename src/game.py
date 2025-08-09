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

# initialize player animator
player_animator = player.PlayerAnimator()

sprite_group = pygame.sprite.Group()

tmx_data, sprite_group, collision_rects = tiles.load_tileset('./data/tmx/untitled.tmx', 16)

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
    tiles.draw_objs(screen, tmx_data)

    # quit game check
    running = player.quit_check(running)
    
    # move player based on input and get movement deltas
    dx, dy = player.player_move(player_pos, dt, collision_rects)
    
    # update player animation
    player_animator.update(dt, dx, dy)
    
    #draw player with current animated sprite
    current_sprite = player_animator.get_current_sprite()
    screen.blit(current_sprite, player_pos)

    # draw new frame
    pygame.display.flip()

    # FPS cap, also updates delta time for physics
    dt = clock.tick(60) / 1000

pygame.quit()