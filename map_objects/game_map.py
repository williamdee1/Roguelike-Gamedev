import tcod as libtcod
from random import randint

from components.ai import BasicMonster
from components.fighter import Fighter
from components.item import Item
from entity import Entity
from game_messages import Message
from item_functions import heal, cast_lightning, cast_fireball, cast_confuse
from map_objects.rect import Rect
from map_objects.tile import Tile
from render_functions import RenderOrder

class GameMap:
    def __init__(self, width, height):
        self.width = width   # width and height are defined in the engine file
        self.height = height
        self.tiles = self.initialize_tiles() # initializes a 2d array

    def initialize_tiles(self):
        tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)] #True sets the default to tile = blocked, and then we choose where we can move by un-blocking

        return tiles

    def make_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities, max_monsters_per_room, max_items_per_room): # creating rooms
        rooms = []
        num_rooms = 0

        for r in range(max_rooms): #setting random height and width for generated rooms
            w = randint(room_min_size, room_max_size)
            h = randint(room_min_size, room_max_size)

            x = randint(0, map_width - w - 1) # random position without going out of the boundaries of the map
            y = randint(0, map_height - h - 1)

            new_room = Rect(x, y, w, h) # makes a room using the rect function

            for other_room in rooms: # looks through other rooms to see if they intersect with the new one
                if new_room.intersect(other_room):
                    break

            else: # i.e. there are no intersections with other walls
                self.create_room(new_room) # creates that new room
                (new_x, new_y) = new_room.center()
                if num_rooms == 0: # the first room where the player starts
                    player.x = new_x
                    player.y = new_y
                else: # i.e. all the rooms excl. the first
                    (prev_x, prev_y) = rooms[num_rooms - 1].center() # get the center co-ords of the last room

                    # drawing tunnels from the center of each dungeon in random directions
                    if randint(0,1) == 1: # random choice between 0 and 1
                        self.create_h_tunnel(prev_x, new_x, prev_y)  # moves horizontally and then vertically, building tunnels
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        self.create_v_tunnel(prev_y, new_y, prev_x) # moves vertically and then horizontally
                        self.create_h_tunnel(prev_x, new_x, new_y)

                self.place_entities(new_room, entities, max_monsters_per_room, max_items_per_room)

                rooms.append(new_room)
                num_rooms += 1

    def create_room(self, room): # goes through the tiles in the rectangle (see rect.py) and makes them passable (not blocked)
        for x in range(room.x1 + 1, room.x2): # from top left to bottom right
            for y in range(room.y1 + 1, room.y2): # we add one so our rectangles (rooms) essentially have a wall separating them from any others
                self.tiles[x][y].blocked = False # making sure the tiles in the room we create aren't blocked
                self.tiles[x][y].block_sight = False

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def place_entities(self, room, entities, max_monsters_per_room, max_items_per_room):
        number_of_monsters = randint(0, max_monsters_per_room) # generates a random no. monsters between these bounds
        number_of_items = randint(0, max_items_per_room)

        for i in range(number_of_monsters): # chooses a random location in the room to spawn each monster below
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            """ Creating the monsters"""
            if not any([entity for entity in entities if entity.x == x and entity.y == y]): # checking no overlap for placement of entities
                if randint(0, 100) < 80:  # used to determine the frequency of diff enemies appearing, 80% chance here it's an 'o'
                    fighter_component = Fighter(hp=10, defense=0, power=3)
                    ai_component = BasicMonster()

                    monster = Entity(x, y, 'o', libtcod.desaturated_chartreuse, 'Orc', blocks = True,
                                     render_order=RenderOrder.ACTOR, fighter = fighter_component, ai = ai_component) # calls the Entity class
                else:
                    fighter_component = Fighter(hp=16, defense=1, power=4)
                    ai_component = BasicMonster()

                    monster = Entity(x, y, 'T', libtcod.darker_green, 'Troll', blocks = True,
                                     render_order=RenderOrder.ACTOR, fighter = fighter_component, ai = ai_component)

                entities.append(monster)

        """Creating the items"""
        for i in range(number_of_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                item_chance = randint(0, 100)

                if item_chance < 70:
                    item_component = Item(use_function=heal, amount=4)
                    item = Entity(x, y, '!', libtcod.violet, 'Healing Potion', render_order=RenderOrder.ITEM,
                                  item=item_component)

                elif item_chance < 80:
                    item_component = Item(use_function=cast_fireball, targeting=True, targeting_message=Message(
                        'Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan),
                                          damage=12, radius=3)
                    item = Entity(x, y, '#', libtcod.red, 'Fireball Scroll', render_order=RenderOrder.ITEM,
                                  item=item_component)

                elif item_chance < 90:
                    item_component = Item(use_function=cast_confuse, targeting=True, targeting_message=Message(
                        'Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan))
                    item = Entity(x, y, '#', libtcod.light_pink, 'Confusion Scroll', render_order=RenderOrder.ITEM,
                                  item=item_component)

                else:
                    item_component = Item(use_function=cast_lightning, damage=20, maximum_range=5)
                    item = Entity(x, y, '#', libtcod.yellow, 'Lightning Scroll', render_order=RenderOrder.ITEM,
                                  item=item_component)

                entities.append(item)


    def is_blocked(self, x, y):
        if self.tiles[x][y].blocked:
            return True

        return False