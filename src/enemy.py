import pygame
from heapq import heappop, heappush # for A*
import tiles
from enemy_animator import EnemyAnimator
from enemy_behaviors import EnemyBehaviors
from enemy_renderer import EnemyRenderer
from enemy_sensors import EnemySensors
from collision_utils import handle_full_collision
from sprite_utils import load_directional_sprites, load_icon_sprites

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position, player_ref, collision_rects, patrol_path=None, items_group=None, wall_tiles=None, slow_tiles=None, map_width=0, map_height=0):
        super().__init__()
        self.position = pygame.Vector2(position)
        self.player_ref = player_ref
        self.collision_rects = collision_rects
        self.items_group = items_group
        
        # Store tile lookup dictionaries for efficient pathfinding
        self.wall_tiles = wall_tiles or {}
        self.slow_tiles = slow_tiles or {}
        self.map_width = map_width
        self.map_height = map_height
        
        # Initialize modular components
        self.animator = EnemyAnimator()
        self.behaviors = EnemyBehaviors(self)
        self.renderer = EnemyRenderer(self)
        self.sensors = EnemySensors(self)
        
        # Movement and pathfinding
        self.is_moving = False
        self.path = []
        self.current_target = None
        self.tiles = None
        self.tile_size = 16

        # Set up patrol path
        self.patrol_path_tiles = patrol_path or [(15, 30), (20, 30), (20, 35), (15, 35)]
        self.patrol_index = 0
        self._convert_patrol_path_to_pixels()
        self.patrol_POIs = []

        # Enemy parameters
        self.hearing_range = 240
        self.close_hearing_range = 32
        self.sight_range = 60
        self.vision_cone_angle = 90
        self.attack_range = 5
        self.bullet_speed = 150
        self.last_AI_check = 0
        self.patrol_speed = 50
        self.chase_speed = 80
        self.chase_AI_interval = 1000
        self.patrol_AI_interval = 333
        self.inspect_AI_interval = 150
        self.distracted_AI_interval = 2000

        # Shooting mechanics
        self.shooting_cooldown = 1000
        self.last_shot_time = 0
        self.fired_bullets = []

        # vision and detection states
        self.player_seen_clearly = False
        self.player_glimpsed = False
        self.sound_heard = False
        self.book_spotted = False
        self.last_known_player_position = None
        self.distraction_position = None
        
        # Wary flags for hiding places (for inspect behavior)
        self.wary_of_boxes = False
        self.wary_of_trees = False
        self.wary_of_lockers = False

        # State management
        self.state = "patrol"
        self.states = {
            "patrol": self.behaviors.patrol,
            "chase": self.behaviors.chase,
            "inspect": self.behaviors.inspect,
            "distracted": self.behaviors.distracted,
            "camp": self.behaviors.camp
        }
        self.dt = 0

        # Icon display system for state changes
        self.show_icon = False
        self.icon_timer = 0.0
        self.icon_duration = 0.75
        self.current_icon = None
        
        # Load sprites and icons
        self.sprites = load_directional_sprites("soldier")
        icons = load_icon_sprites()
        self.exclamation_icon = icons['exclamation']
        self.question_icon = icons['question']

        self.image = self.sprites["down"][0]
        self.rect = self.image.get_rect(center=self.position)

    def show_state_icon(self, icon_type):
        """Display an icon above the enemy for a brief period"""
        self.show_icon = True
        self.icon_timer = 0.0
        self.current_icon = icon_type

    def draw_vision_cone(self, screen, map_layer):
        """Draw vision cone using renderer component"""
        self.renderer.draw_vision_cone(screen, map_layer)
    
    def draw_state_icon(self, screen, map_layer):
        """Draw state icon using renderer component"""
        self.renderer.draw_state_icon(screen, map_layer)

    def follow_path(self, dt):
        """For now, movement is handled in patrol(), so just return the last move"""
        return 0, 0

    def handle_collisions(self, dx, dy):
        """Handle enemy collisions using shared collision system"""
        enemy_size = (16, 16)
        collision_x, collision_y = handle_full_collision(
            self.position, enemy_size, self.collision_rects, [self.player_ref], dx, dy
        )
        
        # If collision detected, skip to next patrol point
        if (collision_x or collision_y) and self.path:
            self.path.pop(0)
        
        # Update rect position
        self.rect.center = (int(self.position.x), int(self.position.y))



    def update(self, dt):
        # Capture previous position so we know true movement after behaviors run
        prev_x, prev_y = self.position.x, self.position.y
        
        # Run state machine (this may move the enemy via behaviors + collision handling)
        self.update_state_machine(dt)

        # Compute actual movement delta from behaviors
        dx = self.position.x - prev_x
        dy = self.position.y - prev_y

        # Update icon timer
        if self.show_icon:
            self.icon_timer += dt
            if self.icon_timer >= self.icon_duration:
                self.show_icon = False
                self.current_icon = None
                self.icon_timer = 0.0

        # Feed actual movement delta to animator (this will update direction based on movement if moving)
        self.animator.update(dt, dx, dy)
        
        # If we're chasing, always face the player regardless of actual movement
        # This must come AFTER animator.update() to override movement-based direction
        if self.state == "chase":
            target_vec = pygame.Vector2(self.player_ref.rect.center) - self.position
            if target_vec.length() > 0.1:
                # Determine facing direction based on direction to player
                if abs(target_vec.x) > abs(target_vec.y):
                    desired_direction = "right" if target_vec.x > 0 else "left"
                else:
                    desired_direction = "down" if target_vec.y > 0 else "up"
                
                # Use the new method to set facing direction
                self.animator.set_facing_direction(desired_direction)

        # Update the sprite image & rect (rect already generally updated in collision handler, but ensure sync)
        self.image = self.animator.get_current_sprite(self.sprites)
        self.rect.center = (int(self.position.x), int(self.position.y))

    def update_state_machine(self, dt):
        # Store dt for use in behaviors
        self.dt = dt
        
        # Dynamic AI check interval based on state for performance optimization
        if self.state == "chase":
            ai_check_interval = self.chase_AI_interval
        elif self.state == "patrol":
            ai_check_interval = self.patrol_AI_interval
        elif self.state == "inspect":
            ai_check_interval = self.inspect_AI_interval
        else:
            ai_check_interval = self.distracted_AI_interval

        current_time = pygame.time.get_ticks()
        if current_time - self.last_AI_check >= ai_check_interval:
            self.last_AI_check = current_time
            # Use behaviors component for state transitions
            self.behaviors.check_transitions()
        
        # Execute the current state behavior every frame
        if self.state in self.states:
            self.states[self.state]()

    def _convert_patrol_path_to_pixels(self):
        """Convert tile coordinates to pixel coordinates for patrol path"""
        self.patrol_path_pixels = []
        for tile_x, tile_y in self.patrol_path_tiles:
            pixel_x = tile_x * self.tile_size + 8  # +8 to center on tile
            pixel_y = tile_y * self.tile_size + 8
            self.patrol_path_pixels.append((pixel_x, pixel_y))

    def set_patrol_path(self, new_patrol_path):
        """Set a new patrol path for this enemy (in tile coordinates)"""
        self.patrol_path_tiles = new_patrol_path
        self.patrol_index = 0
        self._convert_patrol_path_to_pixels()
        # Reset current path to start using new patrol path
        self.path = []
