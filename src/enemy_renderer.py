import pygame
import math


class EnemyRenderer:
    """Handles enemy rendering including vision cones and state icons"""
    
    def __init__(self, enemy):
        self.enemy = enemy
    
    def draw_vision_cone(self, screen, map_layer):
        """Draw a semitransparent vision cone directly on the screen"""
        # Get enemy facing direction
        facing_direction = self._get_facing_direction()
        
        # Calculate the angle of the facing direction
        facing_angle = math.degrees(math.atan2(facing_direction.y, facing_direction.x))
        
        # Calculate cone boundaries
        half_cone_angle = self.enemy.vision_cone_angle / 2
        start_angle = facing_angle - half_cone_angle
        end_angle = facing_angle + half_cone_angle
        
        # Get the actual camera position from the map layer
        camera_x, camera_y = self._get_camera_position(map_layer)
        
        # Calculate enemy's screen position using the actual camera position
        enemy_screen_x = self.enemy.position.x - camera_x
        enemy_screen_y = self.enemy.position.y - camera_y
        
        # Create points for the vision cone polygon
        points = [(enemy_screen_x, enemy_screen_y)]  # Start at enemy position
        
        # Add points along the arc of the vision cone
        num_arc_points = 20
        for i in range(num_arc_points + 1):
            angle = start_angle + (end_angle - start_angle) * (i / num_arc_points)
            angle_rad = math.radians(angle)
            
            # Calculate point on the edge of the sight range
            point_x = enemy_screen_x + self.enemy.sight_range * math.cos(angle_rad)
            point_y = enemy_screen_y + self.enemy.sight_range * math.sin(angle_rad)
            points.append((point_x, point_y))
        
        # Create a surface with per-pixel alpha for the vision cone
        cone_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(cone_surface, (255, 255, 0, 60), points)  # Semi-transparent yellow
        
        # Blit the vision cone to the screen
        screen.blit(cone_surface, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    def draw_state_icon(self, screen, map_layer):
        """Draw the current state icon above the enemy if active"""
        if not self.enemy.show_icon or not self.enemy.current_icon:
            return
            
        # Get the actual camera position from the map layer
        camera_x, camera_y = self._get_camera_position(map_layer)
        
        # Calculate enemy's screen position using the actual camera position
        enemy_screen_x = self.enemy.position.x - camera_x
        enemy_screen_y = self.enemy.position.y - camera_y
        
        # Position icon above enemy (offset by 20 pixels up)
        icon_x = enemy_screen_x - 8  # center the 16x16 icon
        icon_y = enemy_screen_y - 20  # position above enemy
        
        # Select the appropriate icon
        if self.enemy.current_icon == "exclamation":
            icon = self.enemy.exclamation_icon
        elif self.enemy.current_icon == "question":
            icon = self.enemy.question_icon
        else:
            return  # unknown icon type
            
        # Draw the icon
        screen.blit(icon, (icon_x, icon_y))
    
    def _get_facing_direction(self):
        """Get the direction the enemy is currently facing as a vector"""
        direction_map = {
            "down": pygame.Vector2(0, 1),
            "up": pygame.Vector2(0, -1),
            "left": pygame.Vector2(-1, 0),
            "right": pygame.Vector2(1, 0)
        }
        return direction_map.get(self.enemy.animator.current_direction, pygame.Vector2(0, 1))
    
    def _get_camera_position(self, map_layer):
        """Get camera position from map layer with fallback options"""
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
        
        return camera_x, camera_y
