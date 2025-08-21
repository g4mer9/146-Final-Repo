import pygame

class SoundSystem:
    """Global sound system to track audio events for AI"""
    def __init__(self):
        self.active_sounds = []  # list of active sound events
    
    def add_sound(self, position, sound_type, range_radius, duration=333):
        """Add a sound event that lasts for the specified duration (in ms)
        
        Default duration of 333ms ensures sounds don't miss the AI check window
        since enemies check for transitions every 333ms
        """
        current_time = pygame.time.get_ticks()
        sound_event = {
            'position': position,
            'type': sound_type,
            'range': range_radius,
            'start_time': current_time,
            'duration': duration
        }
        self.active_sounds.append(sound_event)
    
    def update(self):
        """Remove expired sound events"""
        current_time = pygame.time.get_ticks()
        self.active_sounds = [
            sound for sound in self.active_sounds 
            if current_time - sound['start_time'] < sound['duration']
        ]
    
    def get_sounds_in_range(self, position, hearing_range):
        """Get all active sounds within hearing range of the given position"""
        sounds_in_range = []
        for sound in self.active_sounds:
            distance = pygame.Vector2(sound['position']).distance_to(position)
            if distance <= hearing_range:
                sounds_in_range.append(sound)
        return sounds_in_range

# Global sound system instance
sound_system = SoundSystem()
