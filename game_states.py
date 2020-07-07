from enum import Enum

""" Enum is a set of named values that doesn't change, here it's used to keep track of whose turn it is"""

class GameStates(Enum):
    PLAYERS_TURN = 1
    ENEMY_TURN = 2
    PLAYER_DEAD = 3
    SHOW_INVENTORY = 4
    DROP_INVENTORY = 5