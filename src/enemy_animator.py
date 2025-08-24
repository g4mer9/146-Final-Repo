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

    def update(self, dt, dx, dy):
        """Update animation state based on enemy movement"""
        # determine if enemy is moving
        self.is_moving = dx != 0 or dy != 0
        
        # choose facing based on dominant axis of movement (fix for left/right never showing)
        # only update direction based on movement if actually moving
        if self.is_moving:
            if abs(dx) > abs(dy):
                # horizontal dominant
                self.current_direction = "right" if dx > 0 else "left"
            else:
                # vertical dominant
                self.current_direction = "down" if dy > 0 else "up"
            
        # update animation only if moving
        if self.is_moving:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0.0
                self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_sequence)
    
    def set_facing_direction(self, direction):
        """Manually set the facing direction (useful for chase behavior when not moving)"""
        if direction in ["up", "down", "left", "right"]:
            self.current_direction = direction
    
    def get_current_sprite(self, sprites):
        """Get the current sprite frame based on animation state"""
        if self.is_moving:
            # use animation sequence when moving
            frame_number = self.animation_sequence[self.current_frame_index]
        else:
            # use frame 0 when idle
            frame_number = 0
        
        return sprites[self.current_direction][frame_number]