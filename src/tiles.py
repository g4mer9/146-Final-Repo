import pygame, sys
from pytmx.util_pygame import load_pygame

# from very helpful youtube tutorial:
# https://www.youtube.com/watch?v=N6xqCwblyiw
# https://pastebin.com/dEUVdNip

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, image, groups):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)

def load_tileset(filename, tile_size):
    tmx_data = load_pygame(filename)
    sprite_group = pygame.sprite.Group()
    collision_tiles = []

    print(f"Loading tileset from {filename}")
    
    # debug tileset information
    for tileset in tmx_data.tilesets:
        print(f"Tileset '{tileset.name}': firstgid={tileset.firstgid}")
    
    # get all collision data once
    try:
        colliders_gen = tmx_data.get_tile_colliders()
        all_colliders = list(colliders_gen)
        print(f"Found collision data for {len(all_colliders)} tiles")
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
                    tile = Tile(pos=pos, image=image, groups=sprite_group)
                    
                    # get the tile GID from the layer data
                    gid = layer.data[y][x] if y < len(layer.data) and x < len(layer.data[y]) else 0
                    if gid > 0:
                        gids_in_layer.add(gid)
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
                        
            if collision_count > 0:
                print(f"Layer '{layer.name}' loaded {collision_count} collision objects")
            
    print(f"Total collision rectangles: {len(collision_tiles)}")
    
    for obj in tmx_data.objects:
        pos = obj.x, obj.y
        if (obj.type in 'Items'):
            Tile(pos=pos, image=obj.image, groups=sprite_group)
        if (hasattr(obj, 'properties') and obj.properties.get('collision', False)):
            collision_tiles.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
    return tmx_data, sprite_group, collision_tiles

def draw_objs(screen, tmx_data):
    if(tmx_data):
        for obj in tmx_data.objects:
            pos = obj.x,obj.y
            if obj.type == 'Shape':
                if obj.name == 'Marker':
                    pygame.draw.circle(screen,'red',(obj.x,obj.y),5)
                if obj.name == 'Rectangle':
                    rect = pygame.Rect(obj.x,obj.y,obj.width,obj.height)
                    pygame.draw.rect(screen,'yellow',rect)
    
                if obj.name == 'Ellipse':
                    rect = pygame.Rect(obj.x,obj.y,obj.width,obj.height)
                    pygame.draw.ellipse(screen,'blue',rect)
    
                if obj.name == 'Polygon':
                    points = [(point.x,point.y) for point in obj.points]
                    pygame.draw.polygon(screen,'green',points)

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