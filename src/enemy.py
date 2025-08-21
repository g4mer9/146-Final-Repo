import pygame
import math
from heapq import heappop, heappush # for A*
import tiles

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position, player_ref, collision_rects):
        super().__init__()
        self.position = pygame.Vector2(position)
        self.player_ref = player_ref
        self.collision_rects = collision_rects
        self.animator = EnemyAnimator()
        self.is_moving = False

        # for A*
        self.path = []
        self.current_target = None
        self.tiles = None
        self.tile_size = 16

        self.patrol_POIs = []
        self.patrol_index = 0

        # placeholder values
        self.hearing_range = 7
        self.sight_range = 10
        self.attack_range = 5
        self.bullet_speed = 15
        self.ms_between_AI_checks = 333
        self.last_AI_check = 0

        self.state = "patrol"
        self.states = {
            "patrol": self.patrol,
            "chase": self.chase,
            "distracted": self.distracted
        }
        
        # Store dt for use in behaviors
        self.dt = 0

        self.load_sprites()
        self.image = self.sprites["down"][0]
        self.rect = self.image.get_rect(center=self.position)

    def load_sprites(self):
        """Load enemy sprite images"""
        self.sprites = {}
        directions = ["down", "up", "left", "right"]
        for direction in directions:
            self.sprites[direction] = []
            for i in range(2):  # soldier sprites only have 0 and 1
                try:
                    sprite_path = f'data/sprites/soldier_{direction}{i}.png'
                    sprite = pygame.image.load(sprite_path).convert_alpha()
                    self.sprites[direction].append(sprite)
                except pygame.error as e:
                    print(f"Warning: Could not load sprite {sprite_path}: {e}")
                    # create a placeholder if sprite is missing
                    placeholder = pygame.Surface((16, 16))
                    placeholder.fill((255, 0, 255))  # magenta placeholder
                    self.sprites[direction].append(placeholder)

