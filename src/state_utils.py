"""
Shared state management utilities for enemy behaviors
"""


def check_hiding_spot_at_position(player_ref, target_pos, tolerance=32):
    """
    Check what type of hiding spot (if any) the player is using at the target position
    
    Args:
        player_ref: Reference to the player object
        target_pos: Target position to check (pygame.Vector2 or tuple)
        tolerance: Distance tolerance in pixels (default 32 = 2 tiles)
    
    Returns:
        str or None: "box", "trees", "locker", or None if no hiding spot found
    """
    import pygame
    
    # Convert target_pos to Vector2 if it's a tuple
    if not isinstance(target_pos, pygame.Vector2):
        target_pos = pygame.Vector2(target_pos)
    
    player_pos = pygame.Vector2(player_ref.rect.center)
    
    # Check if player is close enough to the target position
    if player_pos.distance_to(target_pos) > tolerance:
        return None
    
    # Check what hiding spot the player is using
    if player_ref.box:
        return "box"
    elif player_ref.trees:
        return "trees"
    elif player_ref.locker:
        return "locker"
    
    return None


def update_wary_flags(enemy, hiding_spot_type, found_something):
    """
    Update enemy wary flags based on inspection results
    
    Args:
        enemy: Enemy object with wary flags
        hiding_spot_type: Type of hiding spot found ("box", "trees", "locker", or None)
        found_something: Whether something was found at the location
    
    Returns:
        bool: True if enemy should enter chase (was already wary), False otherwise
    """
    if not found_something:
        # Nothing found - reset all wary flags
        enemy.wary_of_boxes = False
        enemy.wary_of_trees = False
        enemy.wary_of_lockers = False
        return False
    
    # Something was found - check wary state and update accordingly
    if hiding_spot_type == "box":
        if enemy.wary_of_boxes:
            return True  # Already wary - enter chase
        else:
            enemy.wary_of_boxes = True
            return False  # First time - become wary
            
    elif hiding_spot_type == "trees":
        if enemy.wary_of_trees:
            return True  # Already wary - enter chase
        else:
            enemy.wary_of_trees = True
            return False  # First time - become wary
            
    elif hiding_spot_type == "locker":
        if enemy.wary_of_lockers:
            return True  # Already wary - enter chase
        else:
            enemy.wary_of_lockers = True
            return False  # First time - become wary
    
    return False


def transition_to_chase(enemy):
    """
    Transition enemy to chase state with proper setup
    """
    import pygame
    
    enemy.state = "chase"
    enemy.show_state_icon("exclamation")
    enemy.player_seen_clearly = True
    enemy.last_shot_time = pygame.time.get_ticks()
    
    # Clear inspect cooldown when entering chase (clear sight overrides cooldown)
    if hasattr(enemy, 'inspect_cooldown_start'):
        enemy.inspect_cooldown_start = None


def transition_to_patrol(enemy):
    """
    Transition enemy to patrol state with cleanup
    """
    enemy.state = "patrol"
    enemy.last_known_player_position = None
    
    # Reset any timers
    if hasattr(enemy, 'inspect_timer_start'):
        enemy.inspect_timer_start = None
    if hasattr(enemy, 'box_timer_start'):
        enemy.box_timer_start = None
    if hasattr(enemy, 'hiding_spot_timer'):
        enemy.hiding_spot_timer = None
    if hasattr(enemy, 'investigating_hiding_spot'):
        enemy.investigating_hiding_spot = None
    # Note: Don't clear inspect_cooldown_start here as it needs to persist
