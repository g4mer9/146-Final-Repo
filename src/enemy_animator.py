import pygame


class EnemyAnimator:
    """Handles enemy sprite animation"""
    
    def __init__(self):
        self.current_direction = "down"
        self.is_moving = False
        self.animation_timer = 0.0
        self.animation_speed = 0.3  # time between frames in seconds
        self.current_frame_index = 0
        # animation sequence for soldier sprites: 0, 1, 0, 1...
        self.animation_sequence = [0, 1]
        
        # Direction change smoothing to prevent wall-collision glitching
        self.direction_change_cooldown = 0.15  # minimum time between direction changes
        self.last_direction_change_time = 0.0
        self.pending_direction = None
        self.direction_stability_threshold = 3  # frames a direction must be consistent
        self.direction_consistency_count = 0
        self.last_attempted_direction = None

    def update(self, dt, dx, dy):
        """Update animation state based on enemy movement"""
        # Add minimum movement threshold to prevent visual glitching
        movement_threshold = 0.5  # pixels per frame - reduced from 0.75
        movement_magnitude = (dx * dx + dy * dy) ** 0.5
        
        # determine if enemy is moving with threshold
        self.is_moving = movement_magnitude > movement_threshold
        
        # choose facing based on dominant axis of movement (fix for left/right never showing)
        # only update direction based on movement if actually moving above threshold
        if self.is_moving:
            # Determine intended direction based on movement
            if abs(dx) > abs(dy):
                # horizontal dominant
                intended_direction = "right" if dx > 0 else "left"
            else:
                # vertical dominant
                intended_direction = "down" if dy > 0 else "up"
            
            # Apply direction change smoothing to prevent glitching
            current_time = pygame.time.get_ticks() / 1000.0  # Convert to seconds
            
            # Check if this direction is consistent
            if intended_direction == self.last_attempted_direction:
                self.direction_consistency_count += 1
            else:
                self.direction_consistency_count = 1
                self.last_attempted_direction = intended_direction
            
            # Only change direction if:
            # 1. Enough time has passed since last change AND
            # 2. The direction has been consistent for several frames
            if (current_time - self.last_direction_change_time >= self.direction_change_cooldown and
                self.direction_consistency_count >= self.direction_stability_threshold):
                
                if intended_direction != self.current_direction:
                    self.current_direction = intended_direction
                    self.last_direction_change_time = current_time
                    self.direction_consistency_count = 0
            
        # update animation only if moving
        if self.is_moving:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0.0
                self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_sequence)
    
    def set_facing_direction(self, direction):
        """Manually set the facing direction (useful for chase behavior when not moving)"""
        if direction in ["up", "down", "left", "right"]:
            # Allow manual direction setting but still respect cooldown to prevent glitching
            current_time = pygame.time.get_ticks() / 1000.0
            if current_time - self.last_direction_change_time >= self.direction_change_cooldown:
                if direction != self.current_direction:
                    self.current_direction = direction
                    self.last_direction_change_time = current_time
                    # Reset consistency tracking since this is a manual override
                    self.direction_consistency_count = 0
                    self.last_attempted_direction = direction
    
    def get_current_sprite(self, sprites):
        """Get the current sprite frame based on animation state"""
        if self.is_moving:
            # use animation sequence when moving
            frame_number = self.animation_sequence[self.current_frame_index]
        else:
            # use frame 0 when idle
            frame_number = 0
        
        return sprites[self.current_direction][frame_number]