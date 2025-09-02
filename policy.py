from typing import List
import numpy as np

from tile import MahjongTile


class Policy:
    """
    Policy governing bot
    """

    def select_discard(self, state: np.ndarray, hidden_hand: List[MahjongTile]) -> MahjongTile:
        """
        Return the index of the tile to discard in player's hand
        :param state:
        :param hidden_hand:
        """
        raise NotImplementedError

    def select_win(self, state: np.ndarray) -> bool:
        """

        :param state:
        """
        raise NotImplementedError

    def select_pong(self, state: np.ndarray) -> bool:
        """

        :param state:
        """
        raise NotImplementedError

    def select_add_kong(self, state: np.ndarray) -> bool:
        """

        :param state:
        """
        raise NotImplementedError


class Policy:
    """
    Policy governing bot
    """

    def select_discard(self, state: np.ndarray, hidden_hand: List[MahjongTile]) -> MahjongTile:
        """
        Return the index of the tile to discard in player's hand
        :param state:
        :param hidden_hand:
        """
        raise NotImplementedError

    def select_win(self, state: np.ndarray) -> bool:
        """

        :param state:
        """
        raise NotImplementedError

    def select_pong(self, state: np.ndarray) -> bool:
        """

        :param state:
        """
        raise NotImplementedError

    def select_add_kong(self, state: np.ndarray) -> bool:
        """

        :param state:
        """
        raise NotImplementedError
