import pygame
import math
from sound_system import sound_system


class EnemySensors:
    """Handles enemy sight and hearing detection systems"""
    
    def __init__(self, enemy):
        self.enemy = enemy
    
    def check_sight(self):
        """Check if the enemy can see the player"""
        self.enemy.player_seen_clearly = False
        self.enemy.player_glimpsed = False
        
        # Get player position
        player_pos = pygame.Vector2(self.enemy.player_ref.rect.center)
        enemy_pos = pygame.Vector2(self.enemy.position)
        
        # Calculate distance to player
        distance_to_player = enemy_pos.distance_to(player_pos)
        
        # Check if player is within sight range
        if distance_to_player > self.enemy.sight_range:
            return
        
        # Check if player is at the exact same position (distance is zero)
        if distance_to_player < 0.1:  # very close or same position
            # Player is right on top of enemy - definitely seen clearly
            self.enemy.player_seen_clearly = True
            self.enemy.last_known_player_position = player_pos.copy()
            return
        
        # Calculate direction to player
        direction_to_player = (player_pos - enemy_pos).normalize()
        
        # Get enemy facing direction
        enemy_facing = self._get_facing_direction()
        
        # Calculate angle between enemy facing direction and direction to player
        angle_to_player = math.degrees(math.atan2(direction_to_player.y, direction_to_player.x))
        enemy_facing_angle = math.degrees(math.atan2(enemy_facing.y, enemy_facing.x))
        
        # Normalize angles to 0-360 range
        angle_diff = abs(angle_to_player - enemy_facing_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        # Check if player is within vision cone
        if angle_diff <= self.enemy.vision_cone_angle / 2:
            # Player is in vision cone, now check for line of sight
            if self._has_line_of_sight(enemy_pos, player_pos):
                # Player is clearly visible - check if they're hidden
                if self.enemy.player_ref.trees or self.enemy.player_ref.locker or self.enemy.player_ref.box:
                    # Player is hidden but we caught a glimpse
                    self.enemy.player_glimpsed = True
                    # Update last known position even for glimpses
                    self.enemy.last_known_player_position = (player_pos.x, player_pos.y)
                else:
                    # Player is clearly seen
                    self.enemy.player_seen_clearly = True
                    self.enemy.last_known_player_position = (player_pos.x, player_pos.y)
    
    def _get_facing_direction(self):
        """Get the direction the enemy is currently facing as a vector"""
        direction_map = {
            "down": pygame.Vector2(0, 1),
            "up": pygame.Vector2(0, -1),
            "left": pygame.Vector2(-1, 0),
            "right": pygame.Vector2(1, 0)
        }
        return direction_map.get(self.enemy.animator.current_direction, pygame.Vector2(0, 1))
    
    def _has_line_of_sight(self, start_pos, end_pos):
        """Check if there's a clear line of sight between two positions"""
        # Check if start and end positions are the same or very close
        distance = start_pos.distance_to(end_pos)
        if distance < 1.0:
            return True  # Very close, assume clear line of sight
        
        # Use Bresenham's line algorithm to check for obstacles
        dx = abs(end_pos.x - start_pos.x)
        dy = abs(end_pos.y - start_pos.y)
        
        # Determine the step direction
        sx = 1 if start_pos.x < end_pos.x else -1
        sy = 1 if start_pos.y < end_pos.y else -1
        
        err = dx - dy
        
        x, y = int(start_pos.x), int(start_pos.y)
        end_x, end_y = int(end_pos.x), int(end_pos.y)
        
        # Add a safety counter to prevent infinite loops
        max_iterations = int(distance) + 10
        iteration_count = 0
        
        while True:
            # Safety check to prevent infinite loops
            iteration_count += 1
            if iteration_count > max_iterations:
                return True  # Assume clear if we hit the limit
            
            # Check if current position collides with any obstacle
            check_rect = pygame.Rect(x - 4, y - 4, 8, 8)
            for collision_rect in self.enemy.collision_rects:
                if check_rect.colliderect(collision_rect):
                    return False  # Line of sight blocked
            
            # Check if we've reached the end
            if x == end_x and y == end_y:
                break
            
            # Bresenham's algorithm step
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return True  # Clear line of sight

    def check_hearing(self):
        """Check if the enemy can hear a thrown bottle"""
        self.enemy.sound_heard = False
        
        # Get all sounds within hearing range
        sounds_in_range = sound_system.get_sounds_in_range(self.enemy.position, self.enemy.hearing_range)
        
        for sound in sounds_in_range:
            if sound['type'] == 'bottle_break':
                self.enemy.sound_heard = True
                self.enemy.last_known_player_position = sound['position']
                break
