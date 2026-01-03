"""
mahjong_actions.py - constants/enumerator class for readability

includes possible numerical actions reinforcement learning could make
"""

from enum import IntEnum


class MahjongActions(IntEnum):
    """
    enumerator for MahjongActions
    """
    DISCARD_TILE_1 = 0
    DISCARD_TILE_2 = 1
    DISCARD_TILE_3 = 2
    DISCARD_TILE_4 = 3
    DISCARD_TILE_5 = 4
    DISCARD_TILE_6 = 5
    DISCARD_TILE_7 = 6
    DISCARD_TILE_8 = 7
    DISCARD_TILE_9 = 8
    DISCARD_TILE_10 = 9
    DISCARD_TILE_11 = 10
    DISCARD_TILE_12 = 11
    DISCARD_TILE_13 = 12
    DISCARD_TILE_14 = 13
    WIN = 14
    ADD_KONG = 15
    PONG = 16
    LOWER_SHEUNG = 17
    MIDDLE_SHEUNG = 18
    UPPER_SHEUNG = 19
    PASS = 20
