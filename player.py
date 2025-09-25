from __future__ import annotations

import bisect
import copy
from typing import List, Set, Tuple

import numpy as np

from tile import MahjongTile


class Player:
    """
    Represents a player in a MahjongGame
    """
    player_id: int
    hidden_hand: List[MahjongTile]  # assume sorted
    revealed_sets: List[List[MahjongTile]]
    flowers: List[MahjongTile]
    discard_pile: List[MahjongTile]
    score: int = 0
    player_order: int
    highest_fan: int = 0
    _orphans: Set[MahjongTile] = set()

    def __init__(self, player_id: int, player_order: int):
        self.player_id = player_id
        self.hidden_hand = []
        self.revealed_sets = []
        self.flowers = []
        self.discard_pile = []
        self.total_score = 0
        self.player_order = player_order
        self._set_orphans()

    def soft_reset(self) -> None:
        """
        Reset all non-global attributes
        :return:
        """
        self.hidden_hand = []
        self.revealed_sets = []
        self.flowers = []
        self.discard_pile = []
        self.highest_fan = 0

    def check_claims(self, circle_wind: str, player_number: int, latest_tile: MahjongTile = None,
                     state: np.ndarray = None) -> Tuple[bool, bool, bool]:
        """
        WIN_CLAIM
        PONG
        ADD_KONG
        SHEUNG
        DISCARD
        """

        if not latest_tile:
            return False, False, False
        if self.decide_win(latest_tile, circle_wind, state):
            return True, False, False
        if latest_tile is not None:
            if self.decide_pong(latest_tile, state):
                return False, True, False
            elif self.decide_add_kong(latest_tile, state):
                return False, False, True
        return False, False, False

    def _set_hand(self) -> None:
        """
        Set the hand for a player to a specified set
        !!!! FOR TESTING PURPOSES ONLY !!!!
        """
        tile1 = MahjongTile(tiletype="suit", subtype="circle", numchar=1)
        tile2 = MahjongTile(tiletype="suit", subtype="circle", numchar=2)
        tile3 = MahjongTile(tiletype="suit", subtype="circle", numchar=3)
        tile4 = MahjongTile(tiletype="suit", subtype="circle", numchar=4)
        tile5 = MahjongTile(tiletype="suit", subtype="circle", numchar=5)
        tile6 = MahjongTile(tiletype="suit", subtype="circle", numchar=6)
        tile7 = MahjongTile(tiletype="suit", subtype="circle", numchar=7)
        tile8 = MahjongTile(tiletype="suit", subtype="circle", numchar=8)
        tile9 = MahjongTile(tiletype="suit", subtype="circle", numchar=9)
        self.hidden_hand = [tile1, tile1, tile2, tile2, tile2, tile3, tile4, tile4, tile5, tile5, tile5, tile5, tile5,
                            tile6, tile9, tile9, tile9]

    def check_winning_hand(self, circle_wind: str) -> bool:
        """
        Check and return whether the player currently has a winning hand
        with sufficient 'faan' score
        """

        if self.check_thirteen_orphans():
            self.highest_fan = 13 + self.count_flower_fan()
            return True

        possible_hands = []
        i = 0
        while i < len(self.hidden_hand) - 1:
            tile = self.hidden_hand[i]
            potential_hand = []
            if self.hidden_hand[i + 1] == tile:  # check all possible combinations of 'eyes' first for efficiency
                remaining_hand = self.hidden_hand.copy()

                potential_hand.append([remaining_hand.pop(i), remaining_hand.pop(i)])

                if self.can_fit_into_set(remaining_hand, potential_hand):
                    revealed_set = self.revealed_sets.copy()
                    potential_hand += revealed_set
                    possible_hands.append(potential_hand)

            i += 1

        sorted_hands = sorted(possible_hands,
                              key=lambda hand: Player.score_hand(hand, self.flowers, circle_wind, self.player_order),
                              reverse=True)
        if sorted_hands:
            highest_fan = Player.score_hand(sorted_hands[0], self.flowers, circle_wind, self.player_order)
            print(f'Current fan is {highest_fan}')

            if highest_fan >= 3:
                self.highest_fan = highest_fan
                return True
        return False

    def _set_orphans(self):
        """
        Set thirteen orphans
        :return:
        """
        tile1 = MahjongTile(tiletype="suit", subtype="circle", numchar=1)
        tile2 = MahjongTile(tiletype="suit", subtype="circle", numchar=9)
        tile3 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=1)
        tile4 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=9)
        tile5 = MahjongTile(tiletype="suit", subtype="number", numchar=1)
        tile6 = MahjongTile(tiletype="suit", subtype="number", numchar=9)
        tile7 = MahjongTile(tiletype="honour", subtype="dragon", numchar='red')
        tile8 = MahjongTile(tiletype="honour", subtype="dragon", numchar='white')
        tile9 = MahjongTile(tiletype="honour", subtype="dragon", numchar='green')
        tile10 = MahjongTile(tiletype="honour", subtype="wind", numchar='north')
        tile11 = MahjongTile(tiletype="honour", subtype="wind", numchar='east')
        tile12 = MahjongTile(tiletype="honour", subtype="wind", numchar='south')
        tile13 = MahjongTile(tiletype="honour", subtype="wind", numchar='west')
        self.orphans = {tile1, tile2, tile3, tile4, tile5, tile6, tile7, tile8, tile9, tile10,
                        tile11, tile12, tile13}

    def check_thirteen_orphans(self):
        """
        Edge case of thirteen orphans to be checked with winning hand
        """
        pair_exists = any(self.hidden_hand[i] == self.hidden_hand[i+1] for i in range(len(self.hidden_hand)-1))
        all_orphans = self.orphans <= {tile for tile in self.hidden_hand}

        return len(self.hidden_hand) == 14 and pair_exists and all_orphans

    def can_fit_into_set(self, remaining_hand: List[MahjongTile], potential_hand: List[List[MahjongTile]]):
        """
        Recursive function that checks if the remaining hand can fit in
        """
        if len(remaining_hand) == 0:
            return True
        else:
            tile = remaining_hand[0]  # always checks pong first. this approach does appear to work logically speaking
            # because of the sorted hand clears edge cases but
            #  not rigorously proven so possibly bugs CAUTION
            if len(remaining_hand) >= 3 and remaining_hand[1] == tile and remaining_hand[2] == tile:
                for j in range(0, 3):
                    remaining_hand.pop(0)
                potential_hand.append([tile, tile, tile])
                return self.can_fit_into_set(remaining_hand, potential_hand)
            if self.check_sheung(remaining_hand, tile, potential_hand):
                return self.can_fit_into_set(remaining_hand, potential_hand)

            return False

    @staticmethod
    def check_sheung(remaining_hand: List[MahjongTile], selected_tile: MahjongTile,
                     potential_hand: List[List[MahjongTile]]):
        """
        - only check ascending sheung for consistency
        - assumes the tile exists in the remaining hand
        - mutates if True
        """

        if not (selected_tile.tiletype == "suit" and selected_tile.numchar <= 7):
            return False
        index = bisect.bisect_left(remaining_hand, selected_tile)

        indices = [index, -1, -1]
        target_tile = MahjongTile(tiletype=selected_tile.tiletype,
                                  subtype=selected_tile.subtype,
                                  numchar=selected_tile.numchar + 2)

        while index < len(remaining_hand) and remaining_hand[index] <= target_tile:
            if remaining_hand[index].numchar == selected_tile.numchar + 1:
                indices[1] = index
            elif remaining_hand[index].numchar == selected_tile.numchar + 2:
                indices[2] = index
            index += 1

        if indices[1] == -1 or indices[2] == -1:
            return False
        else:
            potential_hand.append([remaining_hand.pop(indices[0]),
                                   remaining_hand.pop(indices[1] - 1),
                                   remaining_hand.pop(indices[2] - 2)])
            return True

    @staticmethod
    def potential_fan(potential_hand: List[List[MahjongTile]], flowers: List[MahjongTile],
                      circle_wind, player_number) -> int | float:
        """
        Return a score for this hand, doesn't have to be complete (for potential fan)
        """
        if len(potential_hand) == 0:
            return 0
        hand_copy = copy.deepcopy(potential_hand)
        flower_copy = copy.deepcopy(flowers)
        fan = 0
        ordered_flower = ['plum', 'orchid', 'chrysanthemum', 'bamboo']
        ordered_season = ['summer', 'spring', 'autumn', 'winter']
        ordered_cardinal = ['east', 'south', 'west', 'north']
        if len(flower_copy) == 0:
            fan += 1
        elif {'plum', 'orchid', 'chrysanthemum', 'bamboo'} <= {flower.numchar for flower in flower_copy}:
            fan += 2
        elif {'summer', 'spring', 'autumn', 'winter'} <= {flower.numchar for flower in flower_copy}:
            fan += 2
        else:
            if any(flower.numchar == ordered_flower[player_number] for flower in flower_copy):
                fan += 1
            if any(season.numchar == ordered_season[player_number] for season in flower_copy):
                fan += 1

        honour_sets = []
        wind_sets = []

        i = 0
        while i < len(hand_copy):
            if hand_copy[i][0].subtype == 'dragon':
                honour_sets.append(hand_copy.pop(i))
                i -= 1
            elif hand_copy[i][0].subtype == 'wind':
                wind_sets.append(hand_copy.pop(i))
                i -= 1
            i += 1

        if len(honour_sets) == 3 and all(len(full_set) == 3 for full_set in honour_sets):
            fan += 8
            return fan
        elif len(honour_sets) == 3:
            fan += 5
        else:
            dragon_sets = len([full_set for full_set in honour_sets if len(full_set) > 2])
            fan += dragon_sets

        if len(wind_sets) == 4 and all(len(full_set) == 3 for full_set in wind_sets):
            fan += 13
            return fan
        elif len(wind_sets) == 4:
            fan += 6
        else:
            if any(full_set[0].numchar == circle_wind and len(full_set) == 3 for full_set in wind_sets):
                fan += 1
            if any(full_set[0].numchar == ordered_cardinal[player_number] and
                   len(full_set) == 3 for full_set in wind_sets):
                fan += 1

        if all(hand_copy[i][0].subtype == hand_copy[i + 1][0].subtype for i in
               range(0, len(hand_copy) - 1)):
            if len(honour_sets) == 0 and len(wind_sets) == 0:
                fan += 5
            else:
                fan += 3

        i = 0
        while i < len(hand_copy) and len(hand_copy[i]) == 3:
            i += 1
        if i != len(hand_copy):
            hand_copy.pop(i)  # remove the eye, otherwise already removed in winds

        # dui dui wu
        if all(tile[0] == tile[1] for tile in hand_copy):
            fan += 3
        # assuming possible hands is structured correctly and can only contain a straight or a triplet
        elif all(tile[0].tiletype == "suit" and tile[1].tiletype == "suit" and
                 tile[0].numchar == tile[1].numchar + 1 for tile in hand_copy):  # ping wu
            fan += 1

        return fan * len(potential_hand) * 3 // 14  # normalised fan based on completion

    @staticmethod
    def score_hand(potential_hand: List[List[MahjongTile]], flowers: List[MahjongTile],
                   circle_wind, player_number) -> int:
        """
        Return a score for this hand, doesn't have to be complete (for potential fan)
        """
        if len(potential_hand) == 0:
            return 0
        hand_copy = copy.deepcopy(potential_hand)
        flower_copy = copy.deepcopy(flowers)
        fan = 0
        ordered_flower = ['plum', 'orchid', 'chrysanthemum', 'bamboo']
        ordered_season = ['summer', 'spring', 'autumn', 'winter']
        ordered_cardinal = ['east', 'south', 'west', 'north']
        if len(flower_copy) == 0:
            fan += 1
            print("No flowers")
        elif {'plum', 'orchid', 'chrysanthemum', 'bamboo'} <= {flower.numchar for flower in flower_copy}:
            fan += 2
            print("Full set of flowers")
        elif {'summer', 'spring', 'autumn', 'winter'} <= {flower.numchar for flower in flower_copy}:
            fan += 2
            print("Full set of flowers")
        else:
            if any(flower.numchar == ordered_flower[player_number] for flower in flower_copy):
                fan += 1
                print("Correct flowers")
            if any(season.numchar == ordered_season[player_number] for season in flower_copy):
                fan += 1
                print("Correct flowers")

        honour_sets = []
        wind_sets = []

        i = 0
        while i < len(hand_copy):
            if hand_copy[i][0].subtype == 'dragon':
                honour_sets.append(hand_copy.pop(i))
                i -= 1
            elif hand_copy[i][0].subtype == 'wind':
                wind_sets.append(hand_copy.pop(i))
                i -= 1
            i += 1

        if len(honour_sets) == 3 and all(len(full_set) == 3 for full_set in honour_sets):
            fan += 8
            print("Great dragons")
            return fan
        elif len(honour_sets) == 3:
            print("Small dragon")
            fan += 5
        else:
            dragon_sets = len([full_set for full_set in honour_sets if len(full_set) > 2])
            fan += dragon_sets
            for _ in range(dragon_sets):
                print("Dragon")

        if len(wind_sets) == 4 and all(len(full_set) == 3 for full_set in wind_sets):
            fan += 13
            print("Great winds")
            return fan
        elif len(wind_sets) == 4:
            fan += 6
            print("Minor winds")
        else:
            if any(full_set[0].numchar == circle_wind and len(full_set) == 3 for full_set in wind_sets):
                fan += 1
                print("Correct circle wind")
            if any(full_set[0].numchar == ordered_cardinal[player_number] and
                   len(full_set) == 3 for full_set in wind_sets):
                fan += 1
                print("Correct player wind")

        if all(hand_copy[i][0].subtype == hand_copy[i + 1][0].subtype for i in
               range(0, len(hand_copy) - 1)):
            if len(honour_sets) == 0 and len(wind_sets) == 0:
                fan += 5
                print("All one set")
            else:
                fan += 3
                print("Mixed one set")

        i = 0
        while i < len(hand_copy) and len(hand_copy[i]) == 3:
            i += 1
        if i != len(hand_copy):
            hand_copy.pop(i)  # remove the eye, otherwise already removed in winds

        # dui dui wu
        if all(tile[0] == tile[1] for tile in hand_copy):
            fan += 3
            print("All triplets")
        # assuming possible hands is structured correctly and can only contain a straight or a triplet
        elif all(tile[0].tiletype == "suit" and tile[1].tiletype == "suit" and
                 tile[0].numchar == tile[1].numchar + 1 for tile in hand_copy):  #ping wu
            fan += 1
            print("All straights")
        return fan

    def show_all_possible_sheungs(self, latest_tile: MahjongTile) -> \
            (Tuple[Tuple[int, int] | None, Tuple[int, int] | None, Tuple[int, int] | None]):
        """

        return a 3-tuple with None if the corresponding sheung is not possible, else the indices in
        self._hidden_hand of the corresponding tiles necessary to form the sheung
        first is for lower sheung, second for middle sheung, third for upper sheung
        """

        if latest_tile.tiletype != 'suit':
            return None, None, None
        sequenced_tiles = [-1, -1, -1, -1]
        lower_num = max(latest_tile.numchar - 2, 1)
        upper_num = min(latest_tile.numchar + 2, 9)
        # binary search
        index = bisect.bisect_left(self.hidden_hand,
                                   MahjongTile(tiletype=latest_tile.tiletype,
                                               subtype=latest_tile.subtype,
                                               numchar=lower_num)
                                   )
        upper_bound = MahjongTile(tiletype=latest_tile.tiletype,
                                  subtype=latest_tile.subtype,
                                  numchar=upper_num)
        while index < len(self.hidden_hand) and self.hidden_hand[index] < upper_bound:
            if self.hidden_hand[index].numchar == latest_tile.numchar - 2:
                sequenced_tiles[0] = index
            elif self.hidden_hand[index].numchar == latest_tile.numchar - 1:
                sequenced_tiles[1] = index
            elif self.hidden_hand[index].numchar == latest_tile.numchar + 1:
                sequenced_tiles[2] = index
            elif self.hidden_hand[index].numchar == latest_tile.numchar + 2:
                sequenced_tiles[3] = index
            index += 1

        if sequenced_tiles[0] == -1 or sequenced_tiles[1] == -1:
            lower_sheung = None
        else:
            lower_sheung = [sequenced_tiles[0], sequenced_tiles[1]]
        if sequenced_tiles[2] == -1 or sequenced_tiles[1] == -1:
            mid_sheung = None
        else:
            mid_sheung = [sequenced_tiles[1], sequenced_tiles[2]]
        if sequenced_tiles[3] == -1 or sequenced_tiles[2] == -1:
            high_sheung = None
        else:
            high_sheung = [sequenced_tiles[2], sequenced_tiles[3]]

        return lower_sheung, mid_sheung, high_sheung

    def decide_add_kong(self, latest_tile: MahjongTile, state: np.ndarray = None) -> bool:
        """
        Base functions check if a kong is possible. All inheriting functions
        should implement functionality of removing the tiles, and whether to
        go through with it
        """
        index = 0
        while index < len(self.hidden_hand) - 2 and self.hidden_hand[index] != latest_tile:
            index += 1
        if index >= len(self.hidden_hand) - 2:
            return False
        elif self.hidden_hand[index + 1] != latest_tile or self.hidden_hand[index + 2] != latest_tile:
            return False

        return True

    def decide_win(self, latest_tile, circle_wind, state: np.ndarray = None) -> bool:
        """
        Base functions check if a win is can be claimed. All inheriting functions
        should implement functionality of deciding whether to claim or not
        """
        self.add_tile(latest_tile)
        if not self.check_winning_hand(circle_wind):
            self.hidden_hand.remove(latest_tile)
            return False
        return True

    def decide_sheung(self, latest_tile: MahjongTile, state: np.array = None) -> Tuple[int, int]:
        """
        Base functions check if a sheung can be claimed. All inheriting functions
        should implement functionality of deciding whether to claim or not and
        actually claiming it
        """
        raise NotImplementedError

    def sheung_possible(self, latest_tile) -> bool:
        """
        Return if a sheung is possible
        :param latest_tile:
        :return:
        """
        possible_sheungs = self.show_all_possible_sheungs(latest_tile)
        if all(sheung is None for sheung in possible_sheungs):
            return False

        return True

    def decide_pong(self, discarded_tile: MahjongTile, state: np.array = None) -> bool:
        """
        Base functions check if a pong is can be claimed. All inheriting functions
        should implement functionality of deciding whether to claim or not and executing
        the claim
        """
        index = bisect.bisect_left(self.hidden_hand, discarded_tile)
        if (index >= len(self.hidden_hand) - 1 or index < 1 or self.hidden_hand[index] != discarded_tile or
                (self.hidden_hand[index + 1] != discarded_tile and self.hidden_hand[index - 1] != discarded_tile)):
            return False

        return True

    def discard_tile(self, state: np.ndarray = None) -> MahjongTile:
        """
        Discard a tile from hand
        """
        raise NotImplementedError

    def add_tile(self, drawn_tile: MahjongTile):
        """
        Add the tile to the hand in a sorted order
        """
        bisect.insort(self.hidden_hand, drawn_tile)

    def print_hand(self):
        """
        Print out currnet hand
        """
        print("PLAYER " + str(self.player_id))
        for tile in self.hidden_hand:
            print(tile)
        print("==================")
        print("REVEALED SETS")
        for subset in self.revealed_sets:
            print("SET START")
            for tile in subset:
                print(tile)
            print("SET END")
        print("==================")
        print("FLOWERS")
        for flower in self.flowers:
            print(flower)
        print("==================")

    # RL ENCODING ========================================================================

    def encode_hidden_hand(self) -> np.ndarray:
        """
        Encode player's hidden hand
        """
        vec = np.zeros(34, dtype=int)
        for tile in self.hidden_hand:
            vec[tile.to_index()] += 1
        return vec

    def encode_revealed_hand(self) -> np.ndarray:
        """
        Encode player's revealed hand (completed sets)
        """
        vec = np.zeros(34, dtype=int)
        for tile in [tile for subset in self.revealed_sets for tile in subset]:
            vec[tile.to_index()] += 1
        return vec

    def encode_discarded_pile(self):
        """
        Encode player's discard pile
        """
        vec = np.zeros(34, dtype=int)
        for tile in self.discard_pile:
            vec[tile.to_index()] += 1
        return vec

    def count_flower_fan(self) -> int:
        """
        Count number of faan by flower
        :return:
        """
        return 0
