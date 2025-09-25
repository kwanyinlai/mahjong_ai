import numpy as np
from Player import Player
from policy import Policy

from tile import MahjongTile


class RLAgent(Player):
    """
    Reinforcement learning
    """
    policy: Policy

    def discard_tile(self, state: np.ndarray) -> MahjongTile:
        """

        :param state:
        :return:
        """
        state = self.game.get_state_representation(self)
        return self.policy.select_discard(state, self.hidden_hand)

    def decide_win(self, tile, state: np.ndarray) -> bool:
        """

        :param tile:
        :param state:
        :return:
        """
        if not super().decide_win(tile):
            return False
        return self.policy.select_win(state)

    def decide_pong(self, tile: MahjongTile, state: np.ndarray) -> bool:
        """

        :param tile:
        :param state:
        :return:
        """
        if not super().decide_pong(tile):
            return False
        return self.policy.select_pong(state)

    def decide_add_kong(self, tile: MahjongTile, state: np.ndarray):
        """

        :param tile:
        :param state:
        :return:
        """
        if not super().decide_add_kong(tile):
            return False
        return self.policy.select_add_kong(state)
