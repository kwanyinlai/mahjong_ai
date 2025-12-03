from typing import Tuple

import numpy as np
from player import Player
from policy import Policy

from tile import MahjongTile


class RLAgent(Player):
    """
    Reinforcement learning
    """
    policy: Policy

    def discard_tile(self, state: np.ndarray = None) -> MahjongTile:
        """

        :param state:
        :return:
        """
        state = self.game.get_state_representation(self)
        return self.policy.select_discard(state, self.hidden_hand)

    def decide_win(self, latest_tile, circle_wind, player_number: int, state: np.ndarray = None) -> bool:
        """

        :param tile:
        :param state:
        :return:
        """
        return self.policy.select_win(state)

    def decide_pong(self, discarded_tile: MahjongTile, state: np.array = None) -> bool:
        """

        :param tile:
        :param state:
        :return:
        """
        return self.policy.select_pong(state)

    def decide_add_kong(self, discarded_tile: MahjongTile, state: np.array = None) -> bool:
        """

        :param tile:
        :param state:
        :return:
        """
        return self.policy.select_add_kong(state)

    def decide_sheung(self, latest_tile: MahjongTile, state: np.ndarray = None) -> Tuple[int, int]:
        return self.policy.select_sheung(state)

    def select_actions(self, observation: np.ndarray):
        if self.policy.select_win(observation):
            return 14
        if self.policy.select_add_kong(observation):
            return 15
        if self.policy.select_pong(observation):
            return 16
        sheung_action = self.policy.select_sheung(observation)
        if self.policy.select_sheung(observation):
            return 17

        tile_to_discard = self.policy.select_discard(observation, self.hidden_hand)
        tile_index = self.hidden_hand.index(tile_to_discard)
        return tile_index
