import pygame
from heapq import heappop, heappush # for A*
import tiles
from enemy_animator import EnemyAnimator
from enemy_behaviors import EnemyBehaviors
from enemy_renderer import EnemyRenderer
from enemy_sensors import EnemySensors

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position, player_ref, collision_rects):
        super().__init__()
        self.position = pygame.Vector2(position)
        self.player_ref = player_ref
        self.collision_rects = collision_rects
        
        # Initialize modular components
        self.animator = EnemyAnimator()
        self.behaviors = EnemyBehaviors(self)
        self.renderer = EnemyRenderer(self)
        self.sensors = EnemySensors(self)
        
        self.is_moving = False

        # for A*
        self.path = []
        self.current_target = None
        self.tiles = None
        self.tile_size = 16

        self.patrol_POIs = []
        self.patrol_index = 0

        # ADJUSTABLE ENEMY PARAMETERS =====================================================
        self.hearing_range = 120      # range in pixels for hearing sounds (adjustable)
        self.sight_range = 60       # range in pixels for vision cone (adjustable)
        self.vision_cone_angle = 60  # total angle of vision cone in degrees (adjustable)
        self.attack_range = 5
        self.bullet_speed = 150  # increased from 15 to 150 for reasonable bullet speed
        self.ms_between_AI_checks = 333
        self.last_AI_check = 0
        
        # Shooting mechanics
        self.shooting_cooldown = 1000  # milliseconds between shots
        self.last_shot_time = 0
        self.fired_bullets = []  # list to track bullets fired by this enemy

        # vision and detection states
        self.player_seen_clearly = False
        self.player_glimpsed = False
        self.sound_heard = False
        self.last_known_player_position = None

        # ADD NEW STATES HERE============================================================================================================================
        self.state = "patrol"
        self.states = {
            "patrol": self.behaviors.patrol,
            "chase": self.behaviors.chase,
            "inspect": self.behaviors.inspect,
            "distracted": self.behaviors.distracted,
            "camp": self.behaviors.camp
        }
        
        # Store dt for use in behaviors
        self.dt = 0

        # Icon display system for state changes
        self.show_icon = False
        self.icon_timer = 0.0
        self.icon_duration = 0.75  # show icon for 0.75 seconds
        self.current_icon = None
        self.load_icons()

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

    def load_icons(self):
        """Load icon sprites for state indicators"""
        try:
            self.exclamation_icon = pygame.image.load('data/sprites/exclamation.png').convert_alpha()
        except pygame.error as e:
            print(f"Warning: Could not load exclamation.png: {e}")
            # create a placeholder if sprite is missing
            self.exclamation_icon = pygame.Surface((16, 16))
            self.exclamation_icon.fill((255, 0, 0))  # red placeholder
            
        try:
            self.question_icon = pygame.image.load('data/sprites/question.png').convert_alpha()
        except pygame.error as e:
            print(f"Warning: Could not load question.png: {e}")
            # create a placeholder if sprite is missing
            self.question_icon = pygame.Surface((16, 16))
            self.question_icon.fill((0, 0, 255))  # blue placeholder

    def show_state_icon(self, icon_type):
        """Display an icon above the enemy for a brief period"""
        self.show_icon = True
        self.icon_timer = 0.0
        self.current_icon = icon_type

    # Delegate methods to modular components
    def draw_vision_cone(self, screen, map_layer):
        """Draw vision cone using renderer component"""
        self.renderer.draw_vision_cone(screen, map_layer)
    
    def draw_state_icon(self, screen, map_layer):
        """Draw state icon using renderer component"""
        self.renderer.draw_state_icon(screen, map_layer)

# PATHFINDING AND MOVEMENT =================================================================================================================

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



    def update(self, dt):
        self.update_state_machine(dt)
        
        # Update icon timer
        if self.show_icon:
            self.icon_timer += dt
            if self.icon_timer >= self.icon_duration:
                self.show_icon = False
                self.current_icon = None
                self.icon_timer = 0.0
        
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
            # Use behaviors component for state transitions
            self.behaviors.check_transitions()

        if self.state in self.states:
            self.states[self.state]()
