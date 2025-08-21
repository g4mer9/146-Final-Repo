import pygame
from sound_system import sound_system


class BottleProjectile(pygame.sprite.Sprite):
    def __init__(self, start_pos, direction):
        super().__init__()
        self.position = pygame.Vector2(start_pos)
        self.direction = direction
        self.speed = 200  # pixels per second
        self.animator = BottleAnimator()
        self.image = self.animator.get_current_sprite(direction)
        self.rect = self.image.get_rect(center=start_pos)
        
        # set velocity based on direction
        self.velocity = pygame.Vector2(0, 0)
        if direction == "up":
            self.velocity.y = -self.speed
        elif direction == "down":
            self.velocity.y = self.speed
        elif direction == "left":
            self.velocity.x = -self.speed
        elif direction == "right":
            self.velocity.x = self.speed
    
    def update(self, dt, collision_rects):
        """Update bottle position and check for collisions"""
        # update animation
        self.animator.update(dt)
        self.image = self.animator.get_current_sprite(self.direction)
        
        # move the bottle
        self.position += self.velocity * dt
        self.rect.center = (int(self.position.x), int(self.position.y))
        
        # check for wall collisions
        bottle_rect = pygame.Rect(self.position.x - 8, self.position.y - 8, 16, 16)
        for collision_rect in collision_rects:
            if bottle_rect.colliderect(collision_rect):
                # Create a sound event when bottle hits a wall
                sound_system.add_sound(
                    position=(self.position.x, self.position.y),
                    sound_type='bottle_break',
                    range_radius=80,  # ADJUSTABLE: hearing range for bottle break
                    duration=333  # sound lasts for 333ms as specified
                )
                return True  # hit a wall, should be destroyed
        
        return False  # no collision


class BottleAnimator:
    def __init__(self):
        self.animation_timer = 0.0
        self.animation_speed = 0.05  # time between frames in seconds
        self.current_frame_index = 0
        
        # load bottle sprites for each direction
        self.sprites = {}
        directions = ["down", "up", "left", "right"]
        for direction in directions:
            try:
                sprite_path = f'data/sprites/bottle_{direction}.png'
                sprite = pygame.image.load(sprite_path).convert_alpha()
                self.sprites[direction] = sprite
            except pygame.error as e:
                print(f"Warning: Could not load bottle sprite {sprite_path}: {e}")
                # create a placeholder if sprite is missing
                placeholder = pygame.Surface((16, 16))
                placeholder.fill((0, 255, 0))  # green placeholder
                self.sprites[direction] = placeholder
    
    def update(self, dt):
        """Update animation timing"""
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0.0
            self.current_frame_index = (self.current_frame_index + 1) % 4  # cycle through 4 directions
    
    def get_current_sprite(self, facing_direction):
        """Get the current sprite based on facing direction and animation frame"""
        # cycle through all directions for spinning effect
        directions = ["down", "right", "up", "left"]
        sprite_direction = directions[self.current_frame_index]
        return self.sprites.get(sprite_direction, self.sprites["down"])
