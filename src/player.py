import pygame
from bottle import BottleProjectile

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
        self.trees = False  # flag to check if player is in trees
        self.bottle = False  # flag to check if player has a bottle
        self.book = False  # flag to check if player has a book
        self.speed_modifier = 1.0  # speed modifier for different terrain types
        
        # for tracking key presses
        self.z_key_pressed_last_frame = False
        
        # box animation variables
        self.box_animation_active = False
        self.box_animation_timer = 0.0
        self.box_animation_stage = 0  # 0: box_open, 1: box_middle, 2: box_closed0
        self.box_animation_speed = 0.3  # time for each stage in seconds
        
    def update(self, dt, collision_rects, overlapping_trees=False):
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
            return 0, 0, None, None, None  # no movement during animation, no bottle thrown, no book dropped, no box dropped
        
        # handle input and movement
        dx, dy, thrown_bottle, dropped_book_pos, dropped_box_pos = self.handle_input(dt, collision_rects, overlapping_trees)
        
        # update animation (always update for timing, regardless of box/trees state)
        self.animator.update(dt, dx, dy, self.box)
        
        # get the appropriate sprite based on current state
        if not self.box_animation_active:
            self.image = self.animator.get_current_sprite(self.box, self.trees)
        
        return dx, dy, thrown_bottle, dropped_book_pos, dropped_box_pos
    
    def set_speed_modifier(self, modifier):
        """Set the speed modifier for different terrain types"""
        self.speed_modifier = modifier
    
    def handle_input(self, dt, collision_rects, overlapping_trees=False):
        
        keys = pygame.key.get_pressed()
        z_key_pressed_this_frame = keys[pygame.K_z]
        z_key_just_pressed = z_key_pressed_this_frame and not self.z_key_pressed_last_frame
        
        thrown_bottle = None
        dropped_book_pos = None
        dropped_box_pos = None
        
        # handle Z key for box, trees, bottle, and book interaction
        if z_key_just_pressed:  # only trigger on initial press, not hold
            if overlapping_trees and not self.trees:
                # enter trees when Z is pressed and overlapping trees
                self.enter_trees()
            elif self.box:
                dropped_box_pos = self.exit_box(collision_rects)
            elif self.book:
                dropped_book_pos = self.drop_book(collision_rects)
            elif self.bottle:
                thrown_bottle = self.throw_bottle()
            
        
        # handle Z key hold for trees
        if z_key_pressed_this_frame:
            if overlapping_trees and not self.trees and not self.box:
                self.enter_trees()
        else:
            # exit trees when Z key is released
            if self.trees:
                self.exit_trees()
        
        # update key state for next frame
        self.z_key_pressed_last_frame = z_key_pressed_this_frame
        
        # if player is not moveable, don't process movement input
        if not self.moveable:
            return 0, 0, None, dropped_book_pos, dropped_box_pos
        
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
        
        # handle collisions and update position
        self.handle_collisions(dx, dy, collision_rects)
        
        # update rect position (for rendering)
        self.rect.center = (int(self.position.x), int(self.position.y))
        
        # return the actual movement that occurred and any thrown bottle
        actual_dx = self.position.x - original_x
        actual_dy = self.position.y - original_y
        return actual_dx, actual_dy, thrown_bottle, dropped_book_pos, dropped_box_pos
    
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

    def throw_bottle(self):
        """Throw a bottle in the direction the player is facing"""
        if self.bottle:
            self.bottle = False
            # create a bottle projectile
            bottle_projectile = BottleProjectile(
                start_pos=self.position.copy(),
                direction=self.animator.current_direction
            )
            return bottle_projectile
        return None

    def _get_drop_position_if_clear(self, collision_rects, enemy_group=None, item_name="item"):
        """Helper function to calculate drop position and check for collisions"""
        # calculate position one tile in front of player based on current direction
        drop_x, drop_y = self.position.x, self.position.y
        if self.animator.current_direction == "up":
            drop_y -= 32
        elif self.animator.current_direction == "down":
            drop_y += 16
        elif self.animator.current_direction == "left":
            drop_x -= 32
        elif self.animator.current_direction == "right":
            drop_x += 16
        
        # create a rect for the item at the drop position (assuming 16x16 item size)
        item_rect = pygame.Rect(drop_x - 8, drop_y - 8, 16, 16)
        
        # check for collisions with walls/objects
        collision_found = False
        for collision_rect in collision_rects:
            if item_rect.colliderect(collision_rect):
                collision_found = True
                break
        
        # check for collisions with enemies if enemy_group is provided
        if not collision_found and enemy_group:
            for enemy in enemy_group:
                if item_rect.colliderect(enemy.rect):
                    collision_found = True
                    break
        
        # return position if clear, None if blocked
        if not collision_found:
            return (drop_x, drop_y)
        else:
            print(f"Cannot drop {item_name} here - position is blocked!")
            return None

    def drop_book(self, collision_rects, enemy_group=None):
        """Handle player dropping a book, only if drop position is not colliding"""
        if self.book:  # only drop if holding a book
            drop_pos = self._get_drop_position_if_clear(collision_rects, enemy_group, "book")
            if drop_pos:
                self.book = False
                return drop_pos
        return None

    def pick_up_bottle(self):
        """Handle player picking up a bottle"""
        if not self.bottle:  # only pick up if not already holding a bottle
            self.bottle = True

    def grab_book(self):
        """Handle player grabbing a book"""
        if not self.book:  # only grab if not already holding a book
            self.book = True

    def exit_box(self, collision_rects, enemy_group=None):
        """Handle player exiting the box state and placing box down"""
        if self.box:  # only exit if currently in a box
            drop_pos = self._get_drop_position_if_clear(collision_rects, enemy_group, "box")
            if drop_pos:
                self.box = False
                # sprite will automatically switch back to normal player sprite
                # through the animator's get_current_sprite method
                return drop_pos
        return None
    
    def enter_trees(self):
        if not self.trees and not self.box:  # only enter if not already in trees or box
            self.trees = True
            self.moveable = False
    
    def exit_trees(self):
        self.trees = False
        self.moveable = True

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
    
    def get_current_sprite(self, is_in_box=False, is_in_trees=False):
        if is_in_trees:
            # create a transparent sprite when in trees
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

def quit_check(running):
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        running = False
    return running