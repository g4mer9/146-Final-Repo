import pygame
import game
import math
from heapq import heappop, heappush # for A*

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

        self.load_sprites()
        self.image = self.sprites["down"][0]
        self.rect = self.image.get_rect(center=self.position)

# BEHAVIORS=====================================================================================================================================

    def patrol(self):
        # Patrol behavior
        pass

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
        dx, dy = 0, 0
        return dx, dy

# UPDATE=============================================================================================================================

    def update(self, dt):
        self.update_state_machine(dt)

        dx, dy = self.follow_path(dt)

        self.rect.center = (int(self.position.x), int(self.position.y))

        self.animator.update(self, dt, dx, dy)

    def update_state_machine(self, dt):
        
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
                        # handle the special case of enemy_up_1.png
                        sprite_path = f'data/sprites/enemy_{direction}_{i}.png'
                    else:
                        sprite_path = f'data/sprites/enemy_{direction}{i}.png'
                    sprite = pygame.image.load(sprite_path).convert_alpha()
                    self.sprites[direction].append(sprite)
                except pygame.error as e:
                    print(f"Warning: Could not load sprite {sprite_path}: {e}")
                    # create a placeholder if sprite is missing
                    placeholder = pygame.Surface((16, 16))
                    placeholder.fill((255, 0, 255))  # magenta placeholder
                    self.sprites[direction].append(placeholder)

# ANIMATOR UPDATE ======================================================================================================================================

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