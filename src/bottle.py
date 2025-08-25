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
                # Calculate a sound position that's offset from the wall in the direction the bottle came from
                # This helps ensure enemies investigate on the correct side of the wall
                offset_distance = 20  # pixels to offset from the wall
                sound_pos_x = self.position.x - (self.velocity.x / abs(self.velocity.x) if self.velocity.x != 0 else 0) * offset_distance
                sound_pos_y = self.position.y - (self.velocity.y / abs(self.velocity.y) if self.velocity.y != 0 else 0) * offset_distance
                
                # Create a sound event when bottle hits a wall
                sound_system.add_sound(
                    position=(sound_pos_x, sound_pos_y),
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


class BulletProjectile(pygame.sprite.Sprite):
    def __init__(self, start_pos, direction, speed=150):
        super().__init__()
        self.position = pygame.Vector2(start_pos)
        self.direction = direction
        self.speed = speed  # pixels per second
        
        # Load and rotate bullet sprite based on direction
        try:
            self.base_image = pygame.image.load('data/sprites/bullet.png').convert_alpha()
        except pygame.error as e:
            print(f"Warning: Could not load bullet.png: {e}")
            # Create a placeholder if sprite is missing
            self.base_image = pygame.Surface((8, 4))
            self.base_image.fill((255, 255, 0))  # yellow placeholder
        
        # Rotate sprite based on direction (bullet.png is default pointing right)
        if direction == "up":
            self.image = pygame.transform.rotate(self.base_image, 90)
        elif direction == "down":
            self.image = pygame.transform.rotate(self.base_image, -90)
        elif direction == "left":
            self.image = pygame.transform.rotate(self.base_image, 180)
        else:  # right
            self.image = self.base_image
        
        self.rect = self.image.get_rect(center=start_pos)
        
        # Create mask for pixel-perfect collision detection
        self.mask = pygame.mask.from_surface(self.image)
        
        # Set velocity based on direction
        self.velocity = pygame.Vector2(0, 0)
        if direction == "up":
            self.velocity.y = -self.speed
        elif direction == "down":
            self.velocity.y = self.speed
        elif direction == "left":
            self.velocity.x = -self.speed
        elif direction == "right":
            self.velocity.x = self.speed
    
    def update(self, dt, collision_rects, player_sprite=None):
        """Update bullet position and check for collisions"""
        # Move the bullet
        self.position += self.velocity * dt
        self.rect.center = (int(self.position.x), int(self.position.y))
        
        # Check for player collision using position-based collision (works even when player sprite is hidden)
        if player_sprite:
            # Calculate distance between bullet and player position
            player_pos = pygame.Vector2(player_sprite.position)
            bullet_pos = pygame.Vector2(self.position)
            distance = bullet_pos.distance_to(player_pos)
            
            # Use a collision radius (roughly the size of the player)
            collision_radius = 12  # Adjust this value as needed for game balance
            if distance <= collision_radius:
                return "player_hit"  # Signal that player was hit
        
        # Check for wall collisions
        bullet_rect = pygame.Rect(self.position.x - 4, self.position.y - 4, 8, 8)
        for collision_rect in collision_rects:
            if bullet_rect.colliderect(collision_rect):
                return "wall_hit"  # Hit a wall, should be destroyed
        
        return None  # No collision
