from __future__ import annotations

import math
import random

import numpy as np

from player import Player
from typing import Tuple

from tile import MahjongTile


class RandomBot(Player):
    def decide_pong(self, tile: MahjongTile, state: np.array = None):
        if not super().decide_pong(tile):
            return False
        is_pong = random.choice([True, False])

        return is_pong

    def decide_add_kong(self, latest_tile, state: np.array = None) -> bool:
        if not super().decide_add_kong(latest_tile):
            return False

        is_kong = random.choice([True, False])  # doesn't work because check if kong

        return is_kong

    def decide_win(self, latest_tile, state: np.array = None):
        return super().decide_win(latest_tile)

    def decide_sheung(self, latest_tile, state: np.array = None) -> Tuple[int, int] | None:
        possible_sheungs = self.show_all_possible_sheungs(latest_tile)
        if all(sheung is None for sheung in possible_sheungs):
            return None
        is_sheung = random.choice([True, False])
        if is_sheung:
            decided_sheung = random.choice([indices for indices in possible_sheungs if indices is not None])
            return decided_sheung

        return None

    def discard_tile(self, state: np.array = None) -> MahjongTile:
        removed_tile = random.choice(self.hidden_hand)
        self.hidden_hand.remove(removed_tile)
        print("PLAYER " + str(self.player_id) + " DISCARDED")
        print(removed_tile)
        self.discard_pile.append(removed_tile)
        return removed_tile


class YesBot(Player):
    def decide_pong(self, tile: MahjongTile, state: np.array = None):
        if not super().decide_pong(tile):
            return False
        return True

    def decide_add_kong(self, latest_tile, state: np.array = None) -> bool:
        if not super().decide_add_kong(latest_tile):
            return False
        return True

    def decide_win(self, latest_tile, state: np.array = None):
        return super().decide_win(latest_tile)

    def decide_sheung(self, latest_tile, state: np.array = None) -> Tuple[int, int] | None:
        possible_sheungs = self.show_all_possible_sheungs(latest_tile)

        if all(sheung is None for sheung in possible_sheungs):
            return None

        decided_sheung = random.choice([indices for indices in possible_sheungs if indices is not None])
        return decided_sheung

    def discard_tile(self, state: np.array = None) -> MahjongTile:
        removed_tile = random.choice(self.hidden_hand)
        self.hidden_hand.remove(removed_tile)
        print("PLAYER " + str(self.player_id) + " DISCARDED")
        print(removed_tile)
        self.discard_pile.append(removed_tile)
        return removed_tile


class BasicBot(Player):

    def decide_pong(self, tile: MahjongTile, state: np.array = None):
        if not super().decide_pong(tile):
            return False

        return True

    def decide_add_kong(self, latest_tile, state: np.array = None) -> bool:
        if not super().decide_add_kong(latest_tile):
            return False
        return True

    def decide_win(self, latest_tile, state: np.array = None):
        return super().decide_win(latest_tile)

    def decide_sheung(self, latest_tile, state: np.array = None) -> Tuple[int, int] | None:
        possible_sheungs = self.show_all_possible_sheungs(latest_tile)

        if all(sheung is None for sheung in possible_sheungs):
            return None

        decided_sheung = random.choice([indices for indices in possible_sheungs if indices is not None])
        return decided_sheung

    def discard_tile(self, state: np.array = None) -> MahjongTile:

        lowest_tile_needed = math.inf
        discarded_tile = None
        current_hand = [tile for subset in self.revealed_sets for tile in subset] + self.hidden_hand

        for tile in self.hidden_hand:
            tile_needed = self.calculate_tiles_required(current_hand, tile)
            if tile_needed < lowest_tile_needed:
                discarded_tile = tile
                lowest_tile_needed = tile_needed

        return discarded_tile

    def calculate_tiles_required(self, hand, removed_tile) -> int:
        """
        Return the tiles required to complete the hand
        """
        hand_copy = hand.copy()
        hand_copy.remove(removed_tile)
        i = 0
        pair = False
        complete_sets = 0
        incomplete_sets = 0

        while i < len(hand_copy) - 2:
            if hand_copy[i] == hand_copy[i + 1]:
                if hand_copy[i] == hand_copy[i + 2]:
                    complete_sets += 1
                    for _ in range(3):
                        hand_copy.pop(i)
                else:
                    for _ in range(2):
                        hand_copy.pop(i)
                    if not pair:
                        pair = True
                    else:
                        incomplete_sets += 1
                pass
            elif (hand_copy[i].tiletype == "suit" and hand_copy[i].subtype == hand_copy[i + 1].subtype and
                  hand_copy[i].numchar == hand_copy[i + 1].numchar - 1):
                if (hand_copy[i].subtype == hand_copy[i + 2].subtype and hand_copy[i].numchar ==
                        hand_copy[i + 2].numchar - 2):
                    complete_sets += 1
                    for j in range(3):
                        hand_copy.pop(i)
                else:
                    for j in range(2):
                        hand_copy.pop(i)
                    incomplete_sets += 1
            else:
                i += 1
        print("COMPLETE SETS: " + str(complete_sets))
        print("INCOMPLETE SETS: " + str(incomplete_sets))
        return 8 - (2 * complete_sets) - incomplete_sets - int(pair)








# function to discourage showing hand
# function to discourage locking into hands
# function to determine how easily the tiles would fit into another set (probability probably)
