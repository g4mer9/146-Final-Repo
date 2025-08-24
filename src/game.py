import pygame
import player
import tiles
import pyscroll
from bottle import BottleProjectile, BulletProjectile
from enemy import Enemy
from sound_system import sound_system

# INITIALIZATIONS ====================================================================================================================================

pygame.init()
# screen dimensions
flags = pygame.SCALED | pygame.FULLSCREEN
screen = pygame.display.set_mode((424, 240), flags)
clock = pygame.time.Clock()
running = True

# FPS counter setup
font = pygame.font.Font(None, 18)
fps_counter_color = (255, 255, 255)  # white text
z_button_ui = pygame.image.load('data/sprites/Z.png').convert_alpha()
box_open_ui = pygame.image.load('data/sprites/box_open.png').convert_alpha()
trees_ui = pygame.image.load('data/sprites/trees.png').convert_alpha()
bottle_ui = pygame.image.load('data/sprites/bottle_up.png').convert_alpha()
book_ui = pygame.image.load('data/sprites/book.png').convert_alpha()
locker_ui = pygame.image.load('data/sprites/locker_closed.png').convert_alpha()

# load locker sprites for animation
locker_closed_sprite = pygame.image.load('data/sprites/locker_closed.png').convert_alpha()
locker_open_sprite = pygame.image.load('data/sprites/locker_open.png').convert_alpha()

# delta time, used for frame-rate independent physics
dt = 0

# load tileset and create pyscroll map
tmx_data, map_data, collision_rects, items_data, wall_tiles, slow_tiles = tiles.load_tileset('data/tmx/untitled.tmx', 16)

# Get map dimensions for pathfinding bounds
map_width = tmx_data.width
map_height = tmx_data.height

# create the scrolling map layer
map_layer = pyscroll.BufferedRenderer(
    data=map_data,
    size=screen.get_size()
)

# create the pyscroll group (like a camera)
camera_group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=1)

# create item sprites group
items_group = pygame.sprite.Group()

# create bottle projectiles group
bottle_projectiles_group = pygame.sprite.Group()

# create bullet projectiles group
bullet_projectiles_group = pygame.sprite.Group()

# create enemies group
enemies_group = pygame.sprite.Group()

# create item sprites from items data
for item_data in items_data:
    item_sprite = tiles.Item(
        pos=item_data['pos'],
        image=item_data['image'],
        item_name=item_data['name'],
        tile_id=item_data['tile_id'],
        groups=[items_group]  # only add to items_group initially
    )
    # add to camera group on layer 0 (below player)
    camera_group.add(item_sprite, layer=0)

# create player and add to camera group
player_start_tile = (24, 15)
player_start_pos = (player_start_tile[0] * 16 + 8, player_start_tile[1] * 16 + 8)
game_player = player.Player(player_start_pos)
# add player to camera group on layer 2 (above items)
camera_group.add(game_player, layer=2)

# create enemies and add to camera group
enemy_spawn_tiles = [
    (15, 30),  
    (33, 30),  
    (12, 20),  
    (36, 20),
    (32, 45),
    (15, 56),
    (12, 40),
    (36, 40)
]

# define patrol paths for each enemy (in tile coordinates)
enemy_patrol_paths = [
    [(15, 30), (15, 36), (33, 36), (33, 30), (15, 30), (15, 24), (33, 24), (33, 30)],  # enemy 0 - room 1
    [(33, 30), (33, 24), (15, 24), (15, 30), (33, 30), (33, 36), (15, 36), (15, 30)],  # enemy 1 - room 1
    [(12, 20), (12, 40), (36, 40), (36, 20)],  # enemy 2 - outside 1
    [(36, 20), (12, 20), (12, 40), (36, 40)],  # enemy 3 - outside 1
    [(32, 45), (35, 45), (35, 50), (32, 50)],  # enemy 4 - small square
    [(15, 56), (20, 56), (20, 60), (15, 60)],  # enemy 5 - square patrol
    [(12, 40), (17, 40), (17, 45), (12, 45)],  # enemy 6 - square patrol
    [(36, 40), (41, 40), (41, 35), (36, 35)]   # enemy 7 - square patrol
]

enemy_spawn_positions = [
    (tile[0] * 16 + 8, tile[1] * 16 + 8) for tile in enemy_spawn_tiles
]

for i, enemy_pos in enumerate(enemy_spawn_positions):
    patrol_path = enemy_patrol_paths[i] if i < len(enemy_patrol_paths) else enemy_patrol_paths[0]
    enemy = Enemy(enemy_pos, game_player, collision_rects, patrol_path, items_group, wall_tiles, slow_tiles, map_width, map_height)
    enemies_group.add(enemy)
    # add enemy to camera group on layer 1 (above items, below player)
    camera_group.add(enemy, layer=1)

