import pygame, sys
from pytmx.util_pygame import load_pygame
import pyscroll

# built off code from very helpful youtube tutorial:
# https://www.youtube.com/watch?v=N6xqCwblyiw
# https://pastebin.com/dEUVdNip

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, image, groups):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)
        # i think later we can plug in cost for A* right here

class Item(pygame.sprite.Sprite):
    def __init__(self, pos, image, item_name, tile_id, groups):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)
        self.item_name = item_name
        self.tile_id = tile_id

def load_tileset(filename, tile_size):
    tmx_data = load_pygame(filename)
    collision_tiles = []
    items = []

    # print(f"Loading tileset from {filename}")
    
    # # debug tileset information
    # for tileset in tmx_data.tilesets:
    #     print(f"Tileset '{tileset.name}': firstgid={tileset.firstgid}")
    
    # Create efficient lookup dictionaries for tile properties
    wall_tiles = {}  # Dictionary: (tile_x, tile_y) -> True if wall
    slow_tiles = {}  # Dictionary: (tile_x, tile_y) -> True if slow
    
    # get all collision data once
    try:
        colliders_gen = tmx_data.get_tile_colliders()
        all_colliders = list(colliders_gen)
        # print(f"Found collision data for {len(all_colliders)} tiles")
    except Exception as e:
        print(f"Error getting colliders: {e}")
        all_colliders = []

    # create a lookup table for collision data by tile GID
    # this automatically works with any tiles that have collision objects defined in the TSX
    collision_lookup = {}
    for tile_id, object_group in all_colliders:
        collision_objects = []
        if hasattr(object_group, '__iter__'):
            for obj in object_group:
                if hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'width') and hasattr(obj, 'height'):
                    collision_objects.append(obj)
        if collision_objects:
            collision_lookup[tile_id] = collision_objects

    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):
            collision_count = 0
            gids_in_layer = set()
            for x, y, image in layer.tiles():
                if image:  # only process non-empty tiles
                    pos = (x * tile_size, y * tile_size)
                    
                    # get the tile GID from the layer data
                    gid = layer.data[y][x] if y < len(layer.data) and x < len(layer.data[y]) else 0
                    if gid > 0:
                        gids_in_layer.add(gid)
                        
                        # Check tile properties and populate lookup dictionaries
                        tile_properties = tmx_data.get_tile_properties_by_gid(gid)
                        if tile_properties:
                            # Check for wall property
                            if tile_properties.get('wall', False):
                                wall_tiles[(x, y)] = True
                            
                            # Check for slow property  
                            if tile_properties.get('slow', False):
                                slow_tiles[(x, y)] = True
                        
                        if gid in collision_lookup:
                            # process collision objects for this tile
                            for obj in collision_lookup[gid]:
                                # convert tile-relative coordinates to world coordinates
                                collision_rect = pygame.Rect(
                                    pos[0] + obj.x,
                                    pos[1] + obj.y,
                                    obj.width,
                                    obj.height
                                )
                                collision_tiles.append(collision_rect)
                                collision_count += 1
                        
            # if collision_count > 0:
            #     print(f"Layer '{layer.name}' loaded {collision_count} collision objects")
            
    # print(f"Total collision rectangles: {len(collision_tiles)}")
    
    for obj in tmx_data.objects:
        pos = obj.x, obj.y
        if (hasattr(obj, 'properties') and obj.properties.get('collision', False)):
            collision_tiles.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
    
    # process items from the 'Items' object layer
    try:
        items_layer = tmx_data.get_layer_by_name('Items')
        if items_layer:
            for obj in items_layer:
                if hasattr(obj, 'gid') and obj.gid:  # tile objects with gid
                    # get the image for this tile
                    tile_image = tmx_data.get_tile_image_by_gid(obj.gid)
                    if tile_image:
                        item_data = {
                            'pos': (obj.x, obj.y),
                            'image': tile_image,
                            'name': getattr(obj, 'name', f'item_{obj.gid}'),
                            'tile_id': obj.gid,
                            'rect': pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                        }
                        items.append(item_data)
                        # print(f"Loaded tile item: name='{item_data['name']}', pos={item_data['pos']}, gid={obj.gid}")
                elif hasattr(obj, 'name') and obj.name:  # rectangle objects with names
                    # create a placeholder image for rectangle objects
                    placeholder_image = pygame.Surface((obj.width, obj.height), pygame.SRCALPHA)
                    placeholder_image.fill((0, 0, 0, 0))  # semi-transparent green
                    
                    item_data = {
                        'pos': (obj.x, obj.y),
                        'image': placeholder_image,
                        'name': obj.name,
                        'tile_id': 0,  # no tile ID for rectangles
                        'rect': pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    }
                    items.append(item_data)
                    # print(f"Loaded rectangle item: name='{item_data['name']}', pos={item_data['pos']}, size=({obj.width}x{obj.height})")
    except Exception as e:
        print(f"Error processing Items layer: {e}")
    
    # print(f"Total items loaded: {len(items)}")  # Summary of items loaded
    
    # create pyscroll map data
    map_data = pyscroll.TiledMapData(tmx_data)
    
    # Print summary of loaded tile properties
    # print(f"Wall tiles loaded: {len(wall_tiles)}")
    # print(f"Slow tiles loaded: {len(slow_tiles)}")
    
    return tmx_data, map_data, collision_tiles, items, wall_tiles, slow_tiles

