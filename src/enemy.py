import pygame
import math
import random
from heapq import heappop, heappush # for A*
import tiles
from sound_system import sound_system

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

        # ADJUSTABLE ENEMY PARAMETERS =====================================================
        self.hearing_range = 120      # range in pixels for hearing sounds (adjustable)
        self.sight_range = 60       # range in pixels for vision cone (adjustable)
        self.vision_cone_angle = 60  # total angle of vision cone in degrees (adjustable)
        self.attack_range = 5
        self.bullet_speed = 15
        self.ms_between_AI_checks = 333
        self.last_AI_check = 0

        # vision and detection states
        self.player_seen_clearly = False
        self.player_glimpsed = False
        self.sound_heard = False
        self.last_known_player_position = None

        # ADD NEW STATES HERE============================================================================================================================
        self.state = "patrol"
        self.states = {
            "patrol": self.patrol,
            "chase": self.chase,
            "inspect": self.inspect,
            "distracted": self.distracted,
            "camp": self.camp
        }
        
        # Store dt for use in behaviors
        self.dt = 0

        self.load_sprites()
        self.image = self.sprites["down"][0]
        self.rect = self.image.get_rect(center=self.position)

    def load_sprites(self):
        """Load enemy sprite images"""
        self.sprites = {}
        directions = ["down", "up", "left", "right"]
        for direction in directions:
            self.sprites[direction] = []
            for i in range(2):  # soldier sprites only have 0 and 1
                try:
                    sprite_path = f'data/sprites/soldier_{direction}{i}.png'
                    sprite = pygame.image.load(sprite_path).convert_alpha()
                    self.sprites[direction].append(sprite)
                except pygame.error as e:
                    print(f"Warning: Could not load sprite {sprite_path}: {e}")
                    # create a placeholder if sprite is missing
                    placeholder = pygame.Surface((16, 16))
                    placeholder.fill((255, 0, 255))  # magenta placeholder
                    self.sprites[direction].append(placeholder)

# BEHAVIORS=====================================================================================================================================

    # implement later for A*
    def follow_path(self, dt):
        # For now, movement is handled in patrol(), so just return the last move
        return 0, 0

    # mostly implemented patrol state for testing
    # in full version, random paths won't be used
    def patrol(self):
        # If no patrol path, generate a new random path
        if not self.path:
            self.generate_random_patrol_path()
        # Move towards the next point in the path
        if self.path:
            target = self.path[0]
            direction = pygame.Vector2(target) - self.position
            distance = direction.length()
            if distance < 2:
                # Arrived at this point, pop it
                self.path.pop(0)
            else:
                direction = direction.normalize()
                speed = 50  # basic patrol speed
                move = direction * speed * self.dt
                # Use collision handling instead of direct position update
                self.handle_collisions(move.x, move.y)


    # chase happens when the player is found
    def chase(self):
        # Placeholder: enemy stands still when chasing
        # TODO: Implement actual chase behavior with pathfinding to player
        pass

    # inspect happens when the enemy is curious about a noise or movement
    def inspect(self):
        # Placeholder: enemy stands still when investigating
        # TODO: Implement movement towards last known position/sound location
        # For now, just transition back to patrol after a delay
        if not hasattr(self, 'inspect_timer'):
            self.inspect_timer = 0.0
        
        self.inspect_timer += self.dt
        if self.inspect_timer >= 3.0:  # investigate for 3 seconds then return to patrol
            self.state = "patrol"
            self.inspect_timer = 0.0
            self.last_known_player_position = None

    # camp happens after the enemy loses sight of the player
    # the enemy stays in the player's last known location, occasionally turning to look around
    def camp(self):
        # Placeholder: enemy stands still when camping
        # TODO: Implement camping behavior with occasional turning/looking around
        # TODO: Add timer to return to patrol after losing player for too long
        pass

    # only possible from the camp or patrol states
    # triggered by seeing a book in their path
    # they return to their previous state after x seconds have passed (30?) 
    def distracted(self):
        # Placeholder: enemy stands still when distracted
        # TODO: Implement distraction behavior (moving towards book, reading it)
        # TODO: Add timer to return to previous state after 30 seconds
        if not hasattr(self, 'distracted_timer'):
            self.distracted_timer = 0.0
        
        self.distracted_timer += self.dt
        if self.distracted_timer >= 30.0:  # distracted for 30 seconds then return to patrol
            self.state = "patrol"
            self.distracted_timer = 0.0

