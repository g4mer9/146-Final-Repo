import pygame
import player
import tiles
import pyscroll

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

# delta time, used for frame-rate independent physics
dt = 0

# load tileset and create pyscroll map
tmx_data, map_data, collision_rects, items_data = tiles.load_tileset('data/tmx/untitled.tmx', 16)

# create the scrolling map layer
map_layer = pyscroll.BufferedRenderer(
    data=map_data,
    size=screen.get_size()
)

# create the pyscroll group (like a camera)
camera_group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=1)

# create item sprites group
items_group = pygame.sprite.Group()

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
player_start_pos = (screen.get_width() // 2, screen.get_height() // 2)
game_player = player.Player(player_start_pos)
# add player to camera group on layer 2 (above items)
camera_group.add(game_player, layer=2)

# Center camera on player initially
camera_group.center(game_player.rect.center)

# tracking variables
overlapping_trees = False

# tiles.debug_tileset(tmx_data)

# MAIN LOOP =========================================================================================================================================

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # quit game check
    running = player.quit_check(running)
    
    # check what tile the player is standing on and adjust speed
    player_center_x, player_center_y = game_player.rect.center
    current_tile_id = tiles.get_tile_id_at_position(tmx_data, player_center_x, player_center_y, 16)
    
    # adjust player speed based on tile ID
    slow_tiles = {3, 4, 5, 6, 7, 8}
    if current_tile_id in slow_tiles:
        if(game_player.box):
            game_player.set_speed_modifier(0.25) #quarter speed
        else: 
            game_player.set_speed_modifier(0.5)  # half speed
        # Debug: uncomment the line below to see when you're on a slow tile
        # print(f"On slow tile {current_tile_id}, speed halved")
    else:
        if(game_player.box):
            game_player.set_speed_modifier(0.5)  # half
        else:
            game_player.set_speed_modifier(1.0)  # normal speed
    
    # update player (handles movement, collisions, and animation)
    # pass the overlapping_trees state to the player
    dx, dy = game_player.update(dt, collision_rects, overlapping_trees)
    
    # check for item collisions (open_box and trees)
    player_rect = game_player.rect
    items_to_remove = []
    overlapping_trees = False  # reset tree overlap state each frame
    
    for item in items_group:
        if item.item_name == 'open_box':  # check for open_box specifically
            if player_rect.colliderect(item.rect):
                print(f"Player is touching the open_box at position ({item.rect.x}, {item.rect.y})")
                # Call the function to handle box interaction
                game_player.enter_box()
                # Mark item for removal
                items_to_remove.append(item)
        elif item.item_name == 'trees' or item.item_name.startswith('item_') and 'tree' in item.item_name.lower():  # check for trees specifically or items with 'tree' in name
            if player_rect.colliderect(item.rect):
                # Set overlap state instead of entering trees
                overlapping_trees = True
    
    # remove items that were interacted with
    for item in items_to_remove:
        items_group.remove(item)
        camera_group.remove(item)
    
    # center camera on player
    camera_group.center(game_player.rect.center)
    
    # draw everything (map and sprites)
    # Note: no need to fill screen, pyscroll handles clearing
    camera_group.draw(screen)

    # draw FPS counter
    fps = clock.get_fps()
    fps_text = font.render(f"FPS: {fps:.1f}", True, fps_counter_color)
    screen.blit(fps_text, (10, 10))
    screen.blit(z_button_ui, (30, 30))  # draw Z button UI
    if overlapping_trees:
        screen.blit(trees_ui, (30, 50))
    elif game_player.box:
        screen.blit(box_open_ui, (30, 50))
    


    # draw new frame
    pygame.display.flip()

    # FPS cap, also updates delta time for physics
    dt = clock.tick(60) / 1000

pygame.quit()