# Center camera on player initially
camera_group.center(game_player.rect.center)

# tracking variables
overlapping_trees = False
overlapping_locker = False
animating_locker_item = None
game_won = False  # Track if the game was won

# Key and lock system - store original data for respawning
original_items_data = items_data.copy()
removed_items = []  # Track removed items for respawning on death

# Lock wall tile positions (defined by user requirements)
lock1_wall_tiles = [(64, 69), (64, 70), (64, 71), (49, 81), (50, 81), (51, 81), (23, 82), (24, 82), (25, 82)]
lock2_wall_tiles = [(65, 69), (65, 70), (65, 71), (49, 82), (50, 82), (51, 82)]
removed_wall_tiles = []  # Track removed wall tiles for respawning on death

# HELPER FUNCTIONS ================================================================================================================================

def remove_wall_tile(tile_pos):
    """Remove a wall tile from the map and collision system"""
    tile_x, tile_y = tile_pos
    
    # Calculate the world position of the tile
    world_x = tile_x * 16
    world_y = tile_y * 16
    
    # Find and remove from collision_rects - check for any rect that overlaps with this tile position
    global collision_rects
    original_count = len(collision_rects)
    collision_rects = [rect for rect in collision_rects if not (
        rect.x <= world_x < rect.x + rect.width and 
        rect.y <= world_y < rect.y + rect.height
    )]
    removed_count = original_count - len(collision_rects)
    print(f"Removed {removed_count} collision rects for tile at ({tile_x}, {tile_y})")
    
    # Store for respawning
    removed_wall_tiles.append((tile_x, tile_y, world_x, world_y))  # Store both tile and world coords
    
    # Remove from tmx data if possible (for visual changes)
    try:
        # Find the wall layer and set the tile to empty (gid = 0)
        tile_changed = False
        for layer in tmx_data.visible_layers:
            if hasattr(layer, 'data') and layer.name.lower() in ['wall', 'walls', 'collision']:
                if 0 <= tile_y < len(layer.data) and 0 <= tile_x < len(layer.data[tile_y]):
                    layer.data[tile_y][tile_x] = 0  # Set to empty tile
                    tile_changed = True
                    print(f"Removed wall tile visually at ({tile_x}, {tile_y})")
                    
        if tile_changed:
            # Recreate the map data and renderer completely to force immediate visual update
            global map_data, map_layer, camera_group
            map_data = pyscroll.TiledMapData(tmx_data)
            
            # Create a completely new BufferedRenderer
            new_map_layer = pyscroll.BufferedRenderer(
                data=map_data,
                size=screen.get_size()
            )
            
            # Update the global map_layer reference
            map_layer = new_map_layer
            
            # Create a new PyscrollGroup with the new map layer
            new_camera_group = pyscroll.PyscrollGroup(map_layer=new_map_layer, default_layer=1)
            
            # Transfer all sprites from old camera group to new one
            for sprite in camera_group.sprites():
                # Find which layer the sprite was on (this is tricky with pyscroll)
                # We'll add them back with reasonable defaults
                if hasattr(sprite, 'item_name'):  # items
                    new_camera_group.add(sprite, layer=0)
                elif sprite == game_player:  # player
                    new_camera_group.add(sprite, layer=2)
                else:  # enemies, projectiles, etc.
                    new_camera_group.add(sprite, layer=1)
            
            # Replace the camera group
            camera_group = new_camera_group
            
            # Center on player
            camera_group.center(game_player.rect.center)
            
            print(f"Completely recreated camera group for tile removal at ({tile_x}, {tile_y})")
    except Exception as e:
        print(f"Error removing wall tile visually: {e}")

def respawn_items_on_death():
    """Respawn all removed items when player dies"""
    global removed_items, removed_wall_tiles, collision_rects
    
    # Reset player flags
    game_player.reset_on_death()
    
    # Respawn items
    for item in removed_items:
        # Create new item sprite
        new_item = tiles.Item(
            pos=item.rect.topleft,
            image=item.image,
            item_name=item.item_name,
            tile_id=item.tile_id,
            groups=[items_group]
        )
        camera_group.add(new_item, layer=0)
    
    # Clear removed items list
    removed_items.clear()
    
    # Restore wall tiles
    for tile_data in removed_wall_tiles:
        if len(tile_data) == 4:  # New format: (tile_x, tile_y, world_x, world_y)
            tile_x, tile_y, world_x, world_y = tile_data
        else:  # Old format: (tile_x, tile_y)
            tile_x, tile_y = tile_data
            world_x, world_y = tile_x * 16, tile_y * 16
        
        # Add back to collision_rects
        tile_rect = pygame.Rect(world_x, world_y, 16, 16)
        collision_rects.append(tile_rect)
        print(f"Restored collision rect for tile at ({tile_x}, {tile_y})")
        
        # Restore in tmx data (this would require more complex logic to restore the original gid)
        # For now, we'll just restore collision
    
    # Clear removed wall tiles list
    removed_wall_tiles.clear()
    
    print("Items and walls respawned on death!")

