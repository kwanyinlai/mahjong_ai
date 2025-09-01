from __future__ import annotations

from typing import List, Union

import numpy as np


class MahjongTile:
    """
    Represents a Mahjong Tile
    """
    tiletype: str
    subtype: str
    numchar: Union[int, str]  # either the character or number represented on the tile

    def __hash__(self):
        return hash((self.tiletype, self.subtype, self.numchar))

    def __init__(self, tiletype: str, subtype: str, numchar: Union[int, str] = -1):
        tiletype = tiletype.lower()
        if tiletype not in ('suit', 'honour', 'flower'):
            raise ValueError("Invalid tile type")
        else:
            self.tiletype = tiletype
        if tiletype == 'suit' and subtype not in ('circle', 'bamboo', 'number'):
            raise ValueError("Invalid subtype")
        elif tiletype == 'honour' and subtype not in ('wind', 'dragon'):
            raise ValueError("Invalid subtype")

        if tiletype == 'suit':
            if not isinstance(numchar, int) or numchar < 1 or numchar > 9:
                raise ValueError("Invalid number")
            else:
                self.numchar = int(numchar)
        elif tiletype == 'honour':
            if subtype == 'wind' and numchar not in ('east', 'south', 'west', 'north'):
                raise ValueError("Invalid number")
            elif subtype == 'dragon' and numchar not in ('red', 'green', 'white'):
                raise ValueError("Invalid number")
            else:
                self.numchar = numchar
        elif tiletype == 'flower':
            if subtype not in ('flower', 'season'):
                raise ValueError("Invalid subtype")
            elif subtype == 'flower' and numchar not in ('plum', 'orchid', 'chrysanthemum', 'bamboo'):
                raise ValueError("Invalid number")
            elif subtype == 'season' and numchar not in ('summer', 'spring', 'autumn', 'winter'):
                raise ValueError("Invalid number")
            else:
                self.numchar = numchar
        self.subtype = subtype
        self.tiletype = tiletype

    def __eq__(self, other: MahjongTile):
        return self.tiletype == other.tiletype and self.subtype == other.subtype and self.numchar == other.numchar

    def __str__(self):
        return self.tiletype + self.subtype + str(self.numchar)

    def __lt__(self, other: MahjongTile):
        suit_order = {'circle': 0, 'bamboo': 1, 'number': 2, 'wind': 3, 'dragon': 4, 'flower': 5, 'season': 6}
        if self.subtype != other.subtype:
            return suit_order[self.subtype] < suit_order[other.subtype]
        return self.numchar < other.numchar
        # TODO: Fix compatability with 'season' and 'flower' subtype

    def __le__(self, other: MahjongTile):
        suit_order = {'circle': 0, 'bamboo': 1, 'number': 2, 'wind': 3, 'dragon': 4, 'flower': 5, 'season': 6}
        if self.subtype != other.subtype:
            return suit_order[self.subtype] <= suit_order[other.subtype]
        return self.numchar <= other.numchar
        # TODO: Fix compatability with 'season' and 'flower' subtype

    def to_index(self):
        if self.subtype == "circle":
            return self.numchar - 1
        elif self.subtype == "bamboo":
            return 9 + (self.numchar - 1)
        elif self.subtype == "number":
            return 18 + (self.numchar - 1)
        elif self.subtype == "wind":
            wind_order = {"east": 27, "south": 28, "west": 29, "north": 30}
            return wind_order[self.numchar]
        elif self.subtype == "dragon":
            dragon_order = {"red": 31, "green": 32, "white": 33}
            return dragon_order[self.numchar]
