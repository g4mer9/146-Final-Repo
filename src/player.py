import pygame

speed = 100

class Player(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__()
        self.animator = PlayerAnimator()
        self.image = self.animator.get_current_sprite()
        self.rect = self.image.get_rect(center=position)
        self.position = pygame.Vector2(position)  # use float position for smooth movement
        self.moveable = True  # flag to check if player can move
        self.box = False  # flag to check if player is in a box
        self.speed_modifier = 1.0  # speed modifier for different terrain types
        
        # box animation variables
        self.box_animation_active = False
        self.box_animation_timer = 0.0
        self.box_animation_stage = 0  # 0: box_open, 1: box_middle, 2: box_closed0
        self.box_animation_speed = 0.3  # time for each stage in seconds
        
    def update(self, dt, collision_rects):
        # handle box animation if active
        if self.box_animation_active:
            self.box_animation_timer += dt
            if self.box_animation_timer >= self.box_animation_speed:
                self.box_animation_timer = 0.0
                self.box_animation_stage += 1
                
                if self.box_animation_stage == 1:
                    # stage 1: box_middle
                    self.image = self.animator.box_sprites['middle']
                elif self.box_animation_stage == 2:
                    # stage 2: box_closed0
                    self.image = self.animator.box_sprites['closed0']
                elif self.box_animation_stage >= 3:
                    # animation finished
                    self.box_animation_active = False
                    self.moveable = True
            return 0, 0  # no movement during animation
        
        # handle input and movement
        dx, dy = self.handle_input(dt, collision_rects)
        
        # update animation (always update for timing, regardless of box state)
        self.animator.update(dt, dx, dy, self.box)
        
        # get the appropriate sprite based on current state
        if not self.box_animation_active:
            self.image = self.animator.get_current_sprite(self.box)
        
        return dx, dy
    
    def set_speed_modifier(self, modifier):
        """Set the speed modifier for different terrain types"""
        self.speed_modifier = modifier
    
    def handle_input(self, dt, collision_rects):
        
        keys = pygame.key.get_pressed()
        
        # store original position
        original_x = self.position.x
        original_y = self.position.y
        
        # calculate movement deltas
        dx = 0
        dy = 0
        
        # apply speed modifier for terrain effects
        current_speed = speed * self.speed_modifier
        
        if keys[pygame.K_LEFT]:
            dx -= current_speed * dt
        if keys[pygame.K_RIGHT]:
            dx += current_speed * dt
        if keys[pygame.K_UP]:
            dy -= current_speed * dt
        if keys[pygame.K_DOWN]:
            dy += current_speed * dt
        
        # check for Z key press to exit box mode
        if keys[pygame.K_z]:
            self.box = False
        
        # handle collisions and update position
        self.handle_collisions(dx, dy, collision_rects)
        
        # update rect position (for rendering)
        self.rect.center = (int(self.position.x), int(self.position.y))
        
        # return the actual movement that occurred
        actual_dx = self.position.x - original_x
        actual_dy = self.position.y - original_y
        if(not self.moveable):
            return 0, 0
        return actual_dx, actual_dy
    
    def handle_collisions(self, dx, dy, collision_rects):
        player_size = (16, 16)
        
        # handle horizontal movement first
        if dx != 0:
            self.position.x += dx
            player_rect = pygame.Rect(self.position.x - player_size[0]//2, 
                                    self.position.y - player_size[1]//2, 
                                    player_size[0], player_size[1])
            
            # check for horizontal collisions and find the closest valid position
            collision_found = False
            closest_x = self.position.x
            
            for rect in collision_rects:
                if player_rect.colliderect(rect):
                    collision_found = True
                    if dx > 0:  # moving right
                        closest_x = min(closest_x, rect.left - player_size[0]//2)
                    else:  # moving left
                        closest_x = max(closest_x, rect.right + player_size[0]//2)
            
            if collision_found:
                self.position.x = closest_x
        
        # handle vertical movement second
        if dy != 0:
            self.position.y += dy
            player_rect = pygame.Rect(self.position.x - player_size[0]//2, 
                                    self.position.y - player_size[1]//2, 
                                    player_size[0], player_size[1])
            
            # check for vertical collisions and find the closest valid position
            collision_found = False
            closest_y = self.position.y
            
            for rect in collision_rects:
                if player_rect.colliderect(rect):
                    collision_found = True
                    if dy > 0:  # moving down
                        closest_y = min(closest_y, rect.top - player_size[1]//2)
                    else:  # moving up
                        closest_y = max(closest_y, rect.bottom + player_size[1]//2)
            
            if collision_found:
                self.position.y = closest_y

    def enter_box(self):
        """Handle player entering a box with animation sequence"""
        if not self.box:  # only enter if not already in a box
            self.box = True
            self.moveable = False
            self.box_animation_active = True
            self.box_animation_timer = 0.0
            self.box_animation_stage = 0
            # start with box_open sprite
            self.image = self.animator.box_sprites['open']
    
    def exit_box(self):
        """Handle player exiting the box state"""
        self.box = False
        # sprite will automatically switch back to normal player sprite
        # through the animator's get_current_sprite method

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
    
    def get_current_sprite(self, is_in_box=False):
        if is_in_box:
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

def quit_check(running):
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        running = False
    return running