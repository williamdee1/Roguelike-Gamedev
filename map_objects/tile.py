
class Tile:
    """
    A tile on a map. It may or may not be blocked, and may or may not block sight.
    """
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked

        if block_sight is None: # setting it so that by default if a tile is blocked, it also blocks sight
            block_sight = blocked

        self.block_sight = block_sight

        self.explored = False # to use to mark tiles viewed previously as explored in the render all function