# tiles.debug_tileset(tmx_data)

# MAIN LOOP =========================================================================================================================================

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # update sound system (remove expired sounds)
    sound_system.update()

    # quit game check
    running = player.quit_check(running)
    
    # check what tile the player is standing on and adjust speed
    player_center_x, player_center_y = game_player.rect.center
    
    # adjust player speed based on tile properties
    if tiles.is_tile_slow(tmx_data, player_center_x, player_center_y, 16):
        if(game_player.box):
            game_player.set_speed_modifier(0.25) #quarter speed
        else: 
            game_player.set_speed_modifier(0.5)  # half speed
        # Debug: uncomment the line below to see when you're on a slow tile
        # print(f"On slow tile, speed halved")
    else:
        if(game_player.box):
            game_player.set_speed_modifier(0.5)  # half
        else:
            game_player.set_speed_modifier(1.0)  # normal speed
    
    # check for overlapping items first (before player update)
    player_rect = game_player.rect
    overlapping_trees = False
    overlapping_locker = False
    current_locker_item = None
    
    for item in items_group:
        if item.item_name == 'trees' and player_rect.colliderect(item.rect):
            overlapping_trees = True
        elif item.item_name == 'locker' and player_rect.colliderect(item.rect):
            overlapping_locker = True
            current_locker_item = item
    
    # update player (handles movement, collisions, and animation)
    # pass the overlapping_trees and overlapping_locker state to the player
    dx, dy, thrown_bottle, dropped_book_pos, dropped_box_pos = game_player.update(dt, collision_rects, enemies_group, overlapping_trees, overlapping_locker)
    
    # update enemies
    for enemy in enemies_group:
        enemy.update(dt)
        
        # collect bullets fired by enemies
        for bullet in enemy.fired_bullets:
            bullet_projectiles_group.add(bullet)
            camera_group.add(bullet, layer=1)  # add on layer 1 (above ground, below player)
        enemy.fired_bullets.clear()  # clear the list after adding to groups
    
    # set the animating locker item when animation starts
    if game_player.locker_animation_active and current_locker_item and not animating_locker_item:
        animating_locker_item = current_locker_item
    
    # handle locker animation (use persistent animating_locker_item)
    if game_player.locker_animation_active and animating_locker_item:
        game_player.locker_animation_timer += dt
        if game_player.locker_animation_timer < game_player.locker_animation_duration * 0.5:
            # first half: show locker_open
            animating_locker_item.image = locker_open_sprite
        elif game_player.locker_animation_timer < game_player.locker_animation_duration:
            # second half: show locker_closed
            animating_locker_item.image = locker_closed_sprite
        else:
            # animation finished, reset to closed and clear the animating item
            animating_locker_item.image = locker_closed_sprite
            game_player.locker_animation_active = False
            animating_locker_item = None
    
    # handle thrown bottle
    if thrown_bottle:
        bottle_projectiles_group.add(thrown_bottle)
        camera_group.add(thrown_bottle, layer=1)  # add on layer 1 (above ground, below player)
    
    # handle dropped book
    if dropped_book_pos:
        # create a new book item at the drop position
        try:
            book_image = pygame.image.load('data/sprites/book.png').convert_alpha()
            book_item = tiles.Item(
                pos=dropped_book_pos,
                image=book_image,
                item_name='book',
                tile_id=0,  # assuming book doesn't have a specific tile_id
                groups=[items_group]
            )
            # add to camera group on layer 0 (below player)
            camera_group.add(book_item, layer=0)
            print(f"Book dropped at position ({dropped_book_pos[0]}, {dropped_book_pos[1]})")
        except pygame.error as e:
            print(f"Error loading book image: {e}")
    
    # handle dropped box
    if dropped_box_pos:
        # create a new box item at the drop position
        try:
            box_image = pygame.image.load('data/sprites/box_open.png').convert_alpha()
            box_item = tiles.Item(
                pos=dropped_box_pos,
                image=box_image,
                item_name='open_box',
                tile_id=0,  # assuming box doesn't have a specific tile_id
                groups=[items_group]
            )
            # add to camera group on layer 0 (below player)
            camera_group.add(box_item, layer=0)
            print(f"Box dropped at position ({dropped_box_pos[0]}, {dropped_box_pos[1]})")
        except pygame.error as e:
            print(f"Error loading box image: {e}")
    
    # handle thrown bottle
    if thrown_bottle:
        bottle_projectiles_group.add(thrown_bottle)
        camera_group.add(thrown_bottle, layer=1)  # add on layer 1 (above ground, below player)
    
    # update bottle projectiles
    bottles_to_remove = []
    for bottle in bottle_projectiles_group:
        # check if bottle hit something
        if bottle.update(dt, collision_rects):
            bottles_to_remove.append(bottle)
    
    # remove bottles that hit walls
    for bottle in bottles_to_remove:
        bottle_projectiles_group.remove(bottle)
        camera_group.remove(bottle)
    
    # update bullet projectiles
    bullets_to_remove = []
    for bullet in bullet_projectiles_group:
        # check if bullet hit something
        collision_result = bullet.update(dt, collision_rects, game_player)
        if collision_result == "player_hit":
            # Player was hit by bullet - reset the game
            print("Player hit by bullet! Resetting game...")
            # Reset player position
            game_player.position = pygame.Vector2(player_start_pos)
            game_player.rect.center = player_start_pos
            game_player.moveable = True
            game_player.speed_modifier = 1.0
            game_player.box_animation_active = False
            game_player.locker_animation_active = False
            
            # Respawn all items and walls
            respawn_items_on_death()
            
            # Remove all bullets
            for b in bullet_projectiles_group:
                camera_group.remove(b)
            bullet_projectiles_group.empty()
            # Remove all bottle projectiles
            for bottle in bottle_projectiles_group:
                camera_group.remove(bottle)
            bottle_projectiles_group.empty()
            # Reset all enemies to their starting positions and states
            for i, enemy in enumerate(enemies_group):
                # Reset position
                enemy.position = pygame.Vector2(enemy_spawn_positions[i])
                enemy.rect.center = enemy_spawn_positions[i]
                
                # Reset state machine
                enemy.state = "patrol"
                enemy.path = []
                
                # Reset patrol path - restore original patrol path for this enemy
                patrol_path = enemy_patrol_paths[i] if i < len(enemy_patrol_paths) else enemy_patrol_paths[0]
                enemy.patrol_path_tiles = patrol_path
                enemy.patrol_index = 0
                enemy._convert_patrol_path_to_pixels()
                
                # Reset detection flags
                enemy.player_seen_clearly = False
                enemy.player_glimpsed = False
                enemy.sound_heard = False
                enemy.book_spotted = False
                enemy.last_known_player_position = None
                enemy.distraction_position = None
                
                # Reset combat
                enemy.fired_bullets.clear()
                enemy.last_shot_time = 0
                
                # Reset AI timing
                enemy.last_AI_check = 0
                
                # Reset icons
                enemy.show_icon = False
                enemy.icon_timer = 0.0
                enemy.current_icon = None
                
                # Reset all behavior timers
                if hasattr(enemy, 'inspect_timer'):
                    enemy.inspect_timer = 0.0
                if hasattr(enemy, 'distracted_timer'):
                    enemy.distracted_timer = 0.0
                
                # Reset animator to default state
                enemy.animator.current_direction = "down"
                enemy.animator.current_frame_index = 0
                enemy.animator.animation_timer = 0.0
                enemy.image = enemy.sprites["down"][0]
            bullets_to_remove.clear()
            break
        elif collision_result == "wall_hit":
            bullets_to_remove.append(bullet)
    
    # remove bullets that hit walls
    for bullet in bullets_to_remove:
        bullet_projectiles_group.remove(bullet)
        camera_group.remove(bullet)
    
    # check for item collisions (open_box, bottle, book, keys, locks - trees and locker handled above)
    player_rect = game_player.rect
    items_to_remove = []
    
    for item in items_group:
        if item.item_name == 'open_box':  # check for open_box specifically
            if player_rect.colliderect(item.rect):
                print(f"Player is touching the open_box at position ({item.rect.x}, {item.rect.y})")
                # call the function to handle box interaction
                game_player.enter_box()
                # mark item for removal
                items_to_remove.append(item)
        elif item.item_name == 'bottle':
            if player_rect.colliderect(item.rect) and not game_player.bottle:
                print(f"Player is touching the bottle at position ({item.rect.x}, {item.rect.y})")
                # call the function to handle bottle interaction
                game_player.pick_up_bottle()
                # mark item for removal
                items_to_remove.append(item)
        elif item.item_name == 'book':
            if player_rect.colliderect(item.rect):
                print(f"Player is touching the book at position ({item.rect.x}, {item.rect.y})")
                # call the function to handle book interaction
                game_player.grab_book()
                # mark item for removal
                items_to_remove.append(item)
        elif item.item_name == 'key1':
            if player_rect.colliderect(item.rect) and not game_player.key1:
                print(f"Player picked up key1 (yellow key) at position ({item.rect.x}, {item.rect.y})")
                game_player.pick_up_key1()
                # store for respawning on death
                removed_items.append(item)
                items_to_remove.append(item)
        elif item.item_name == 'key2':
            if player_rect.colliderect(item.rect) and not game_player.key2:
                print(f"Player picked up key2 (blue key) at position ({item.rect.x}, {item.rect.y})")
                game_player.pick_up_key2()
                # store for respawning on death
                removed_items.append(item)
                items_to_remove.append(item)
        elif item.item_name == 'lock1':
            if player_rect.colliderect(item.rect) and game_player.key1:
                print(f"Player unlocked lock1 with key1 at position ({item.rect.x}, {item.rect.y})")
                # remove lock and corresponding wall tiles
                removed_items.append(item)
                items_to_remove.append(item)
                # remove wall tiles for lock1
                for tile_pos in lock1_wall_tiles:
                    remove_wall_tile(tile_pos)
        elif item.item_name == 'lock2':
            if player_rect.colliderect(item.rect) and game_player.key2:
                print(f"Player unlocked lock2 with key2 at position ({item.rect.x}, {item.rect.y})")
                # remove lock and corresponding wall tiles
                removed_items.append(item)
                items_to_remove.append(item)
                # remove wall tiles for lock2
                for tile_pos in lock2_wall_tiles:
                    remove_wall_tile(tile_pos)
        elif item.item_name == 'win':
            if player_rect.colliderect(item.rect):
                print(f"Player reached the win condition at position ({item.rect.x}, {item.rect.y})")
                # End the main game loop
                game_won = True
                running = False
        # Note: trees and locker items are not removed, only used for overlap detection
    
    # remove items that were interacted with
    for item in items_to_remove:
        items_group.remove(item)
        camera_group.remove(item)
    
    # center camera on player
    camera_group.center(game_player.rect.center)
    
    # draw everything (map and sprites)
    # note: no need to fill screen, pyscroll handles clearing
    camera_group.draw(screen)
    
    # Draw vision cones for enemies (after drawing sprites but before UI)
    for enemy in enemies_group:
        enemy.draw_vision_cone(screen, map_layer)
        enemy.draw_state_icon(screen, map_layer)

    # draw FPS counter
    fps = clock.get_fps()
    fps_text = font.render(f"FPS: {fps:.1f}", True, fps_counter_color)
    screen.blit(fps_text, (10, 10))
    screen.blit(z_button_ui, (30, 30))  # draw Z button UI
    if overlapping_trees and not game_player.box:
        screen.blit(trees_ui, (30, 50))
    elif overlapping_locker and not game_player.box:
        screen.blit(locker_ui, (30, 50))
    elif game_player.box:
        screen.blit(box_open_ui, (30, 50))
    elif game_player.book:
        screen.blit(book_ui, (30, 50))
    elif game_player.bottle:
        screen.blit(bottle_ui, (30, 50))

    # draw new frame
    pygame.display.flip()

    # FPS cap, also updates delta time for physics
    dt = clock.tick(60) / 1000

# WIN SCREEN ========================================================================================================================================

# Check if the game ended due to win condition
if game_won:
    # Win screen loop
    win_running = True
    win_font = pygame.font.Font(None, 48)
    win_text = win_font.render("YOU WIN!", True, (255, 255, 255))
    win_text_rect = win_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    
    instruction_font = pygame.font.Font(None, 24)
    instruction_text = instruction_font.render("Press ESC to quit", True, (255, 255, 255))
    instruction_rect = instruction_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 50))
    
    while win_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                win_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    win_running = False
        
        # Fill screen with black
        screen.fill((0, 0, 0))
        
        # Draw win text
        screen.blit(win_text, win_text_rect)
        screen.blit(instruction_text, instruction_rect)
        
        # Update display
        pygame.display.flip()
        
        # Control frame rate
        clock.tick(60)

pygame.quit()