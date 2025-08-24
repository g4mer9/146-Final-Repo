import pygame
import random
import heapq


class EnemyBehaviors:
    """Handles enemy AI behaviors and state logic"""
    
    def __init__(self, enemy):
        self.enemy = enemy
        self.prev_pathfind_length = 0
        self.current_path = []
        self.pathfind_cooldown = 500 

    """A* with 8 directions for better agent movement"""
    def _a_star_pathfind(self, start_position, goal_position, tile_size = 32):
        start_grid = (int(start_position.x // tile_size), int(start_position.y // tile_size))
        goal_grid = (int(goal_position.x // tile_size), int(goal_position.y // tile_size))
        
        # 8-directional movement and cost
        directions = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
        diagonal_cost = 1.414
        
        priorityqueue = [(0, 0, start_grid, [(start_position.x, start_position.y)])]
        pathfinding = set()
        
        while priorityqueue:
            _, goal_cost, current, path = heapq.heappop(priorityqueue)
            
            if current in pathfinding:
                continue
            pathfinding.add(current)
            
            if current == goal_grid:
                return [pygame.Vector2(pos) for pos in path[1:]]
            
            for diagonal_x, diagonal_y in directions:
                neighbor = (current[0] + diagonal_x, current[1] + diagonal_y)
                
                if neighbor in pathfinding:
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
        Get movement cost for a tile position"""
        try:
            if not hasattr(self.enemy, 'game_map'):
                return 1  # Fallback case
            
            tile = self.enemy.game_map.get_tile(grid_x, grid_y)
            if tile is None or tile.is_wall():
                return float('inf')
            return 3 if tile.is_tile_slow() else 1
        except:
            return float('inf')



    # TODO: use A* pathfinding to player. 
    # use tile.is_tile_slow() to find slow tiles, and give them weight of 3 instead of 1. walls give weight of 100+ or inf
    def chase(self):
        """Chase behavior - enemy pursues and shoots at player now with A* pathfinding"""
        # In line of sight assault
        if self.enemy.player_seen_clearly:
            current_time = pygame.time.get_ticks()
            if current_time - self.enemy.last_shot_time >= self.enemy.shooting_cooldown:
                if bullet := self._shoot_at_player():
                    self.enemy.fired_bullets.append(bullet)
                    self.enemy.last_shot_time = current_time
        
        # Pathfinding logic
        current_time = pygame.time.get_ticks() #need curr time to check against prev_pathfind_length
        player_pos = pygame.Vector2(self.enemy.player_ref.rect.center)
        enemy_pos = pygame.Vector2(self.enemy.position)
        
        # Path recalculation if cooldown pass
        if (current_time - self.prev_pathfind_length >= self.pathfind_cooldown or not self.current_path):
            self.current_path = self._a_star_pathfind(enemy_pos, player_pos)
            self.prev_pathfind_length = current_time
            
            # Back to direct movement if no path presented
            if not self.current_path:
                self._move_directly_to_target(player_pos, enemy_pos)
                return
        
        # Follow through with path and send to helper
        self._follow_path(enemy_pos)

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
        """Direct movement - helper method when no path given"""
        direction = target_pos - current_pos
        if direction.length() > 2:
            move = direction.normalize() * self.enemy.chase_speed * self.enemy.dt
            self.enemy.handle_collisions(move.x, move.y)

    def _follow_path(self, enemy_pos):
        """Path execution helper method"""
        if not self.current_path:
            return
        
        target = self.current_path[0]
        direction = pygame.Vector2(target) - enemy_pos
        distance = direction.length()
        
        # Move to next waypoint if close enough
        if distance < 5:
            self.current_path.pop(0)
            if not self.current_path:
                return
            target = self.current_path[0]
            direction = pygame.Vector2(target) - enemy_pos
            distance = direction.length()
        
        # Move towards waypoint
        if distance > 2:
            move = direction.normalize() * self.enemy.chase_speed * self.enemy.dt
            self.enemy.handle_collisions(move.x, move.y)

    

    # TODO: start timer only after A* pathfinding towards sound/seen player and destination reached
    # keep in mind, if the destination is a player in a box, a rand call should decide whether to enter chase or return to patrol
    # (also disable player.box)
    def inspect(self):
        """Inspect behavior - enemy investigates disturbances"""
        # Placeholder: enemy stands still when investigating
        # TODO: Implement movement towards last known position/sound location
        # For now, just transition back to patrol after a delay
        if hasattr(self.enemy, 'last_known_player_position') and self.enemy.last_known_player_position is not None:
            target = pygame.Vector2(self.enemy.last_known_player_position)
            enemy_pos = pygame.Vector2(self.enemy.position)
            direction = target - enemy_pos
            distance = direction.length()
            if distance > 1:
                direction = direction.normalize()
                speed = self.enemy.patrol_speed  # same as patrol speed
                move = direction * speed * self.enemy.dt
                self.enemy.handle_collisions(move.x, move.y)
                # Reset timer until enemy arrives at camp spot
                

        if not hasattr(self.enemy, 'last_box_position'):
            self.enemy.last_box_position = pygame.Vector2(self.enemy.player_ref.rect.center)

        #checking if the enemy is inspecting the box, then chase/shoot if the box is moving  
        if self.enemy.player_ref.box:
                box_position = pygame.Vector2(self.enemy.player_ref.rect.center)

                if abs((box_position - self.enemy.last_box_position).length()) > 1: 
                    print('Enemy: Box Moved! Player is inside! Shooting and chasing!')
                    self.enemy.player_seen_clearly = True
                    self.enemy.state = "chase"
                    self.enemy.show_state_icon("exclamation")
                    self.enemy.last_known_player_position = (box_position.x, box_position.y)
                    self.enemy.box_still_timer = 0.0
                #if the box hasn't moved
                else: 
                    if not hasattr(self.enemy, 'box_timer_start') or self.enemy.box_timer_start is None:
                        self.enemy.box_timer_start = pygame.time.get_ticks()
                                     
                    elapsed_time = (pygame.time.get_ticks() - self.enemy.box_timer_start)
                    if elapsed_time >= 3000: #the box hasnt moved in a while
                        self.enemy.state = "patrol"
                        self.enemy.inspect_timer = 0.0
                        self.enemy.last_known_player_position = None
                        self.enemy.box_still_timer = 0.0
                
                self.enemy.last_box_position = box_position
                
        #counting in ms, so 3000 is 3 seconds, return to patrolling after inspecting for 3 seconds
        else:
            if not hasattr(self.enemy, 'inspect_timer_start') or self.enemy.inspect_timer_start is None:
                self.enemy.inspect_timer_start = pygame.time.get_ticks()
            elapsed_inspect_timer = (pygame.time.get_ticks() - self.enemy.inspect_timer_start)
            if elapsed_inspect_timer >= 3000:  # investigate for 3 seconds then return to patrol
                self.enemy.state = "patrol"
                self.enemy.inspect_timer = 0.0
                self.enemy.last_known_player_position = None


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
