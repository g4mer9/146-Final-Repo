import pygame

speed = 100


def player_move(player_pos, dt, collision_rects, player_size=(16, 16)):
    keys = pygame.key.get_pressed()
    
    # store original position
    original_x = player_pos.x
    original_y = player_pos.y
    
    # calculate movement deltas
    dx = 0
    dy = 0
    
    if keys[pygame.K_LEFT]:
        dx -= speed * dt
    if keys[pygame.K_RIGHT]:
        dx += speed * dt
    if keys[pygame.K_UP]:
        dy -= speed * dt
    if keys[pygame.K_DOWN]:
        dy += speed * dt
    
    # handle horizontal movement first
    if dx != 0:
        player_pos.x += dx
        player_rect = pygame.Rect(player_pos.x, player_pos.y, player_size[0], player_size[1])
        
        # check for horizontal collisions and find the closest valid position
        collision_found = False
        closest_x = player_pos.x
        
        for rect in collision_rects:
            if player_rect.colliderect(rect):
                collision_found = True
                if dx > 0:  # moving right
                    closest_x = min(closest_x, rect.left - player_size[0])
                else:  # moving left
                    closest_x = max(closest_x, rect.right)
        
        if collision_found:
            player_pos.x = closest_x
    
    # handle vertical movement second
    if dy != 0:
        player_pos.y += dy
        player_rect = pygame.Rect(player_pos.x, player_pos.y, player_size[0], player_size[1])
        
        # check for vertical collisions and find the closest valid position
        collision_found = False
        closest_y = player_pos.y
        
        for rect in collision_rects:
            if player_rect.colliderect(rect):
                collision_found = True
                if dy > 0:  # moving down
                    closest_y = min(closest_y, rect.top - player_size[1])
                else:  # moving up
                    closest_y = max(closest_y, rect.bottom)
        
        if collision_found:
            player_pos.y = closest_y

def quit_check(running):
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        running = False
    return running