"""
Shared movement and direction utilities
"""
import pygame


def get_direction_vector(current_direction):
    """Get direction vector from a string direction"""
    direction_map = {
        "down": pygame.Vector2(0, 1),
        "up": pygame.Vector2(0, -1),
        "left": pygame.Vector2(-1, 0),
        "right": pygame.Vector2(1, 0)
    }
    return direction_map.get(current_direction, pygame.Vector2(0, 1))


def get_closest_cardinal_direction(direction_vector):
    """Get the closest cardinal direction from a direction vector"""
    if abs(direction_vector.x) > abs(direction_vector.y):
        return "right" if direction_vector.x > 0 else "left"
    else:
        return "down" if direction_vector.y > 0 else "up"


def move_towards_target(position, target, speed, dt, collision_handler):
    """
    Move an entity towards a target position with collision handling
    
    Args:
        position: Current position (pygame.Vector2)
        target: Target position (pygame.Vector2 or tuple)
        speed: Movement speed in pixels per second
        dt: Delta time in seconds
        collision_handler: Function to call for collision handling (dx, dy)
    
    Returns:
        float: Distance remaining to target
    """
    if not isinstance(target, pygame.Vector2):
        target = pygame.Vector2(target)
    
    direction = target - position
    distance = direction.length()
    
    if distance > 2:  # Only move if not already close enough
        move = direction.normalize() * speed * dt
        collision_handler(move.x, move.y)
    
    return distance