# AI STUFF============================================================================================================================

    # for HFSM 
    # called 3 times a second, should call helper functions that check sight, hearing
    def check_transitions(self):
        # Update vision and hearing
        self.check_sight()
        self.check_hearing()
        
        # State transition logic
        if self.state == "patrol":
            if self.player_seen_clearly:
                self.state = "chase"
                print("Enemy: Spotted player clearly - entering chase mode!")
            elif self.player_glimpsed or self.sound_heard:
                self.state = "inspect"
                if self.player_glimpsed:
                    print("Enemy: Caught a glimpse of something - investigating...")
                if self.sound_heard:
                    print("Enemy: Heard a sound - investigating...")
        
        elif self.state == "inspect":
            if self.player_seen_clearly:
                self.state = "chase"
                print("Enemy: Found the target - entering chase mode!")
            # inspect state will automatically return to patrol when reaching investigation point
        
        elif self.state == "chase":
            # Add logic for losing the player and transitioning to camp or patrol
            if not self.player_seen_clearly:
                # Could add a timer here before transitioning to camp
                pass
        
        # Reset detection flags after processing
        if not (self.player_seen_clearly or self.player_glimpsed or self.sound_heard):
            # No immediate threats detected
            pass

    # Check if the enemy can see the player
    def check_sight(self):
        self.player_seen_clearly = False
        self.player_glimpsed = False
        
        # Get player position
        player_pos = pygame.Vector2(self.player_ref.rect.center)
        enemy_pos = pygame.Vector2(self.position)
        
        # Calculate distance to player
        distance_to_player = enemy_pos.distance_to(player_pos)
        
        # Check if player is within sight range
        if distance_to_player > self.sight_range:
            return
        
        # Check if player is at the exact same position (distance is zero)
        if distance_to_player < 0.1:  # very close or same position
            # Player is right on top of enemy - definitely seen clearly
            self.player_seen_clearly = True
            self.last_known_player_position = player_pos.copy()
            return
        
        # Calculate direction to player
        direction_to_player = (player_pos - enemy_pos).normalize()
        
        # Get enemy facing direction
        enemy_facing = self.get_facing_direction()
        
        # Calculate angle between enemy facing direction and direction to player
        angle_to_player = math.degrees(math.atan2(direction_to_player.y, direction_to_player.x))
        enemy_facing_angle = math.degrees(math.atan2(enemy_facing.y, enemy_facing.x))
        
        # Normalize angles to 0-360 range
        angle_diff = abs(angle_to_player - enemy_facing_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        # Check if player is within vision cone
        if angle_diff <= self.vision_cone_angle / 2:
            # Player is in vision cone, now check for line of sight
            if self.has_line_of_sight(enemy_pos, player_pos):
                # Player is clearly visible - check if they're hidden
                if self.player_ref.trees or self.player_ref.locker or self.player_ref.box:
                    # Player is hidden but we caught a glimpse
                    self.player_glimpsed = True
                else:
                    # Player is clearly seen
                    self.player_seen_clearly = True
                    self.last_known_player_position = (player_pos.x, player_pos.y)
    
    def get_facing_direction(self):
        """Get the direction the enemy is currently facing as a vector"""
        direction_map = {
            "down": pygame.Vector2(0, 1),
            "up": pygame.Vector2(0, -1),
            "left": pygame.Vector2(-1, 0),
            "right": pygame.Vector2(1, 0)
        }
        return direction_map.get(self.animator.current_direction, pygame.Vector2(0, 1))
    
    def has_line_of_sight(self, start_pos, end_pos):
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
            for collision_rect in self.collision_rects:
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

    def draw_vision_cone(self, screen, map_layer):
        """Draw a semitransparent vision cone directly on the screen"""
        # Get enemy facing direction
        facing_direction = self.get_facing_direction()
        
        # Calculate the angle of the facing direction
        facing_angle = math.degrees(math.atan2(facing_direction.y, facing_direction.x))
        
        # Calculate cone boundaries
        half_cone_angle = self.vision_cone_angle / 2
        start_angle = facing_angle - half_cone_angle
        end_angle = facing_angle + half_cone_angle
        
        # Get the actual camera position from the map layer
        # Try different ways to access the camera position
        try:
            camera_x = map_layer.view_rect.x
            camera_y = map_layer.view_rect.y
        except AttributeError:
            try:
                camera_x = map_layer.map_rect.x
                camera_y = map_layer.map_rect.y
            except AttributeError:
                # Fallback: use the rect position directly
                camera_x = getattr(map_layer, '_camera_x', 0)
                camera_y = getattr(map_layer, '_camera_y', 0)
        
        # Calculate enemy's screen position using the actual camera position
        enemy_screen_x = self.position.x - camera_x
        enemy_screen_y = self.position.y - camera_y
        
        # Create points for the vision cone polygon
        points = [(enemy_screen_x, enemy_screen_y)]  # Start at enemy position
        
        # Add points along the arc of the vision cone
        num_arc_points = 20
        for i in range(num_arc_points + 1):
            angle = start_angle + (end_angle - start_angle) * (i / num_arc_points)
            angle_rad = math.radians(angle)
            
            # Calculate point on the edge of the sight range
            point_x = enemy_screen_x + self.sight_range * math.cos(angle_rad)
            point_y = enemy_screen_y + self.sight_range * math.sin(angle_rad)
            points.append((point_x, point_y))
        
        # Create a surface with per-pixel alpha for the vision cone
        cone_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(cone_surface, (255, 255, 0, 60), points)  # Semi-transparent yellow
        
        # Blit the vision cone to the screen
        screen.blit(cone_surface, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # Check if the enemy can hear a thrown bottle (bottle sounds must last 333 ms so that it doesn't miss the hearing window)
    def check_hearing(self):
        self.sound_heard = False
        
        # Get all sounds within hearing range
        sounds_in_range = sound_system.get_sounds_in_range(self.position, self.hearing_range)
        
        for sound in sounds_in_range:
            if sound['type'] == 'bottle_break':
                self.sound_heard = True
                self.last_known_player_position = sound['position']
                break

    def handle_collisions(self, dx, dy):
        """Handle enemy collisions with walls, similar to player collision handling"""
        enemy_size = (16, 16)
        
        # Store original position in case we need to revert
        original_x = self.position.x
        original_y = self.position.y
        
        # Handle horizontal movement first
        if dx != 0:
            self.position.x += dx
            enemy_rect = pygame.Rect(self.position.x - enemy_size[0]//2, 
                                   self.position.y - enemy_size[1]//2, 
                                   enemy_size[0], enemy_size[1])
            
            # Check for horizontal collisions
            collision_found = False
            closest_x = self.position.x
            
            for rect in self.collision_rects:
                if enemy_rect.colliderect(rect):
                    collision_found = True
                    if dx > 0:  # moving right
                        closest_x = min(closest_x, rect.left - enemy_size[0]//2)
                    else:  # moving left
                        closest_x = max(closest_x, rect.right + enemy_size[0]//2)
            
            # Check for player collision
            if enemy_rect.colliderect(self.player_ref.rect):
                collision_found = True
                if dx > 0:  # moving right
                    closest_x = min(closest_x, self.player_ref.rect.left - enemy_size[0]//2)
                else:  # moving left
                    closest_x = max(closest_x, self.player_ref.rect.right + enemy_size[0]//2)
            
            if collision_found:
                self.position.x = closest_x
                # If collision detected, skip to next patrol point
                if self.path:
                    self.path.pop(0)
        
        # Handle vertical movement second
        if dy != 0:
            self.position.y += dy
            enemy_rect = pygame.Rect(self.position.x - enemy_size[0]//2, 
                                   self.position.y - enemy_size[1]//2, 
                                   enemy_size[0], enemy_size[1])
            
            # Check for vertical collisions
            collision_found = False
            closest_y = self.position.y
            
            for rect in self.collision_rects:
                if enemy_rect.colliderect(rect):
                    collision_found = True
                    if dy > 0:  # moving down
                        closest_y = min(closest_y, rect.top - enemy_size[1]//2)
                    else:  # moving up
                        closest_y = max(closest_y, rect.bottom + enemy_size[1]//2)
            
            # Check for player collision
            if enemy_rect.colliderect(self.player_ref.rect):
                collision_found = True
                if dy > 0:  # moving down
                    closest_y = min(closest_y, self.player_ref.rect.top - enemy_size[1]//2)
                else:  # moving up
                    closest_y = max(closest_y, self.player_ref.rect.bottom + enemy_size[1]//2)
            
            if collision_found:
                self.position.y = closest_y
                # If collision detected, skip to next patrol point
                if self.path:
                    self.path.pop(0)
        
        # Update rect position
        self.rect.center = (int(self.position.x), int(self.position.y))

    # debug only function. comment out when done
    def generate_random_patrol_path(self):
        # Generate a random walkable path of 3-5 points within the map bounds
        import random
        # Map bounds (hardcoded for now, should match your map size)
        min_x, max_x = 32, 400
        min_y, max_y = 32, 200
        num_points = random.randint(3, 5)
        self.path = []
        for _ in range(num_points):
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            self.path.append((x, y))

# UPDATE=============================================================================================================================

    def update(self, dt):
        self.update_state_machine(dt)
        # For now, dx/dy are not used, but keep for animator compatibility
        dx, dy = 0, 0
        # If moving, calculate dx/dy for animation
        if self.path:
            target = self.path[0]
            direction = pygame.Vector2(target) - self.position
            if direction.length() > 1:
                direction = direction.normalize()
                speed = 50
                move = direction * speed * dt
                dx, dy = move.x, move.y
        self.animator.update(self, dt, dx, dy)
        # Update the sprite image
        self.image = self.animator.get_current_sprite(self.sprites)

    def update_state_machine(self, dt):
        # Store dt for use in behaviors
        self.dt = dt
        
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
        self.animation_speed = 0.3  # time between frames in seconds
        self.current_frame_index = 0
        # animation sequence for soldier sprites: 0, 1, 0, 1...
        self.animation_sequence = [0, 1]

# ANIMATOR UPDATE ======================================================================================================================================

    def update(self, enemy, dt, dx, dy):
        # determine if enemy is moving
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
    
    def get_current_sprite(self, sprites):
        if self.is_moving:
            # use animation sequence when moving
            frame_number = self.animation_sequence[self.current_frame_index]
        else:
            # use frame 0 when idle
            frame_number = 0
        
        return sprites[self.current_direction][frame_number]