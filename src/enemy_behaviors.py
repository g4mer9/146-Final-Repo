import pygame
import random
import heapq
from state_utils import check_hiding_spot_at_position, update_wary_flags, transition_to_chase, transition_to_patrol
from movement_utils import get_closest_cardinal_direction, move_towards_target


class EnemyBehaviors:
    """Handles enemy AI behaviors and state logic"""
    
    def __init__(self, enemy):
        self.enemy = enemy
        self.prev_pathfind_length = 0
        self.current_path = []
        self.pathfind_cooldown = 1500
        self.last_player_position = None  # Track last known player position for optimization
        
        # Stuck detection for wall-running fix
        self.last_position = None
        self.stuck_timer = 0.0
        self.stuck_threshold = 0.5  # seconds before considering enemy "stuck"
        self.min_movement_distance = 5.0  # minimum distance to consider as "movement" 

    """A* with 8 directions for better agent movement"""
    def _a_star_pathfind(self, start_position, goal_position, tile_size = 16, max_path_length=25):
        start_grid = (int(start_position.x // tile_size), int(start_position.y // tile_size))
        goal_grid = (int(goal_position.x // tile_size), int(goal_position.y // tile_size))
        
        # Early exit if goal is too far away (performance optimization)
        manhattan_distance = abs(start_grid[0] - goal_grid[0]) + abs(start_grid[1] - goal_grid[1])
        if manhattan_distance > max_path_length:
            return []  # Return empty path if too far
        
        # 8-directional movement and cost
        directions = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
        diagonal_cost = 1.414
        
        priorityqueue = [(0, 0, start_grid, [(start_position.x, start_position.y)])]
        pathfinding = set()
        nodes_expanded = 0  # Track performance
        max_nodes = 300  # Reduced from 500 to 300 for better performance
        
        while priorityqueue and nodes_expanded < max_nodes:
            _, goal_cost, current, path = heapq.heappop(priorityqueue)
            
            if current in pathfinding:
                continue
            pathfinding.add(current)
            nodes_expanded += 1
            
            if current == goal_grid:
                return [pygame.Vector2(pos) for pos in path[1:]]
            
            for diagonal_x, diagonal_y in directions:
                neighbor = (current[0] + diagonal_x, current[1] + diagonal_y)
                
                if neighbor in pathfinding:
                    continue
                
                # Check bounds - make sure neighbor is within map
                if (neighbor[0] < 0 or neighbor[0] >= self.enemy.map_width or 
                    neighbor[1] < 0 or neighbor[1] >= self.enemy.map_height):
                    continue
                
                # Check for diagonal corner cutting so the agents don't clip thru walls
                if diagonal_x != 0 and diagonal_y != 0:
                    if (self._get_tile_weight(current[0] + diagonal_x, current[1]) == float('inf') or 
                        self._get_tile_weight(current[0], current[1] + diagonal_y) == float('inf')):
                        continue
                
                move_cost = self._get_tile_weight(neighbor[0], neighbor[1])
                if move_cost == float('inf'):
                    continue

                # Add in diagonal cost
                if diagonal_x != 0 and diagonal_y != 0:
                    move_cost *= diagonal_cost
                
                new_goal_cost = goal_cost + move_cost
                h_cost = abs(neighbor[0] - goal_grid[0]) + abs(neighbor[1] - goal_grid[1])
                
                neighbor_pos = (neighbor[0] * tile_size + tile_size // 2,
                            neighbor[1] * tile_size + tile_size // 2)
                
                heapq.heappush(priorityqueue, (new_goal_cost + h_cost, new_goal_cost,\
                                               neighbor, path + [neighbor_pos]))
        
        return []
    
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

    def _get_tile_weight(self, grid_x, grid_y):
        """Tile weight helper func for A* 
        Get movement cost for a tile position using fast lookup dictionaries"""
        # Import the fast lookup function from tiles module
        from tiles import get_tile_weight_fast
        return get_tile_weight_fast(self.enemy.wall_tiles, self.enemy.slow_tiles, grid_x, grid_y)

    def _is_stuck(self, current_pos):
        """Detect if enemy is stuck (not moving for a while)"""
        if self.last_position is None:
            self.last_position = current_pos.copy()
            return False
        
        distance_moved = current_pos.distance_to(self.last_position)
        
        if distance_moved < self.min_movement_distance:
            self.stuck_timer += self.enemy.dt
        else:
            self.stuck_timer = 0.0
            self.last_position = current_pos.copy()
        
        return self.stuck_timer >= self.stuck_threshold

    def _find_intermediate_waypoint(self, enemy_pos, player_pos):
        """Find an intermediate waypoint when direct path is blocked"""
        tile_size = 16
        
        # Try positions around the enemy to find a good intermediate point
        search_radius = 3  # tiles
        best_waypoint = None
        best_score = float('inf')
        
        enemy_tile_x = int(enemy_pos.x // tile_size)
        enemy_tile_y = int(enemy_pos.y // tile_size)
        
        for dx in range(-search_radius, search_radius + 1):
            for dy in range(-search_radius, search_radius + 1):
                if dx == 0 and dy == 0:
                    continue
                    
                test_x = enemy_tile_x + dx
                test_y = enemy_tile_y + dy
                
                # Skip if this position is a wall
                if self._get_tile_weight(test_x, test_y) == float('inf'):
                    continue
                
                test_pos = pygame.Vector2(test_x * tile_size + 8, test_y * tile_size + 8)
                
                # Score based on distance to player (closer is better)
                score = test_pos.distance_to(player_pos)
                
                if score < best_score:
                    best_score = score
                    best_waypoint = test_pos
        
        return best_waypoint



    # TODO: use A* pathfinding to player. 
    # use tile.is_tile_slow() to find slow tiles, and give them weight of 3 instead of 1. walls give weight of 100+ or inf
    def chase(self):
        """Chase behavior - enemy pursues and shoots at player now with A* pathfinding"""
        # Shoot at player during chase mode (regardless of visibility)
        current_time = pygame.time.get_ticks()
        if current_time - self.enemy.last_shot_time >= self.enemy.shooting_cooldown:
            if bullet := self._shoot_at_player():
                self.enemy.fired_bullets.append(bullet)
                self.enemy.last_shot_time = current_time
        
        # Pathfinding logic with optimization
        current_time = pygame.time.get_ticks()
        player_pos = pygame.Vector2(self.enemy.player_ref.rect.center)
        enemy_pos = pygame.Vector2(self.enemy.position)
        
        # Check if enemy is stuck
        is_stuck = self._is_stuck(enemy_pos)
        
        # Check if player has moved significantly since last pathfind
        player_moved_significantly = False
        if self.last_player_position is not None:
            distance_moved = player_pos.distance_to(self.last_player_position)
            player_moved_significantly = distance_moved > 24  # Reduced from 32 to 24 pixels (1.5 tiles)
        
        # Check if player is very close (might be behind a thin wall)
        distance_to_player = enemy_pos.distance_to(player_pos)
        player_very_close = distance_to_player <= 48  # Within 3 tiles
        
        # Only recalculate path if:
        # 1. Cooldown has passed AND
        # 2. (Player moved significantly OR no current path OR path is nearly complete OR enemy is stuck)
        should_recalculate = (
            current_time - self.prev_pathfind_length >= self.pathfind_cooldown and
            (player_moved_significantly or not self.current_path or len(self.current_path) <= 2 or is_stuck)
        )
        
        if should_recalculate:
            # If player is very close but enemy is stuck, find intermediate waypoint first
            if player_very_close and is_stuck:
                intermediate_waypoint = self._find_intermediate_waypoint(enemy_pos, player_pos)
                if intermediate_waypoint:
                    # Try pathfinding to intermediate waypoint first
                    new_path = self._a_star_pathfind(enemy_pos, intermediate_waypoint)
                    if new_path:
                        self.current_path = new_path
                        self.prev_pathfind_length = current_time
                        self.last_player_position = player_pos.copy()
                        self.stuck_timer = 0.0  # Reset stuck timer
                    else:
                        # Try direct pathfind to player as fallback
                        new_path = self._a_star_pathfind(enemy_pos, player_pos)
                        if new_path:
                            self.current_path = new_path
                            self.prev_pathfind_length = current_time
                            self.last_player_position = player_pos.copy()
                        else:
                            self._move_directly_to_target(player_pos, enemy_pos)
                            return
                else:
                    # No intermediate waypoint found, try direct pathfind
                    new_path = self._a_star_pathfind(enemy_pos, player_pos)
                    if new_path:
                        self.current_path = new_path
                        self.prev_pathfind_length = current_time
                        self.last_player_position = player_pos.copy()
                    else:
                        self._move_directly_to_target(player_pos, enemy_pos)
                        return
            else:
                # Normal pathfinding
                new_path = self._a_star_pathfind(enemy_pos, player_pos)
                
                # If A* succeeds, use the new path
                if new_path:
                    self.current_path = new_path
                    self.prev_pathfind_length = current_time
                    self.last_player_position = player_pos.copy()
                    if is_stuck:
                        self.stuck_timer = 0.0  # Reset stuck timer
                else:
                    # Fallback: if A* fails, use direct movement with some avoidance
                    self._move_directly_to_target(player_pos, enemy_pos)
                    # Don't update the timer so we'll try A* again sooner
                    return
        
        # If we have a path, follow it; otherwise fall back to direct movement
        if self.current_path:
            self._follow_path(enemy_pos)
        else:
            self._move_directly_to_target(player_pos, enemy_pos)

        #transition to camp if lost player
        if not self.enemy.player_seen_clearly:
            if not hasattr(self.enemy, 'lost_player_timer'):
                self.enemy.lost_player_timer = 0.0
            self.enemy.lost_player_timer += self.enemy.dt

            if self.enemy.lost_player_timer >= 5.0: #camp if havent found player in 5s
                self.enemy.state = "camp"
                self.enemy.show_state_icon("question")
                print("Enemy: Lost player during chase - camping where player was last seen...")
                self.enemy.lost_player_timer= 0.0

    def _move_directly_to_target(self, target_pos, current_pos):
        """Direct movement with simple wall avoidance - helper method when no path given"""
        direction = target_pos - current_pos
        if direction.length() <= 2:
            return
        
        # Try direct movement first
        normalized_direction = direction.normalize()
        move = normalized_direction * self.enemy.chase_speed * self.enemy.dt
        
        # Store original position to check if movement succeeded
        original_pos = current_pos.copy()
        
        # Try the movement
        self.enemy.handle_collisions(move.x, move.y)
        
        # Check if we actually moved (not stuck against wall)
        new_pos = pygame.Vector2(self.enemy.position)
        movement_distance = new_pos.distance_to(original_pos)
        
        # If we barely moved, try alternative directions
        if movement_distance < 1.0:
            # Try perpendicular directions to go around obstacles
            perpendicular_directions = [
                pygame.Vector2(-normalized_direction.y, normalized_direction.x),  # 90 degrees
                pygame.Vector2(normalized_direction.y, -normalized_direction.x),  # -90 degrees
            ]
            
            for alt_direction in perpendicular_directions:
                alt_move = alt_direction * self.enemy.chase_speed * self.enemy.dt * 0.7  # Slightly slower
                
                # Reset position and try alternative move
                self.enemy.position = original_pos.copy()
                self.enemy.handle_collisions(alt_move.x, alt_move.y)
                
                # Check if this alternative movement worked better
                alt_new_pos = pygame.Vector2(self.enemy.position)
                alt_movement_distance = alt_new_pos.distance_to(original_pos)
                
                if alt_movement_distance > movement_distance:
                    # This alternative direction worked better, keep it
                    break
                else:
                    # Reset position for next attempt
                    self.enemy.position = original_pos.copy()

    def _follow_path(self, enemy_pos):
        """Path execution helper method with improved performance"""
        if not self.current_path:
            return
        
        target = self.current_path[0]
        direction = pygame.Vector2(target) - enemy_pos
        distance = direction.length()
        
        # Use a larger threshold to reduce micro-adjustments and path thrashing
        arrival_threshold = 8  # Increased from 5 to 8 pixels
        
        # Move to next waypoint if close enough
        if distance < arrival_threshold:
            self.current_path.pop(0)
            if not self.current_path:
                return
            # Check if we have more waypoints, otherwise continue to current target
            if self.current_path:
                target = self.current_path[0]
                direction = pygame.Vector2(target) - enemy_pos
                distance = direction.length()
        
        # Move towards waypoint with minimum distance check
        if distance > 2:
            move = direction.normalize() * self.enemy.chase_speed * self.enemy.dt
            self.enemy.handle_collisions(move.x, move.y)

    

    def inspect(self):
        """Inspect behavior - enemy investigates disturbances"""        
        # If we don't have a target position, return to patrol
        if not hasattr(self.enemy, 'last_known_player_position') or self.enemy.last_known_player_position is None:
            transition_to_patrol(self.enemy)
            return
            
        target = pygame.Vector2(self.enemy.last_known_player_position)
        enemy_pos = pygame.Vector2(self.enemy.position)
        distance = target.distance_to(enemy_pos)
        
        # If we haven't reached the target position yet, move towards it
        if distance > 16:  # More than one tile away
            direction = (target - enemy_pos).normalize()
            move = direction * self.enemy.patrol_speed * self.enemy.dt
            self.enemy.handle_collisions(move.x, move.y)
            return
        
        # We've reached the target position - check what's here
        hiding_spot_type = check_hiding_spot_at_position(self.enemy.player_ref, target)
        found_something = hiding_spot_type is not None
        
        # Update wary flags and check if we should chase
        should_chase = update_wary_flags(self.enemy, hiding_spot_type, found_something)
        
        if should_chase:
            print(f"Enemy: I already suspected {hiding_spot_type}s! Found you!")
            transition_to_chase(self.enemy)
        else:
            if found_something:
                print(f"Enemy: Suspicious {hiding_spot_type}... I'll remember this.")
            else:
                print("Enemy: False alarm. Resetting suspicions.")
            
            print("Enemy: Investigation complete. Returning to patrol.")
            transition_to_patrol(self.enemy)


    # when camp ends, A* needs to be called from current pos to start of set patrol path
    def camp(self):
        """Camp behavior - enemy stays at last known player location"""
        # Placeholder: enemy stands still when camping
        # TODO: Implement camping behavior with occasional turning/looking around
        # TODO: Add timer to return to patrol after losing player for too long
        #chase from where camping if player seen
        if self.enemy.player_seen_clearly:
            self.enemy.state = "chase"
            self.enemy.show_state_icon("exclamation")
            self.enemy.last_shot_time = pygame.time.get_ticks()
            return
        if not hasattr(self.enemy, 'camp_origin') or self.enemy.camp_origin is None:
            self.enemy.camp_origin = pygame.Vector2(self.enemy.position)
            self.enemy.camp_index = 0
            self.enemy.time_camped = None
        
        #stop in tracks when lose sight of player and paces the area
        pacing = [
                pygame.Vector2(0 -80),
                pygame.Vector2(0, 80),
                pygame.Vector2(-80,0),
                pygame.Vector2(80,0),
            ]

        target = self.enemy.camp_origin + pacing[self.enemy.camp_index]
        enemy_pos = pygame.Vector2(self.enemy.position)
        direction = target - enemy_pos
        distance = direction.length()

        if distance > 1:
            direction = direction.normalize()
            speed = self.enemy.patrol_speed
            move = direction * speed * self.enemy.dt
            self.enemy.handle_collisions(move.x, move.y)
        else:
            self.enemy.camp_index += 1
            if self.enemy.camp_index >= len(pacing):
                self.enemy.time_camped = pygame.time.get_ticks()
        
        if self.enemy.camp_index >= len(pacing):
            if self.enemy.time_camped is not None:

                if pygame.time.get_ticks() - self.enemy.time_camped > 10000:
                    patrol_start = pygame.Vector2(self.enemy.patrol_path_pixels[0])
                    self.current_path = self._a_star_pathfind(self.enemy.positon, patrol_start)
                    self.enemy.state = "patrol"
                    self.enemy.camp_origin = None
                    self.enemy.camp_index = 0
                    self.enenmy.time_camped = None


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
        direction = get_closest_cardinal_direction(direction_vector)
        
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
                
        elif self.enemy.state == "camp":
            if not self.enemy.player_seen_clearly:
                if not hasattr(self.enemy, "camping_time") or self.enemy.camping_time is None:
                    self.enemy.camping_time = pygame.time.get_ticks()
                else:
                    if pygame.time.get_ticks() - self.enemy.camping_time > 5000: #5 seconds
                        self.enemy.state = "patrol"
                        self.enemy.camping_time = None
                        self.enemy.camp_origin = None
                        self.enemy.camp_index = 0
                
                

        # Reset detection flags after processing
        if not (self.enemy.player_seen_clearly or self.enemy.player_glimpsed or self.enemy.sound_heard):
            # No immediate threats detected
            pass
