import tcod as libtcod
""" From the Roguelike Dev Tutorial found at : http://rogueliketutorials.com/tutorials/tcod/ """
"""Current Stage - Part 9"""

from components.fighter import Fighter
from components.inventory import Inventory
from death_functions import kill_monster, kill_player
from entity import Entity, get_blocking_entities_at_location
from fov_functions import initialize_fov, recompute_fov
from game_messages import Message, MessageLog
from game_states import GameStates
from input_handlers import handle_keys
from map_objects.game_map import GameMap
from render_functions import clear_all, render_all, RenderOrder


def main():
    screen_width = 80
    screen_height = 50

    bar_width = 20
    panel_height = 7
    panel_y = screen_height - panel_height

    message_x = bar_width + 2
    message_width = screen_width - bar_width - 2
    message_height = panel_height - 1

    map_width = 80
    map_height = 43

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    fov_algorithm = 0  # the default algo that libtcod uses for Field of View
    fov_light_walls = True  # whether to light up the walls that you see
    fov_radius = 10 # how far you can see

    max_monsters_per_room = 3 # used in the game_map file to place entities
    max_items_per_room = 2

    colors = {
        'dark_wall': libtcod.Color(0, 0, 100),
        'dark_ground': libtcod.Color(50, 50, 150),
        'light_wall': libtcod.Color(130, 110, 50),
        'light_ground': libtcod.Color(200, 180, 50)
    }

    fighter_component = Fighter(hp = 30, defense = 2, power = 5) # ascribing values to fighter, calling the functon within components
    inventory_component = Inventory(26)  # how much you can hold
    player = Entity(0,0, '@', libtcod.black, 'Player', blocks = True, render_order = RenderOrder.ACTOR,
                    fighter = fighter_component, inventory = inventory_component) # the player then has the attributes listed above
    entities = [player]

    libtcod.console_set_custom_font('image.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD) # setting font according to our file

    libtcod.console_init_root(screen_width, screen_height, 'roguelike game', False) # name of the game and width/height

    con = libtcod.console_new(screen_width, screen_height) # defining a specific console 'con' to be able to write to

    panel = libtcod.console_new(screen_width, panel_height) # 2nd console, holding HP bar and any messages

    game_map = GameMap(map_width, map_height) # initializes the gamemap from gamemap.py in map_objects folder
    game_map.make_map(max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities, max_monsters_per_room, max_items_per_room)

    fov_recompute = True # used to tell algo when to change field of view, i.e. only when moving not when standing still/attacking

    fov_map = initialize_fov(game_map)

    message_log = MessageLog(message_x, message_width, message_height)

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    game_state = GameStates.PLAYERS_TURN # starts on players turn
    previous_game_state = game_state # Used to not skip a players turn if they do something like pick up an item

    while not libtcod.console_is_window_closed(): # a loop that won't end until the game window is closed
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse) # this captures user input and updates the key/mouse variables above

        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, fov_radius, fov_light_walls, fov_algorithm) # coming from fov_functions

        render_all(con, panel, entities, player, game_map, fov_map, fov_recompute, message_log, screen_width,
                   screen_height, bar_width, panel_height, panel_y, mouse, colors, game_state) # con is the current console, entities is drawn in render_functions

        fov_recompute = False

        libtcod.console_flush() # this presents everything on screen

        clear_all(con, entities) # put a blank below our character so it doesn't leave a trail, see render_functions.py

        """Action Handling"""
        action = handle_keys(key, game_state) # calls our handle keys function from the input_handlers file, using our key variable, to result in a dictionary called action

        move = action.get('move') # uses the action dictionary created above to return move, exit, pickup or fullscreen from handle_keys function
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        drop_inventory = action.get('drop_inventory')
        inventory_index = action.get('inventory_index')
        exit = action.get('exit')
        fullscreen = action.get('fullscreen')

        player_turn_results = []

        if move and game_state == GameStates.PLAYERS_TURN:
            dx, dy = move
            destination_x = player.x + dx
            destination_y = player.y + dy

            if not game_map.is_blocked(destination_x, destination_y):
                target = get_blocking_entities_at_location(entities, destination_x, destination_y)

                if target: # i.e. does something to the target blocking the way
                    attack_results = player.fighter.attack(target)
                    player_turn_results.extend(attack_results)

                else:
                    player.move(dx, dy) # gets move function from entity class

                    fov_recompute = True # sets fov to True (i.e. to change) when we move

                game_state = GameStates.ENEMY_TURN  # switches it to the enemies turn after moving

        elif pickup and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.item and entity.x == player.x and entity.y == player.y:
                    pickup_results = player.inventory.add_item(entity)
                    player_turn_results.extend(pickup_results)

                    break
            else:
                message_log.add_message(Message('There is nothing here to pick up.', libtcod.yellow))

        if show_inventory:
            previous_game_state = game_state  # ref'd at top, stops it skipping to enemies turn
            game_state = GameStates.SHOW_INVENTORY # switching to this game state with different keys

        if drop_inventory:
            previous_game_state = game_state
            game_state = GameStates.DROP_INVENTORY

        if inventory_index is not None and previous_game_state != GameStates.PLAYER_DEAD and inventory_index < len(
                player.inventory.items):
            item = player.inventory.items[inventory_index]

            if game_state == GameStates.SHOW_INVENTORY:
                player_turn_results.extend(player.inventory.use(item))
            elif game_state == GameStates.DROP_INVENTORY:
                player_turn_results.extend(player.inventory.drop_item(item))

        if exit:
            if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
                game_state = previous_game_state  # now the Esc key just exits the inventory menu, rather than the whole game
            else:
                return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        for player_turn_result in player_turn_results:
            message = player_turn_result.get('message')
            dead_entity = player_turn_result.get('dead')
            item_added = player_turn_result.get('item_added')
            item_consumed = player_turn_result.get('consumed')
            item_dropped = player_turn_result.get('item_dropped')

            if message:
                message_log.add_message(message)

            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity)
                else:
                    message = kill_monster(dead_entity)

                message_log.add_message(message)

            if item_added:
                entities.remove(item_added)

                game_state = GameStates.ENEMY_TURN

            if item_consumed:
                game_state = GameStates.ENEMY_TURN

            if item_dropped:
                entities.append(item_dropped)

                game_state = GameStates.ENEMY_TURN

        if game_state == GameStates.ENEMY_TURN:
            for entity in entities:
                if entity.ai:  # note, the player and items etc won't have an AI component, so this skips them
                    enemy_turn_results = entity.ai.take_turn(player, fov_map, game_map, entities)  # take turn managed in ai file, tells it to move towards or attack player

                    for enemy_turn_result in enemy_turn_results:
                        message = enemy_turn_result.get('message')
                        dead_entity = enemy_turn_result.get('dead')

                        if message:
                            message_log.add_message(message)

                        if dead_entity:
                            if dead_entity == player:
                                message, game_state = kill_player(dead_entity)
                            else:
                                message = kill_monster(dead_entity)

                            message_log.add_message(message)

                        if game_state == GameStates.PLAYER_DEAD:
                            break

                    if game_state == GameStates.PLAYER_DEAD:
                        break
            else:
                game_state = GameStates.PLAYERS_TURN

if __name__ == '__main__':
    main()