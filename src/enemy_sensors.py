import pygame
import math
from sound_system import sound_system
from movement_utils import get_direction_vector


class EnemySensors:
    """Handles enemy sight and hearing detection systems"""
    
    def __init__(self, enemy):
        self.enemy = enemy
        # Track how long player has been visible for glimpse vs clear sight distinction
        self.first_sight_time = None  # When player was first spotted
        self.clear_sight_threshold = 0.3  # seconds before glimpse becomes clear sight (adjusted for 333ms intervals)
        self.player_currently_visible = False
    
    def check_sight(self):
        """Check if the enemy can see the player or books"""
        self.enemy.player_seen_clearly = False
        self.enemy.player_glimpsed = False
        self.enemy.book_spotted = False
        
        # Track previous visibility state
        was_visible = self.player_currently_visible
        self.player_currently_visible = False
        
        # Check for books within sight range
        if self.enemy.items_group:
            enemy_pos = pygame.Vector2(self.enemy.position)
            for item in self.enemy.items_group:
                if item.item_name == 'book':
                    book_pos = pygame.Vector2(item.rect.center)
                    distance_to_book = enemy_pos.distance_to(book_pos)
                    
                    # Check if book is within sight range
                    if distance_to_book <= self.enemy.sight_range:
                        # Check if book is in vision cone
                        if distance_to_book < 0.1:  # very close
                            self.enemy.book_spotted = True
                            self.enemy.distraction_position = (book_pos.x, book_pos.y)
                        else:
                            direction_to_book = (book_pos - enemy_pos).normalize()
                            enemy_facing = self._get_facing_direction()
                            
                            # Calculate angle between enemy facing direction and direction to book
                            angle_to_book = math.degrees(math.atan2(direction_to_book.y, direction_to_book.x))
                            enemy_facing_angle = math.degrees(math.atan2(enemy_facing.y, enemy_facing.x))
                            
                            # Normalize angles to 0-360 range
                            angle_diff = abs(angle_to_book - enemy_facing_angle)
                            if angle_diff > 180:
                                angle_diff = 360 - angle_diff
                            
                            # Check if book is within vision cone
                            if angle_diff <= self.enemy.vision_cone_angle / 2:
                                # Book is in vision cone, now check for line of sight
                                if self._has_line_of_sight(enemy_pos, book_pos):
                                    self.enemy.book_spotted = True
                                    self.enemy.distraction_position = (book_pos.x, book_pos.y)
                                    break  # Only need to spot one book
        
        # Get player position
        player_pos = pygame.Vector2(self.enemy.player_ref.rect.center)
        enemy_pos = pygame.Vector2(self.enemy.position)
        
        # Calculate distance to player
        distance_to_player = enemy_pos.distance_to(player_pos)
        
        # Check if player is within sight range
        if distance_to_player > self.enemy.sight_range:
            # Player out of range - reset visibility tracking
            self.first_sight_time = None
            self.player_currently_visible = False
            return
        
        # Check if player is at the exact same position (distance is zero)
        if distance_to_player < 0.1:  # very close or same position
            # Player is right on top of enemy - definitely seen clearly
            self.player_currently_visible = True
            if self.first_sight_time is None:
                self.first_sight_time = pygame.time.get_ticks()
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
                self.player_currently_visible = True
                
                # Track when player was first spotted
                current_time = pygame.time.get_ticks()
                if self.first_sight_time is None:
                    self.first_sight_time = current_time
                
                # Calculate how long player has been visible
                visibility_duration = (current_time - self.first_sight_time) / 1000.0  # convert to seconds
                
                # Check if they're hidden (always counts as glimpse regardless of timer)
                if self.enemy.player_ref.trees or self.enemy.player_ref.locker or self.enemy.player_ref.box:
                    # Player is hidden but we caught a glimpse
                    self.enemy.player_glimpsed = True
                    # Update last known position even for glimpses
                    self.enemy.last_known_player_position = (player_pos.x, player_pos.y)
                else:
                    # Player is not hidden - check visibility duration
                    if visibility_duration >= self.clear_sight_threshold:
                        # Player has been visible long enough - seen clearly
                        self.enemy.player_seen_clearly = True
                        self.enemy.last_known_player_position = (player_pos.x, player_pos.y)
                    else:
                        # Player visible but not long enough - just a glimpse
                        self.enemy.player_glimpsed = True
                        self.enemy.last_known_player_position = (player_pos.x, player_pos.y)
        
        # If player is not currently visible, reset the timer
        if not self.player_currently_visible:
            self.first_sight_time = None
    
    def _get_facing_direction(self):
        """Get the direction the enemy is currently facing as a vector"""
        return get_direction_vector(self.enemy.animator.current_direction)
    
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
                
                # Find a walkable position near the sound instead of using exact break position
                sound_pos = pygame.Vector2(sound['position'])
                walkable_pos = self._find_walkable_investigation_target(sound_pos)
                
                self.enemy.last_known_player_position = walkable_pos if walkable_pos else sound['position']
                break
    
    def _find_walkable_investigation_target(self, sound_pos, search_radius=2):
        """Find a walkable position near the sound for investigation"""
        tile_size = 16
        sound_tile_x = int(sound_pos.x // tile_size)
        sound_tile_y = int(sound_pos.y // tile_size)
        
        # First check if the sound position itself is walkable
        if self._is_position_walkable(sound_tile_x, sound_tile_y):
            return sound_pos
        
        # Try positions in expanding circles around the sound
        for radius in range(1, search_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    # Skip positions not on the current radius circle
                    if abs(dx) != radius and abs(dy) != radius:
                        continue
                    
                    check_x = sound_tile_x + dx
                    check_y = sound_tile_y + dy
                    
                    # Check bounds
                    if (check_x < 0 or check_x >= self.enemy.map_width or 
                        check_y < 0 or check_y >= self.enemy.map_height):
                        continue
                    
                    # Check if tile is walkable
                    if self._is_position_walkable(check_x, check_y):
                        world_x = check_x * tile_size + tile_size // 2
                        world_y = check_y * tile_size + tile_size // 2
                        return pygame.Vector2(world_x, world_y)
        
        return None  # No walkable position found
    
    def _is_position_walkable(self, tile_x, tile_y):
        """Check if a tile position is walkable (not a wall)"""
        from tiles import is_tile_wall_fast
        return not is_tile_wall_fast(self.enemy.wall_tiles, tile_x, tile_y)
