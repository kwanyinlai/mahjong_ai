import random

from main import Tiles, Player


class RandomBot(Player):
    def check_pong(self, tile: Tiles):
        if tile in self.hand and self.hand[tile] == 2:
            is_pong = random.choice([True, False])
            if is_pong:
                self.hand[tile] = 3


        return False
