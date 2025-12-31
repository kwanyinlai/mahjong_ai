"""
mahjong_actions.py - constants/enumerator class for readability

includes possible numerical actions reinforcement learning could make
"""

from enum import IntEnum


class MahjongActions(IntEnum):
    """
    enumerator for MahjongActions
    """
    WIN = 14
    ADD_KONG = 15
    PONG = 16
    LOWER_SHEUNG = 17
    MIDDLE_SHEUNG = 18
    UPPER_SHEUNG = 19
    PASS = 20
