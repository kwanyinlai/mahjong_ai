from __future__ import annotations

import bisect
from typing import List, Tuple

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

    def __init__(self, player_id):
        self.player_id = player_id
        self.hidden_hand = []
        self.revealed_sets = []
        self.flowers = []
        self.discard_pile = []
        self.total_score = 0


    def soft_reset(self):
        self.hidden_hand = []
        self.revealed_sets = []
        self.flowers = []
        self.discard_pile = []


    def check_claims(self, circle_wind, player_number, latest_tile: MahjongTile = None,
                     state: np.ndarray = None) -> Tuple[bool, bool, bool]:
        """
        WIN_CLAIM
        PONG
        ADD_KONG
        SHEUNG
        DISCARD
        """
        if self.decide_win(latest_tile, circle_wind, player_number, state):
            return True, False, False
        if latest_tile is not None:
            if self.decide_pong(latest_tile, state):
                return False, True, False
            elif self.decide_add_kong(latest_tile, state):
                return False, False, True

        return False, False, False

    def set_hand(self):
        """
        Set hand for a player for testing
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

    def check_winning_hand(self, circle_wind: str, player_number: int) -> bool:
        """
        Check whether the player currently has a winning hand
        """
        possible_hands = []
        i = 0
        while i < len(self.hidden_hand) - 1:
            tile = self.hidden_hand[i]
            potential_hand = []
            if self.hidden_hand[i + 1] == tile:  # check all possible combinations of 'eyes' first for efficiency
                remaining_hand = self.hidden_hand.copy()
                potential_hand.append([remaining_hand.pop(i), remaining_hand.pop(i)])

                if self.can_fit_into_set(remaining_hand, potential_hand):
                    potential_hand += self.revealed_sets
                    possible_hands.append(potential_hand)

            i += 1

        possible_hands = sorted(possible_hands, key=lambda hand: Player.score_hand(hand, self.flowers, circle_wind, 0))
        # TODO: Scoring is not rigorously tested yet but should work
        return possible_hands != []


    def check_thirteen_orphans(self, remaining_hand, potential_hand):
        """
        Edge case of thirteen orphans to be checked with winning hand
        """
        pass

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
    def score_hand(potential_hand: List[List[MahjongTile]], flowers: List[MahjongTile],
                   circle_wind, player_number) -> int:
        """
        Return a score for this hand, doesn't have to be complete (for potential fan)
        """
        fan = 0
        ordered_flower = ['plum', 'orchid', 'chrysanthemum', 'bamboo']
        ordered_season = ['summer', 'spring', 'autumn', 'winter']
        ordered_cardinal = ['east', 'south', 'west', 'north']
        # TODO: Need a potential faan function which finds completed sets
        # TODO: Maybe use my check winning hands function but don't discard
        # TODO: incomplete hands and just toss away the incomplete part and return
        # TODO: the fan score of the remaining hand and the distance from completion.
        if len(flowers) == 0:
            fan += 1
        elif ['plum', 'orchid', 'chrysanthemum', 'bamboo'] <= [flower.numchar for flower in flowers]:
            fan += 2
        elif ['summer', 'spring', 'autumn', 'winter'] <= [flower.numchar for flower in flowers]:
            fan += 2
        else:
            if any(flower.numchar == ordered_flower[player_number] for flower in flowers):
                fan += 1
            if any(season.numchar == ordered_season[player_number] for season in flowers):
                fan += 1

        honour_sets = []
        wind_sets = []

        i = 0
        while i < len(potential_hand):
            if potential_hand[i][0].subtype == 'honour':
                honour_sets.append(potential_hand.pop(i))
            elif potential_hand[i][0].subtype == 'wind':
                wind_sets.append(potential_hand.pop(i))
            i += 1

        if len(honour_sets) == 3 and all(len(full_set) == 3 for full_set in honour_sets):
            fan += 8
            return fan
        elif len(honour_sets) == 3:
            fan += 5
        else:
            fan += len([full_set for full_set in honour_sets if len(full_set) > 2])

        if len(wind_sets) == 4 and all(len(full_set) == 3 for full_set in wind_sets):
            fan += 13
            return fan
        elif len(wind_sets) == 4:
            fan += 6
        else:
            if any(full_set == circle_wind and len(full_set) == 3 for full_set in wind_sets):
                fan += 1
            elif any(full_set == ordered_cardinal[player_number] and len(full_set) == 3 for full_set in wind_sets):
                fan += 1

        if all(potential_hand[i][0].subtype == potential_hand[i + 1][0].subtype for i in
               range(0, len(potential_hand) - 1)):
            if len(honour_sets) == 0 and len(wind_sets) == 0:
                fan += 5
            else:
                fan += 3

        i = 0

        while i < len(potential_hand) and len(potential_hand[i]) < 2:
            i += 1
        potential_hand.pop(i)  # remove the eye

        # dui dui wu
        if all(tile[0] == tile[1] for tile in potential_hand):
            fan += 3
        # assuming possible hands is structured correctly and can only contain a straight or a triplet
        elif all(tile[0].tiletype == "suit" and tile[1].tiletype == "suit" and
                 tile[0].numchar == tile[1].numchar + 1 for tile in potential_hand):  #ping wu
            fan += 1

        return fan

    def show_all_possible_sheungs(self, latest_tile: MahjongTile) -> \
            (Tuple[Tuple[int, int] | None, Tuple[int, int] | None, Tuple[int, int] | None]):
        """

        return a 3 item tuple with None if the corresponding sheung is not possible, else the indices in
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

    def decide_add_kong(self, latest_tile: MahjongTile, state: np.array = None) -> bool:
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

    def decide_win(self, latest_tile, circle_wind, player_number, state: np.array = None) -> bool:
        """
        Base functions check if a win is can be claimed. All inheriting functions
        should implement functionality of deciding whether to claim or not
        """

        self.add_tile(latest_tile)
        if not self.check_winning_hand(circle_wind, player_number):
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

    def discard_tile(self, state: np.array = None) -> MahjongTile:
        """
        Discard a tile from hand
        """
        raise NotImplementedError

    def add_tile(self, drawn_tile: MahjongTile):
        """
        Add the tile to the hand in a sorted order
        """
        bisect.insort(self.hidden_hand, drawn_tile)
        # if len(self.hidden_hand) + 3*len(self.revealed_sets) != 14:
        #     print("ERROR FOR PLAYER" + str(self.player_id))
        #     self.print_hand()
        #     print("REVEALED")
        #     for subset in self.revealed_sets:
        #         print("SET START")
        #         for tile in subset:
        #             print(tile)
        #         print("SET END")

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
