import pygame
import random


class EnemyBehaviors:
    """Handles enemy AI behaviors and state logic"""
    
    def __init__(self, enemy):
        self.enemy = enemy
    
    # TODO: create set patrol paths depending on their spawn position instead of random
    def patrol(self):
        """Patrol behavior - enemy follows patrol path"""
        # If no patrol path, use the predefined patrol path
        if not self.enemy.path:
            self._set_next_patrol_point()
        
        # Move towards the next point in the path
        if self.enemy.path:
            target = self.enemy.path[0]
            direction = pygame.Vector2(target) - self.enemy.position
            distance = direction.length()
            
            # Use a smaller arrival threshold so enemies get closer to patrol points
            arrival_threshold = 1  # decreased from 2 to 1 pixel for more precise navigation
            
            if distance < arrival_threshold:
                # Arrived at this point, pop it and move to next patrol point
                self.enemy.path.pop(0)
                if not self.enemy.path:  # if path is empty, set next patrol point
                    self._advance_patrol_index()
                    self._set_next_patrol_point()
            else:
                direction = direction.normalize()
                speed = self.enemy.patrol_speed  # basic patrol speed
                move = direction * speed * self.enemy.dt
                
                # Add a small overshoot to help clear walls
                # If we're close to the target, add extra momentum in the same direction
                if distance < 20:  # when close to target
                    overshoot_factor = 1.2  # move 20% faster to clear obstacles
                    move *= overshoot_factor
                
                # Use collision handling instead of direct position update
                self.enemy.handle_collisions(move.x, move.y)

    # TODO: use A* pathfinding to player. 
    # use tile.is_tile_slow() to find slow tiles, and give them weight of 3 instead of 1. walls give weight of 100+ or inf
    def chase(self):
        """Chase behavior - enemy pursues and shoots at player"""
        # If player is clearly visible, shoot at them
        if self.enemy.player_seen_clearly:
            current_time = pygame.time.get_ticks()
            if current_time - self.enemy.last_shot_time >= self.enemy.shooting_cooldown:
                bullet = self._shoot_at_player()
                if bullet:
                    self.enemy.fired_bullets.append(bullet)
                    self.enemy.last_shot_time = current_time
        
        # later needs to be A* pathfinding instead of direct movement
        player_pos = pygame.Vector2(self.enemy.player_ref.rect.center)
        enemy_pos = pygame.Vector2(self.enemy.position)
        direction = player_pos - enemy_pos
        distance = direction.length()
        if distance > 2:
            direction = direction.normalize()
            speed = self.enemy.chase_speed  # Faster than patrol speed
            move = direction * speed * self.enemy.dt
            self.enemy.handle_collisions(move.x, move.y)

    # TODO: start timer only after A* pathfinding towards sound/seen player and destination reached
    # keep in mind, if the destination is a player in a box, a rand call should decide whether to enter chase or return to patrol
    # (also disable player.box)
    def inspect(self):
        """Inspect behavior - enemy investigates disturbances"""
        # Placeholder: enemy stands still when investigating
        # TODO: Implement movement towards last known position/sound location
        # For now, just transition back to patrol after a delay
        if not hasattr(self.enemy, 'inspect_timer'):
            self.enemy.inspect_timer = 0.0
        
        self.enemy.inspect_timer += self.enemy.dt
        if self.enemy.inspect_timer >= 3.0:  # investigate for 3 seconds then return to patrol
            self.enemy.state = "patrol"
            self.enemy.inspect_timer = 0.0
            self.enemy.last_known_player_position = None


    # when camp ends, A* needs to be called from current pos to start of set patrol path
    def camp(self):
        """Camp behavior - enemy stays at last known player location"""
        # Placeholder: enemy stands still when camping
        # TODO: Implement camping behavior with occasional turning/looking around
        # TODO: Add timer to return to patrol after losing player for too long
        pass

    def distracted(self):
        """Distracted behavior - enemy is distracted by books"""

        if hasattr(self.enemy, 'distraction_position') and self.enemy.distraction_position is not None:
            target = pygame.Vector2(self.enemy.distraction_position)
            enemy_pos = pygame.Vector2(self.enemy.position)
            direction = target - enemy_pos
            distance = direction.length()
            if distance > 2:
                direction = direction.normalize()
                speed = self.enemy.patrol_speed  # same as patrol speed
                move = direction * speed * self.enemy.dt
                self.enemy.handle_collisions(move.x, move.y)
                # Reset timer until enemy arrives at distraction
                self.enemy.distracted_timer = 0.0
                return # Don't start timer until arrived
        
        if not hasattr(self.enemy, 'distracted_timer'):
            self.enemy.distracted_timer = 0.0
        
        self.enemy.distracted_timer += self.enemy.dt
        if self.enemy.distracted_timer >= 30.0:  # distracted for 30 seconds then return to patrol
            self.enemy.state = "patrol"
            self.enemy.distracted_timer = 0.0
            self.enemy.distraction_position = None
    
    def _shoot_at_player(self):
        """Create a bullet projectile aimed at the player"""
        # Import here to avoid circular imports
        from bottle import BulletProjectile
        
        # Calculate direction to aim at player
        player_pos = pygame.Vector2(self.enemy.player_ref.rect.center)
        enemy_pos = pygame.Vector2(self.enemy.position)
        direction_vector = (player_pos - enemy_pos).normalize()
        
        # Determine the closest cardinal direction
        if abs(direction_vector.x) > abs(direction_vector.y):
            # More horizontal than vertical
            direction = "right" if direction_vector.x > 0 else "left"
        else:
            # More vertical than horizontal  
            direction = "down" if direction_vector.y > 0 else "up"
        
        # Create bullet projectile
        bullet = BulletProjectile(
            start_pos=self.enemy.position.copy(),
            direction=direction,
            speed=self.enemy.bullet_speed
        )
        
        return bullet
    
    def _set_next_patrol_point(self):
        """Set the next patrol point as the current path destination"""
        if hasattr(self.enemy, 'patrol_path_pixels') and self.enemy.patrol_path_pixels:
            next_point = self.enemy.patrol_path_pixels[self.enemy.patrol_index]
            self.enemy.path = [next_point]
        else:
            # Fallback to a default point if no patrol path is set
            self.enemy.path = [(self.enemy.position.x + 32, self.enemy.position.y)]

    def _advance_patrol_index(self):
        """Move to the next point in the patrol path, wrapping around if necessary"""
        if hasattr(self.enemy, 'patrol_path_pixels') and self.enemy.patrol_path_pixels:
            self.enemy.patrol_index = (self.enemy.patrol_index + 1) % len(self.enemy.patrol_path_pixels)

    def _generate_random_patrol_path(self):
        """Generate a random walkable path for debugging purposes (deprecated - use set patrol paths instead)"""
        # This method is kept for backward compatibility but should not be used
        # Map bounds (hardcoded for now, should match your map size)
        min_x, max_x = 32, 400
        min_y, max_y = 32, 200
        num_points = random.randint(3, 5)
        self.enemy.path = []
        for _ in range(num_points):
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            self.enemy.path.append((x, y))


    # TODO: allow enemy to lose track of the player if x seconds pass without seeing/hearing while in chase state, go into camp
    def check_transitions(self):
        """Check for state transitions based on sensor input"""
        # Update vision and hearing
        self.enemy.sensors.check_sight()
        self.enemy.sensors.check_hearing()
        
        # State transition logic
        if self.enemy.state == "patrol":
            if self.enemy.player_seen_clearly:
                self.enemy.state = "chase"
                self.enemy.show_state_icon("exclamation")
                # Start bullet cooldown to prevent immediate shooting
                self.enemy.last_shot_time = pygame.time.get_ticks()
                print("Enemy: Spotted player clearly - entering chase mode!")
            elif hasattr(self.enemy, 'book_spotted') and self.enemy.book_spotted:
                self.enemy.state = "distracted"
                self.enemy.show_state_icon("question")
                print("Enemy: Spotted a book - getting distracted...")
            elif self.enemy.player_glimpsed or self.enemy.sound_heard:
                self.enemy.state = "inspect"
                self.enemy.show_state_icon("question")
                if self.enemy.player_glimpsed:
                    print("Enemy: Caught a glimpse of something - investigating...")
                if self.enemy.sound_heard:
                    print("Enemy: Heard a sound - investigating...")
        
        elif self.enemy.state == "inspect":
            if self.enemy.player_seen_clearly:
                self.enemy.state = "chase"
                self.enemy.show_state_icon("exclamation")
                # Start bullet cooldown to prevent immediate shooting
                self.enemy.last_shot_time = pygame.time.get_ticks()
                print("Enemy: Found the target - entering chase mode!")
            # inspect state will automatically return to patrol when reaching investigation point
        
        elif self.enemy.state == "chase":
            # Add logic for losing the player and transitioning to camp or patrol
            if not self.enemy.player_seen_clearly:
                # Could add a timer here before transitioning to camp
                pass
            
        # Reset detection flags after processing
        if not (self.enemy.player_seen_clearly or self.enemy.player_glimpsed or self.enemy.sound_heard):
            # No immediate threats detected
            pass
