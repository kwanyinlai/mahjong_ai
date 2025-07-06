import random

from main import Tiles, Player


class RandomBot(Player):
    def decide_pong(self, tile: Tiles):
        if tile in self._hidden_hand and self._hidden_hand[tile] == 2:
            is_pong = random.choice([True, False])
            if is_pong:
                self._hidden_hand[tile] = 0
                self.revealed_sets.append([tile, tile, tile])
                return True


        return False

    def decide_add_kong(self, latest_tile) -> bool:
        super().decide_add_kong(latest_tile)


    def decide_win(self, latest_tile, game_state):
        raise NotImplementedError

    def decide_sheung(self, selected_tile) -> bool:
        raise NotImplementedError

    def decide_pong(self, discarded_tile: Tiles) -> bool:
        raise NotImplementedError

    def discard_tile(self, game_state: MahjongGame) -> Tiles:
        raise NotImplementedError # implement decision making logic or player input




    # function to discourage showing hand
    # function to discourage locking into hands
    # function to determine how easily the tiles would fit into another set (probability probably)
