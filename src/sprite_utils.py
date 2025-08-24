"""
Shared sprite loading utilities
"""
import pygame


def load_sprite_with_fallback(sprite_path, fallback_color=(255, 0, 255), fallback_size=(16, 16)):
    """
    Load a sprite with a fallback placeholder if loading fails
    
    Args:
        sprite_path: Path to the sprite file
        fallback_color: Color for placeholder if sprite fails to load
        fallback_size: Size of placeholder sprite
    
    Returns:
        pygame.Surface: Loaded sprite or placeholder
    """
    try:
        return pygame.image.load(sprite_path).convert_alpha()
    except pygame.error as e:
        print(f"Warning: Could not load sprite {sprite_path}: {e}")
        placeholder = pygame.Surface(fallback_size)
        placeholder.fill(fallback_color)
        return placeholder


def load_directional_sprites(base_name, directions=None, frame_count=2):
    """
    Load sprites for multiple directions and frames
    
    Args:
        base_name: Base name for sprites (e.g., "soldier")
        directions: List of directions (default: ["down", "up", "left", "right"])
        frame_count: Number of animation frames per direction
    
    Returns:
        dict: Dictionary with direction keys and lists of sprites as values
    """
    if directions is None:
        directions = ["down", "up", "left", "right"]
    
    sprites = {}
    for direction in directions:
        sprites[direction] = []
        for i in range(frame_count):
            sprite_path = f'data/sprites/{base_name}_{direction}{i}.png'
            sprite = load_sprite_with_fallback(sprite_path)
            sprites[direction].append(sprite)
    
    return sprites


def load_icon_sprites():
    """Load UI icon sprites with fallbacks"""
    icons = {}
    
    # Exclamation icon (red fallback)
    icons['exclamation'] = load_sprite_with_fallback(
        'data/sprites/exclamation.png', 
        fallback_color=(255, 0, 0)
    )
    
    # Question icon (blue fallback)
    icons['question'] = load_sprite_with_fallback(
        'data/sprites/question.png', 
        fallback_color=(0, 0, 255)
    )
    
    return icons
