import pygame
import player
import tiles
import pyscroll
from bottle import BottleProjectile

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

# create bottle projectiles group
bottle_projectiles_group = pygame.sprite.Group()

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
    
    # update player (handles movement, collisions, and animation)
    # pass the overlapping_trees state to the player
    dx, dy, thrown_bottle, dropped_book_pos, dropped_box_pos = game_player.update(dt, collision_rects, overlapping_trees)
    
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
    
    # check for item collisions (open_box and trees)
    player_rect = game_player.rect
    items_to_remove = []
    overlapping_trees = False  # reset tree overlap state each frame
    
    for item in items_group:
        if item.item_name == 'open_box':  # check for open_box specifically
            if player_rect.colliderect(item.rect):
                print(f"Player is touching the open_box at position ({item.rect.x}, {item.rect.y})")
                # call the function to handle box interaction
                game_player.enter_box()
                # mark item for removal
                items_to_remove.append(item)
        elif item.item_name == 'bottle':
            if player_rect.colliderect(item.rect):
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
        elif item.item_name == 'trees':
            if player_rect.colliderect(item.rect):
                # set overlap state instead of entering trees
                overlapping_trees = True
    
    # remove items that were interacted with
    for item in items_to_remove:
        items_group.remove(item)
        camera_group.remove(item)
    
    # center camera on player
    camera_group.center(game_player.rect.center)
    
    # draw everything (map and sprites)
    # note: no need to fill screen, pyscroll handles clearing
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
    elif game_player.book:
        screen.blit(book_ui, (30, 50))
    elif game_player.bottle:
        screen.blit(bottle_ui, (30, 50))

    # draw new frame
    pygame.display.flip()

    # FPS cap, also updates delta time for physics
    dt = clock.tick(60) / 1000

pygame.quit()