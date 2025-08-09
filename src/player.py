import pygame

speed = 100

class PlayerAnimator:
    def __init__(self):
        self.current_direction = "down"
        self.is_moving = False
        self.animation_timer = 0.0
        self.animation_speed = 0.15  # time between frames in seconds
        self.current_frame_index = 0
        # animation sequence: 0, 1, 0, 2, 0, 1, 0, 2...
        self.animation_sequence = [0, 1, 0, 2]
        
        # load all sprite images
        self.sprites = {}
        directions = ["down", "up", "left", "right"]
        for direction in directions:
            self.sprites[direction] = []
            for i in range(3):
                try:
                    if direction == "up" and i == 1:
                        # handle the special case of player_up_1.png
                        sprite_path = f'./data/sprites/player_{direction}_{i}.png'
                    else:
                        sprite_path = f'./data/sprites/player_{direction}{i}.png'
                    sprite = pygame.image.load(sprite_path).convert_alpha()
                    self.sprites[direction].append(sprite)
                except pygame.error as e:
                    print(f"Warning: Could not load sprite {sprite_path}: {e}")
                    # create a placeholder if sprite is missing
                    placeholder = pygame.Surface((16, 16))
                    placeholder.fill((255, 0, 255))  # magenta placeholder
                    self.sprites[direction].append(placeholder)
    
    def update(self, dt, dx, dy):
        # determine if player is moving
        self.is_moving = dx != 0 or dy != 0
        
        # update direction based on movement (prioritize vertical movement)
        if dy > 0:
            self.current_direction = "down"
        elif dy < 0:
            self.current_direction = "up"
        elif dx > 0:
            self.current_direction = "right"
        elif dx < 0:
            self.current_direction = "left"
        
        # update animation only if moving
        if self.is_moving:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0.0
                self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_sequence)
    
    def get_current_sprite(self):
        if self.is_moving:
            # use animation sequence when moving
            frame_number = self.animation_sequence[self.current_frame_index]
        else:
            # use frame 0 when idle
            frame_number = 0
        
        return self.sprites[self.current_direction][frame_number]

def handle_collisions(dx, dy, player_pos, player_size, collision_rects):
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

    return player_pos

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
    
    player_pos = handle_collisions(dx, dy, player_pos, player_size, collision_rects)
    
    # return the actual movement that occurred
    actual_dx = player_pos.x - original_x
    actual_dy = player_pos.y - original_y
    return actual_dx, actual_dy

def quit_check(running):
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        running = False
    return running