def get_tile_id_at_position(tmx_data, x, y, tile_size=16):
    """Get the tile ID at a specific world position"""
    # convert world coordinates to tile coordinates
    tile_x = int(x // tile_size)
    tile_y = int(y // tile_size)
    
    # look through visible layers to find background tiles
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):
            # check if the tile coordinates are within bounds
            if (0 <= tile_y < len(layer.data) and 
                0 <= tile_x < len(layer.data[tile_y])):
                gid = layer.data[tile_y][tile_x]
                if gid > 0:  # non-empty tile
                    return gid
    
    return 0  # return 0 if no tile found

def is_tile_slow(tmx_data, x, y, tile_size=16):
    """Check if the tile at a specific world position has the 'slow' property set to true"""
    # convert world coordinates to tile coordinates
    tile_x = int(x // tile_size)
    tile_y = int(y // tile_size)
    
    # look through visible layers to find background tiles
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):
            # check if the tile coordinates are within bounds
            if (0 <= tile_y < len(layer.data) and 
                0 <= tile_x < len(layer.data[tile_y])):
                gid = layer.data[tile_y][tile_x]
                if gid > 0:  # non-empty tile
                    # get tile properties from the tileset
                    tile_properties = tmx_data.get_tile_properties_by_gid(gid)
                    if tile_properties and tile_properties.get('slow', False):
                        return True
    
    return False  # return False if no slow tile found

def is_tile_slow_fast(slow_tiles_dict, tile_x, tile_y):
    """Fast lookup for slow tiles using precomputed dictionary"""
    return slow_tiles_dict.get((tile_x, tile_y), False)

def is_tile_wall_fast(wall_tiles_dict, tile_x, tile_y):
    """Fast lookup for wall tiles using precomputed dictionary"""
    return wall_tiles_dict.get((tile_x, tile_y), False)

def get_tile_weight_fast(wall_tiles_dict, slow_tiles_dict, tile_x, tile_y):
    """Get movement cost for a tile position using fast lookup dictionaries"""
    # Bounds check can be done by the caller if needed
    if is_tile_wall_fast(wall_tiles_dict, tile_x, tile_y):
        return float('inf')  # Walls are impassable
    elif is_tile_slow_fast(slow_tiles_dict, tile_x, tile_y):
        return 3  # Slow tiles have higher cost
    else:
        return 1  # Normal movement cost

def debug_tileset(tmx_data):
    # get layers 
    print(tmx_data.layers) # get all layers 
    for layer in tmx_data.visible_layers: # get visible layers 
      print(layer)
    
    # print(tmx_data.layernames) # get all layer names as dict
    
    # print(tmx_data.get_layer_by_name('Floor')) # get one layer by name
    
    # for obj in tmx_data.objectgroups: # get object layers
    #   print(obj)
    
    # get tiles
    # layer = tmx_data.get_layer_by_name('Floor')
    # for x,y,surf in layer.tiles(): # get all the information
    #   print(x * 128)
    #   print(y * 128)
    #   print(surf)
    
    # print(layer.data)
    
    # print(layer.name)
    # print(layer.id)
    
    # get objects
    # object_layer = tmx_data.get_layer_by_name('Objects')
    # for obj in object_layer:
    #   # print(obj.x)
    #   # print(obj.y)
    #   # print(obj.image)
    #   if obj.type == 'Shape':
            # if obj.name == 'Marker':
            #   print(obj.x)
            #   print(obj.y)
            # if obj.name == 'Rectangle':
            #   print(obj.x)
            #   print(obj.y)
            #   print(obj.width)
            #   print(obj.height)
            #   print(obj.as_points)
    
            # if obj.name == 'Ellipse':
            #   print(dir(obj))
    
            # if obj.name == 'Polygon':
            #   print(obj.as_points)
            #   print(obj.points)
    
    # for obj in tmx_data.objects:
    #   print(obj)