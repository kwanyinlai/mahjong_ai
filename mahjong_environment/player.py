"""
player.py - represents a player in a MahjongGame
"""

from __future__ import annotations

import bisect
import copy
from typing import List, Optional, Set, Tuple

import numpy as np

from mahjong_environment.tile import MahjongTile


class Player:
    """
    Class which is compatible with MahjongGame in mahjong_game.py
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

    def _set_hand(self) -> None:
        """
        Set the hand for a player to a specified set
        !!!! FOR TESTING PURPOSES ONLY !!!!
        SHOULD NOT BE USED IN REAL SITUATIONS
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
        :param circle_wind: the current circle wind in {"north", "east",
                            "south", "west"}
        :return: return True if we have a winning hand, otherwise False
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

    def check_thirteen_orphans(self):
        """
        Edge case of thirteen orphans to be checked with winning hand
        """
        pair_exists = any(self.hidden_hand[i] == self.hidden_hand[i + 1] for i in range(len(self.hidden_hand) - 1))
        all_orphans = self.orphans <= {tile for tile in self.hidden_hand}
        return len(self.hidden_hand) == 14 and pair_exists and all_orphans

    def _set_orphans(self):
        """
        Set thirteen orphans attribute
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
        tile14 = MahjongTile(tiletype="honour", subtype="wind", numchar='west')
        self.orphans = {tile1, tile2, tile3, tile4, tile5, tile6, tile7, tile8, tile9, tile10,
                        tile11, tile12, tile13}

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

    def decide_win(self, latest_tile, circle_wind, player_number: int, state: np.ndarray = None) -> bool:
        """
        Base functions check if a win is can be claimed. All inheriting functions
        should implement functionality of deciding whether to claim or not
        """
        if latest_tile is None:
            return False
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
        vec = np.zeros(34, dtype=np.float32)
        for tile in self.hidden_hand:
            vec[tile.to_index()] += 1
        return vec / 4.0

    def encode_revealed_hand(self) -> np.ndarray:
        """
        Encode player's revealed hand (completed sets)
        Each revealed set is separated by 34. For instance, if
        we have three revealed sets, then the first 0-33 elements of the array
        represent the first, 34-67 are the second set, etc.
        Size of 34 * 4
        """
        revealed_vecs = np.zeros(34 * 4, dtype=np.float32)
        for i in range(len(self.revealed_sets)):
            for tile in self.revealed_sets[i]:
                revealed_vecs[i * 34 + tile.to_index()] += 1
        return revealed_vecs / 4.0

    def encode_discarded_pile(self):
        """
        Encode player's discard pile
        """
        vec = np.zeros(34, dtype=np.float32)
        for tile in self.discard_pile:
            vec[tile.to_index()] += 1
        return vec / 4.0

    def encode_flower_set(self):
        vec = np.zeros(8, dtype=np.float32)
        flower_mapping = {'plum': 0, 'orchid': 1, 'chrysanthemum': 2, 'bamboo': 3,
                          'summer': 4, 'spring': 5, 'autumn': 6, 'winter': 7}
        for flower in self.flowers:
            vec[flower_mapping[flower.numchar]] += 1
        return vec

    def count_flower_fan(self) -> int:
        """
        Count number of faan by flower
        :return:
        """
        return 0

    def get_hand_length(self):
        return len(self.hidden_hand)

    def prepare_action(self, discarded_tile, circle_wind, player_number) -> Tuple[Optional[int], Optional[str],
            Optional[Tuple[int, int]]]:
        if self.decide_win(discarded_tile, circle_wind, player_number):
            return self.player_id, "win", None
        if self.decide_add_kong(discarded_tile):
            return self.player_id, "kong", None
        if self.decide_pong(discarded_tile):
            return self.player_id, "pong", None
        if (sheung_indices := self.decide_sheung(discarded_tile)) and player_number == (self.player_id - 1) % 4:
            return self.player_id, "sheung", sheung_indices
        return None, None, None

    @staticmethod
    def player_from_player_state(player_state, player_id, player_order):

        player = Player(player_id=player_id, player_order=player_order)

        hidden_hand_vec = player_state[:34]
        player.hidden_hand = Player.create_tile_pile(hidden_hand_vec)

        revealed_sets_vec = player_state[34:34 * 5]
        player.revealed_sets = Player.create_revealed_sets(revealed_sets_vec)

        discarded_pile_vec = player_state[34 * 5: 34 * 6]
        player.discard_pile = Player.create_tile_pile(discarded_pile_vec)
        player.hidden_hand.sort()

        flower_vec = player_state[34 * 6:34 * 6 + 8]
        player.flowers = Player.create_flowers(flower_vec)

        return player

    @staticmethod
    def create_tile_pile(hand_vec):
        """
        Generate from normalised vector
        :param hand_vec:
        :return:
        """
        hand = []
        for i in range(34):
            count = int(round(hand_vec[i] * 4))
            for _ in range(count):
                tile = MahjongTile.index_to_tile(i)
                hand.append(tile)
        return hand

    @staticmethod
    def create_revealed_sets(revealed_sets_vec):
        revealed_sets = []
        for i in range(4):
            revealed_set = []
            for j in range(34):
                count = int(revealed_sets_vec[i * 34 + j] * 4)
                for _ in range(count):
                    tile = MahjongTile.index_to_tile(j)
                    revealed_set.append(tile)
            if revealed_set:
                revealed_sets.append(revealed_set)
        return revealed_sets

    @staticmethod
    def create_flowers(flower_vec):
        flowers = []
        flower_mapping = {0: 'plum', 1: 'orchid', 2: 'chrysanthemum', 3: 'bamboo',
                          4: 'summer', 5: 'spring', 6: 'autumn', 7: 'winter'}
        for i in range(8):
            count = int(flower_vec[i])  # Reverse the normalization
            for _ in range(count):
                if flower_mapping[i] in {'plum', 'orchid', 'chrysanthemum', 'bamboo'}:
                    flower = MahjongTile(tiletype='flower', subtype='flower', numchar=flower_mapping[i])
                else:
                    flower = MahjongTile(tiletype='flower', subtype='season', numchar=flower_mapping[i])
                flowers.append(flower)
        return flowers
