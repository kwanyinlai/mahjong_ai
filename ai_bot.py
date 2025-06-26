import random

from main import Tiles, Player


class RandomBot(Player):
    def check_pong(self, tile: Tiles):
        if tile in self.hidden_hand and self.hidden_hand[tile] == 2:
            is_pong = random.choice([True, False])
            if is_pong:
                self.hidden_hand[tile] = 0
                self.revealed_sets.append([tile, tile, tile])
                return True


        return False
