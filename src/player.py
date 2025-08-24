import pygame
from bottle import BottleProjectile
import player_animator
from collision_utils import handle_full_collision

speed = 100

class Player(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__()
        self.animator = player_animator.PlayerAnimator()
        self.image = self.animator.get_current_sprite()
        self.rect = self.image.get_rect(center=position)
        # Create mask for pixel-perfect collision detection
        self.mask = pygame.mask.from_surface(self.image)
        self.position = pygame.Vector2(position)  # use float position for smooth movement
        self.moveable = True  # flag to check if player can move
        self.box = False  # flag to check if player is in a box
        self.trees = False  # flag to check if player is in trees
        self.locker = False  # flag to check if player is in a locker
        self.bottle = False  # flag to check if player has a bottle
        self.book = False  # flag to check if player has a book
        self.key1 = False  # flag to check if player has key1 (yellow key)
        self.key2 = False  # flag to check if player has key2 (blue key)
        self.speed_modifier = 1.0  # speed modifier for different terrain types
        
        # for tracking key presses
        self.z_key_pressed_last_frame = False
        
        # box animation variables
        self.box_animation_active = False
        self.box_animation_timer = 0.0
        self.box_animation_stage = 0  # 0: box_open, 1: box_middle, 2: box_closed0
        self.box_animation_speed = 0.3  # time for each stage in seconds
        
        # locker animation variables
        self.locker_animation_active = False
        self.locker_animation_timer = 0.0
        self.locker_animation_duration = 0.5  # total duration for locker open animation

# UPDATE ===============================================================================================================================

    def update(self, dt, collision_rects, enemies_group=None, overlapping_trees=False, overlapping_locker=False):
        # handle box animation if active
        if self.box_animation_active:
            self.box_animation_timer += dt
            if self.box_animation_timer >= self.box_animation_speed:
                self.box_animation_timer = 0.0
                self.box_animation_stage += 1
                
                if self.box_animation_stage >= 3:  # animation complete
                    self.box_animation_active = False
                    self.box = True  # player is now in box mode
                    self.box_animation_stage = 0
        
        # handle input and movement
        dx, dy, thrown_bottle, dropped_book_pos, dropped_box_pos = self.handle_input(dt, collision_rects, enemies_group, overlapping_trees, overlapping_locker)
        
        # update animation (always update for timing, regardless of box/trees state)
        self.animator.update(dt, dx, dy, self.box)
        
        # get the appropriate sprite based on current state
        if not self.box_animation_active:
            self.image = self.animator.get_current_sprite(self.box, self.trees, self.locker)
            self.mask = pygame.mask.from_surface(self.image)
        
        return dx, dy, thrown_bottle, dropped_book_pos, dropped_box_pos
    
    def handle_input(self, dt, collision_rects, enemies_group=None, overlapping_trees=False, overlapping_locker=False):
        keys = pygame.key.get_pressed()
        z_key_pressed_this_frame = keys[pygame.K_z]
        z_key_just_pressed = z_key_pressed_this_frame and not self.z_key_pressed_last_frame
        
        thrown_bottle = None
        dropped_book_pos = None
        dropped_box_pos = None
        
        # handle Z key for box, trees, locker, bottle, and book interaction
        if z_key_just_pressed:
            if self.box:
                # exit box if currently in box
                dropped_box_pos = self.exit_box(collision_rects, enemies_group)
            elif overlapping_trees and not self.trees:
                # enter trees
                self.enter_trees()
            elif overlapping_locker and not self.locker:
                # enter locker
                self.enter_locker()
            elif self.bottle:
                # throw bottle
                thrown_bottle = self.throw_bottle()
            elif self.book:
                # drop book
                dropped_book_pos = self.drop_book(collision_rects, enemies_group)
        
        # handle Z key hold for trees and locker
        if z_key_pressed_this_frame:
            if overlapping_trees and not self.trees:
                self.enter_trees()
            elif overlapping_locker and not self.locker:
                self.enter_locker()
        else:
            if self.trees:
                self.exit_trees()
            elif self.locker:
                self.exit_locker()
        
        # update key state for next frame
        self.z_key_pressed_last_frame = z_key_pressed_this_frame
        
        # if player is not moveable, don't process movement input
        if not self.moveable:
            return 0, 0, thrown_bottle, dropped_book_pos, dropped_box_pos
        
        # store original position
        original_x = self.position.x
        original_y = self.position.y
        
        # calculate movement deltas
        dx = 0
        dy = 0
        
        # apply speed modifier for terrain effects
        current_speed = speed * self.speed_modifier
        
        if keys[pygame.K_LEFT]:
            dx = -current_speed * dt
        if keys[pygame.K_RIGHT]:
            dx = current_speed * dt
        if keys[pygame.K_UP]:
            dy = -current_speed * dt
        if keys[pygame.K_DOWN]:
            dy = current_speed * dt
        
        # handle collisions and update position
        self.handle_collisions(dx, dy, collision_rects, enemies_group)
        
        # update rect position (for rendering)
        self.rect.center = (int(self.position.x), int(self.position.y))
        
        # return the actual movement that occurred and any thrown bottle
        actual_dx = self.position.x - original_x
        actual_dy = self.position.y - original_y
        return actual_dx, actual_dy, thrown_bottle, dropped_book_pos, dropped_box_pos
    
# HELPERS ==============================================================================================================================

    def set_speed_modifier(self, modifier):
        """Set the speed modifier for different terrain types"""
        self.speed_modifier = modifier
        
    def reset_on_death(self):
        """Reset player flags when player dies"""
        self.key1 = False
        self.key2 = False
        self.bottle = False
        self.book = False
        self.box = False
        self.trees = False
        self.locker = False
      
    def handle_collisions(self, dx, dy, collision_rects, enemies_group=None):
        """Handle player collisions using shared collision system"""
        player_size = (16, 16)
        handle_full_collision(self.position, player_size, collision_rects, enemies_group, dx, dy)

    def enter_box(self):
        """Handle player entering a box with animation sequence"""
        if not self.box:
            self.box_animation_active = True
            self.box_animation_timer = 0.0
            self.box_animation_stage = 0

    def throw_bottle(self):
        """Throw a bottle in the direction the player is facing"""
        if self.bottle:
            self.bottle = False
            bottle_pos = (self.position.x, self.position.y)
            return BottleProjectile(bottle_pos, self.animator.current_direction)
        return None

    def _get_drop_position_if_clear(self, collision_rects, enemy_group=None, item_name="item"):
        """Helper function to calculate drop position and check for collisions"""
        # calculate position one tile in front of player based on current direction
        drop_x, drop_y = self.position.x, self.position.y
        if self.animator.current_direction == "up":
            drop_y -= 16
        elif self.animator.current_direction == "down":
            drop_y += 16
        elif self.animator.current_direction == "left":
            drop_x -= 16
        elif self.animator.current_direction == "right":
            drop_x += 16
        
        # create a rect for the item at the drop position (assuming 16x16 item size)
        item_rect = pygame.Rect(drop_x - 8, drop_y - 8, 16, 16)
        
        # check for collisions with walls/objects
        collision_found = False
        for collision_rect in collision_rects:
            if item_rect.colliderect(collision_rect):
                collision_found = True
                break
        
        # check for collisions with enemies if enemy_group is provided
        if not collision_found and enemy_group:
            for enemy in enemy_group:
                if item_rect.colliderect(enemy.rect):
                    collision_found = True
                    break
        
        # return position if clear, None if blocked
        if not collision_found:
            return (drop_x, drop_y)
        else:
            return None

    def drop_book(self, collision_rects, enemy_group=None):
        """Handle player dropping a book, only if drop position is not colliding"""
        if self.book:
            drop_pos = self._get_drop_position_if_clear(collision_rects, enemy_group, "book")
            if drop_pos:
                self.book = False
                return drop_pos
        return None

    def pick_up_bottle(self):
        """Handle player picking up a bottle"""
        if not self.bottle:
            self.bottle = True

    def grab_book(self):
        """Handle player grabbing a book"""
        if not self.book:
            self.book = True

    def pick_up_key1(self):
        """Handle player picking up key1 (yellow key)"""
        if not self.key1:
            self.key1 = True

    def pick_up_key2(self):
        """Handle player picking up key2 (blue key)"""
        if not self.key2:
            self.key2 = True

    def exit_box(self, collision_rects, enemy_group=None):
        """Handle player exiting a box"""
        if self.box:
            drop_pos = self._get_drop_position_if_clear(collision_rects, enemy_group, "box")
            if drop_pos:
                self.box = False
                return drop_pos
        return None
    
    def enter_trees(self):
        if not self.trees:
            self.moveable = False
            self.trees = True
    
    def exit_trees(self):
        if self.trees:
            self.moveable = True
            self.trees = False
    
    def enter_locker(self):
        if not self.locker:
            self.locker = True
            self.moveable = False
            self.locker_animation_active = True
            self.locker_animation_timer = 0.0
    
    def exit_locker(self):
        if self.locker:
            self.moveable = True
            self.locker = False


def quit_check(running):
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        running = False
    return running
