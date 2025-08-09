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
    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):
            for x, y, image in layer.tiles():
                pos = (x * tile_size, y * tile_size)
                Tile(pos=pos, image=image, groups=sprite_group)
    for obj in tmx_data.objects:
        pos = obj.x, obj.y
        if (obj.type in 'Items'):
            Tile(pos=pos, image=obj.image, groups=sprite_group)

    return tmx_data, sprite_group

def draw_background(screen, tmx_data):
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