# BEHAVIORS=====================================================================================================================================

    # mostly implemented patrol state for testing
    # in full version, random paths won't be used
    def patrol(self):
        # If no patrol path, generate a new random path
        if not self.path:
            self.generate_random_patrol_path()
        # Move towards the next point in the path
        if self.path:
            target = self.path[0]
            direction = pygame.Vector2(target) - self.position
            distance = direction.length()
            if distance < 2:
                # Arrived at this point, pop it
                self.path.pop(0)
            else:
                direction = direction.normalize()
                speed = 50  # basic patrol speed
                move = direction * speed * self.dt
                # Use collision handling instead of direct position update
                self.handle_collisions(move.x, move.y)

    def chase(self):
        # Chase behavior
        pass

    def distracted(self):
        # distracted behavior
        pass

    # for HFSM
    def check_transitions(self):
        # Check for state transitions
        pass

    # implement later for A*
    def follow_path(self, dt):
        # For now, movement is handled in patrol(), so just return the last move
        return 0, 0

    def handle_collisions(self, dx, dy):
        """Handle enemy collisions with walls, similar to player collision handling"""
        enemy_size = (16, 16)
        
        # Store original position in case we need to revert
        original_x = self.position.x
        original_y = self.position.y
        
        # Handle horizontal movement first
        if dx != 0:
            self.position.x += dx
            enemy_rect = pygame.Rect(self.position.x - enemy_size[0]//2, 
                                   self.position.y - enemy_size[1]//2, 
                                   enemy_size[0], enemy_size[1])
            
            # Check for horizontal collisions
            collision_found = False
            closest_x = self.position.x
            
            for rect in self.collision_rects:
                if enemy_rect.colliderect(rect):
                    collision_found = True
                    if dx > 0:  # moving right
                        closest_x = min(closest_x, rect.left - enemy_size[0]//2)
                    else:  # moving left
                        closest_x = max(closest_x, rect.right + enemy_size[0]//2)
            
            # Check for player collision
            if enemy_rect.colliderect(self.player_ref.rect):
                collision_found = True
                if dx > 0:  # moving right
                    closest_x = min(closest_x, self.player_ref.rect.left - enemy_size[0]//2)
                else:  # moving left
                    closest_x = max(closest_x, self.player_ref.rect.right + enemy_size[0]//2)
            
            if collision_found:
                self.position.x = closest_x
                # If collision detected, skip to next patrol point
                if self.path:
                    self.path.pop(0)
        
        # Handle vertical movement second
        if dy != 0:
            self.position.y += dy
            enemy_rect = pygame.Rect(self.position.x - enemy_size[0]//2, 
                                   self.position.y - enemy_size[1]//2, 
                                   enemy_size[0], enemy_size[1])
            
            # Check for vertical collisions
            collision_found = False
            closest_y = self.position.y
            
            for rect in self.collision_rects:
                if enemy_rect.colliderect(rect):
                    collision_found = True
                    if dy > 0:  # moving down
                        closest_y = min(closest_y, rect.top - enemy_size[1]//2)
                    else:  # moving up
                        closest_y = max(closest_y, rect.bottom + enemy_size[1]//2)
            
            # Check for player collision
            if enemy_rect.colliderect(self.player_ref.rect):
                collision_found = True
                if dy > 0:  # moving down
                    closest_y = min(closest_y, self.player_ref.rect.top - enemy_size[1]//2)
                else:  # moving up
                    closest_y = max(closest_y, self.player_ref.rect.bottom + enemy_size[1]//2)
            
            if collision_found:
                self.position.y = closest_y
                # If collision detected, skip to next patrol point
                if self.path:
                    self.path.pop(0)
        
        # Update rect position
        self.rect.center = (int(self.position.x), int(self.position.y))

    # debug only function. comment out when done
    def generate_random_patrol_path(self):
        # Generate a random walkable path of 3-5 points within the map bounds
        import random
        # Map bounds (hardcoded for now, should match your map size)
        min_x, max_x = 32, 400
        min_y, max_y = 32, 200
        num_points = random.randint(3, 5)
        self.path = []
        for _ in range(num_points):
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            self.path.append((x, y))

# UPDATE=============================================================================================================================

    def update(self, dt):
        self.update_state_machine(dt)
        # For now, dx/dy are not used, but keep for animator compatibility
        dx, dy = 0, 0
        # If moving, calculate dx/dy for animation
        if self.path:
            target = self.path[0]
            direction = pygame.Vector2(target) - self.position
            if direction.length() > 1:
                direction = direction.normalize()
                speed = 50
                move = direction * speed * dt
                dx, dy = move.x, move.y
        self.animator.update(self, dt, dx, dy)
        # Update the sprite image
        self.image = self.animator.get_current_sprite(self.sprites)

    def update_state_machine(self, dt):
        # Store dt for use in behaviors
        self.dt = dt
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_AI_check >= self.ms_between_AI_checks:
            self.last_AI_check = current_time
            # state check
            self.check_transitions()

        if self.state in self.states:
            self.states[self.state]()

# ENEMY ANIMATOR ====================================================================================================================

class EnemyAnimator:
    def __init__(self):
        self.current_direction = "down"
        self.is_moving = False
        self.animation_timer = 0.0
        self.animation_speed = 0.3  # time between frames in seconds
        self.current_frame_index = 0
        # animation sequence for soldier sprites: 0, 1, 0, 1...
        self.animation_sequence = [0, 1]

# ANIMATOR UPDATE ======================================================================================================================================

    def update(self, enemy, dt, dx, dy):
        # determine if enemy is moving
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
    
    def get_current_sprite(self, sprites):
        if self.is_moving:
            # use animation sequence when moving
            frame_number = self.animation_sequence[self.current_frame_index]
        else:
            # use frame 0 when idle
            frame_number = 0
        
        return sprites[self.current_direction][frame_number]