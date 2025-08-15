import pygame


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
                        sprite_path = f'data/sprites/player_{direction}_{i}.png'
                    else:
                        sprite_path = f'data/sprites/player_{direction}{i}.png'
                    sprite = pygame.image.load(sprite_path).convert_alpha()
                    self.sprites[direction].append(sprite)
                except pygame.error as e:
                    print(f"Warning: Could not load sprite {sprite_path}: {e}")
                    # create a placeholder if sprite is missing
                    placeholder = pygame.Surface((16, 16))
                    placeholder.fill((255, 0, 255))  # magenta placeholder
                    self.sprites[direction].append(placeholder)
        
        # load box sprites
        self.box_sprites = {}
        try:
            self.box_sprites['open'] = pygame.image.load('data/sprites/box_open.png').convert_alpha()
            self.box_sprites['middle'] = pygame.image.load('data/sprites/box_middle.png').convert_alpha()
            self.box_sprites['closed0'] = pygame.image.load('data/sprites/box_closed0.png').convert_alpha()
            self.box_sprites['closed1'] = pygame.image.load('data/sprites/box_closed1.png').convert_alpha()
        except pygame.error as e:
            print(f"Warning: Could not load box sprites: {e}")
            # create placeholder sprites if missing
            placeholder = pygame.Surface((16, 16))
            placeholder.fill((255, 165, 0))  # orange placeholder
            self.box_sprites['open'] = placeholder
            self.box_sprites['middle'] = placeholder
            self.box_sprites['closed0'] = placeholder
            self.box_sprites['closed1'] = placeholder
        
        # load locker sprites
        self.locker_sprites = {}
        try:
            self.locker_sprites['closed'] = pygame.image.load('data/sprites/locker_closed.png').convert_alpha()
            self.locker_sprites['open'] = pygame.image.load('data/sprites/locker_open.png').convert_alpha()
        except pygame.error as e:
            print(f"Warning: Could not load locker sprites: {e}")
            # create placeholder sprites if missing
            placeholder = pygame.Surface((16, 16))
            placeholder.fill((128, 128, 128))  # gray placeholder
            self.locker_sprites['closed'] = placeholder
            self.locker_sprites['open'] = placeholder
    
    def update(self, dt, dx, dy, is_in_box=False):
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
    
    def get_current_sprite(self, is_in_box=False, is_in_trees=False, is_in_locker=False):
        if is_in_trees:
            # create a transparent sprite when in trees
            transparent_sprite = pygame.Surface((16, 16), pygame.SRCALPHA)
            transparent_sprite.fill((0, 0, 0, 0))  # completely transparent
            return transparent_sprite
        elif is_in_locker:
            # create a transparent sprite when in locker (player is hidden)
            transparent_sprite = pygame.Surface((16, 16), pygame.SRCALPHA)
            transparent_sprite.fill((0, 0, 0, 0))  # completely transparent
            return transparent_sprite
        elif is_in_box:
            # if in box mode, alternate between closed0 and closed1 when moving
            if self.is_moving:
                # alternate between closed0 and closed1
                if self.current_frame_index % 2 == 0:
                    return self.box_sprites['closed0']
                else:
                    return self.box_sprites['closed1']
            else:
                # use closed0 when idle
                return self.box_sprites['closed0']
        else:
            # normal player sprite logic
            if self.is_moving:
                # use animation sequence when moving
                frame_number = self.animation_sequence[self.current_frame_index]
            else:
                # use frame 0 when idle
                frame_number = 0
            
            return self.sprites[self.current_direction][frame_number]
