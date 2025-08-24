"""
Shared collision handling utilities to reduce code duplication
"""
import pygame


def handle_collision_axis(position, rect_size, collision_rects, entity_group, delta, axis='x'):
    """
    Handle collision detection and response for a single axis (x or y)
    
    Args:
        position: Current position as pygame.Vector2
        rect_size: Tuple of (width, height) for the entity
        collision_rects: List of collision rectangles
        entity_group: Group of entities to check collision with (can be None)
        delta: Movement delta for this axis
        axis: 'x' or 'y' to indicate which axis to process
    
    Returns:
        bool: True if collision was found and corrected
    """
    if delta == 0:
        return False
    
    # Update position for this axis
    if axis == 'x':
        position.x += delta
    else:
        position.y += delta
    
    # Create rect at new position
    entity_rect = pygame.Rect(
        position.x - rect_size[0]//2, 
        position.y - rect_size[1]//2, 
        rect_size[0], rect_size[1]
    )
    
    collision_found = False
    closest_pos = position.x if axis == 'x' else position.y
    
    # Check collisions with static rects
    for rect in collision_rects:
        if entity_rect.colliderect(rect):
            collision_found = True
            if axis == 'x':
                if delta > 0:  # moving right
                    closest_pos = min(closest_pos, rect.left - rect_size[0]//2)
                else:  # moving left
                    closest_pos = max(closest_pos, rect.right + rect_size[0]//2)
            else:  # y axis
                if delta > 0:  # moving down
                    closest_pos = min(closest_pos, rect.top - rect_size[1]//2)
                else:  # moving up
                    closest_pos = max(closest_pos, rect.bottom + rect_size[1]//2)
    
    # Check collisions with entity group if provided
    if entity_group:
        for entity in entity_group:
            if entity_rect.colliderect(entity.rect):
                collision_found = True
                if axis == 'x':
                    if delta > 0:  # moving right
                        closest_pos = min(closest_pos, entity.rect.left - rect_size[0]//2)
                    else:  # moving left
                        closest_pos = max(closest_pos, entity.rect.right + rect_size[0]//2)
                else:  # y axis
                    if delta > 0:  # moving down
                        closest_pos = min(closest_pos, entity.rect.top - rect_size[1]//2)
                    else:  # moving up
                        closest_pos = max(closest_pos, entity.rect.bottom + rect_size[1]//2)
    
    # Update position if collision found
    if collision_found:
        if axis == 'x':
            position.x = closest_pos
        else:
            position.y = closest_pos
    
    return collision_found


def handle_full_collision(position, rect_size, collision_rects, entity_group, dx, dy):
    """
    Handle collision detection for both x and y axes
    
    Args:
        position: Current position as pygame.Vector2 (modified in place)
        rect_size: Tuple of (width, height) for the entity
        collision_rects: List of collision rectangles
        entity_group: Group of entities to check collision with (can be None)
        dx: Horizontal movement delta
        dy: Vertical movement delta
    
    Returns:
        tuple: (collision_x, collision_y) - booleans indicating collisions on each axis
    """
    # Handle horizontal movement first
    collision_x = handle_collision_axis(position, rect_size, collision_rects, entity_group, dx, 'x')
    
    # Handle vertical movement second
    collision_y = handle_collision_axis(position, rect_size, collision_rects, entity_group, dy, 'y')
    
    return collision_x, collision_y
