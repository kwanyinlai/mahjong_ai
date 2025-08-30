from __future__ import annotations
import random
import bisect
from typing import Union, List, Optional, Tuple


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


class MahjongGame:
    """
    Represents one Mahjong Game
    """
    tiles: List[MahjongTile]
    players: List[Player]
    current_player_no: int
    current_player: Player
    discarded_tiles: List[MahjongTile] = []
    latest_tile: MahjongTile = None
    game_over: bool
    winner: Player

    def __init__(self):
        self.players = [RandomBot(i) for i in range(4)]
        self.tiles = MahjongGame.initialize_tiles()
        self.setup_game()

    @staticmethod
    def test_sheung():
        player1 = YesBot(1)
        player2 = YesBot(2)
        player3 = YesBot(3)
        player4 = YesBot(4)
        players = [player1, player2, player3, player4]

        tile1 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=2)
        tile2 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=3)
        tile3 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=4)
        tile4 = MahjongTile(tiletype="suit", subtype="circle", numchar=5)
        tile5 = MahjongTile(tiletype="suit", subtype="circle", numchar=6)
        tile6 = MahjongTile(tiletype="suit", subtype="circle", numchar=7)
        tile7 = MahjongTile(tiletype="suit", subtype="number", numchar=3)
        tile8 = MahjongTile(tiletype="honour", subtype="dragon", numchar="white")
        tile9 = MahjongTile(tiletype="suit", subtype="number", numchar=6)
        player1.hidden_hand = [tile1, tile2, tile4, tile5, tile6, tile7, tile7, tile7, tile8, tile8, tile8,
                               tile9, tile9]

        player1.hidden_hand.sort()
        print(player1.decide_sheung(tile3))

    @staticmethod
    def test_pong():
        player1 = YesBot(1)
        player2 = YesBot(2)
        player3 = YesBot(3)
        player4 = YesBot(4)
        players = [player1, player2, player3, player4]

        tile1 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=2)
        tile2 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=3)
        tile3 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=4)
        tile4 = MahjongTile(tiletype="suit", subtype="circle", numchar=5)
        tile5 = MahjongTile(tiletype="suit", subtype="circle", numchar=6)
        tile6 = MahjongTile(tiletype="suit", subtype="circle", numchar=7)
        tile7 = MahjongTile(tiletype="suit", subtype="number", numchar=3)
        tile8 = MahjongTile(tiletype="honour", subtype="dragon", numchar="white")
        tile9 = MahjongTile(tiletype="suit", subtype="number", numchar=6)
        player1.hidden_hand = [tile2, tile3, tile4, tile5, tile6, tile7, tile7, tile8, tile8, tile8,
                               tile9, tile9]
        player1.hidden_hand.sort()
        print(player1.decide_pong(tile7))

    @staticmethod
    def test_win_claim():
        player1 = YesBot(1)
        player2 = YesBot(2)
        player3 = YesBot(3)
        player4 = YesBot(4)
        players = [player1, player2, player3, player4]
        mahjong_game = MahjongGame()
        mahjong_game.players = players
        mahjong_game.initialize_tiles()
        mahjong_game.setup_game()

        tile1 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=2)
        tile2 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=3)
        tile3 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=4)
        tile4 = MahjongTile(tiletype="suit", subtype="circle", numchar=5)
        tile5 = MahjongTile(tiletype="suit", subtype="circle", numchar=6)
        tile6 = MahjongTile(tiletype="suit", subtype="circle", numchar=7)
        tile7 = MahjongTile(tiletype="suit", subtype="number", numchar=3)
        tile8 = MahjongTile(tiletype="honour", subtype="dragon", numchar="white")
        tile9 = MahjongTile(tiletype="suit", subtype="number", numchar=6)
        player1.hidden_hand = [tile2, tile3, tile4, tile5, tile6, tile7, tile7, tile7, tile8, tile8, tile8,
                               tile9, tile9]
        player1.hidden_hand.sort()

        print("WIN POSSIBLE: " + str(player1.decide_win(tile1)))

    @staticmethod
    def test_add_kong():
        player1 = YesBot(1)
        player2 = YesBot(2)
        player3 = YesBot(3)
        player4 = YesBot(4)
        players = [player1, player2, player3, player4]

        tile1 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=2)
        tile2 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=3)
        tile3 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=4)
        tile4 = MahjongTile(tiletype="suit", subtype="circle", numchar=5)
        tile5 = MahjongTile(tiletype="suit", subtype="circle", numchar=6)
        tile6 = MahjongTile(tiletype="suit", subtype="circle", numchar=7)
        tile7 = MahjongTile(tiletype="suit", subtype="number", numchar=3)
        tile8 = MahjongTile(tiletype="honour", subtype="dragon", numchar="white")
        tile9 = MahjongTile(tiletype="suit", subtype="number", numchar=6)
        player1.hidden_hand = [tile1, tile2, tile3, tile4, tile5, tile6, tile7, tile7, tile7, tile8, tile8, tile8,
                               tile9, tile9]
        player1.hidden_hand.sort()
        print(player1.decide_add_kong(tile7))

    @staticmethod
    def test_win_scenario():
        player1 = YesBot(1)
        player2 = YesBot(2)
        player3 = YesBot(3)
        player4 = YesBot(4)
        players = [player1, player2, player3, player4]

        tile1 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=2)
        tile2 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=3)
        tile3 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=4)
        tile4 = MahjongTile(tiletype="suit", subtype="circle", numchar=5)
        tile5 = MahjongTile(tiletype="suit", subtype="circle", numchar=6)
        tile6 = MahjongTile(tiletype="suit", subtype="circle", numchar=7)
        tile7 = MahjongTile(tiletype="suit", subtype="number", numchar=3)
        tile8 = MahjongTile(tiletype="honour", subtype="dragon", numchar="white")
        tile9 = MahjongTile(tiletype="suit", subtype="number", numchar=6)
        player1.hidden_hand = [tile1, tile2, tile3, tile4, tile5, tile6, tile7, tile7, tile7, tile8, tile8, tile8,
                               tile9, tile9]

        player1.hidden_hand.sort()

        player1.check_winning_hand()

    @staticmethod
    def initialize_tiles() -> List[MahjongTile]:
        """
        Initialises the set of tiles that can be drawn in a game
        """
        tiles = []
        for suit in ('circle', 'bamboo', 'number'):
            for i in range(1, 10):
                for j in range(1, 5):
                    tiles.append(MahjongTile(tiletype='suit', subtype=suit, numchar=j))

        for colour in ('red', 'green', 'white'):
            for i in range(0, 4):
                tiles.append(MahjongTile(tiletype='honour', subtype='dragon', numchar=colour))

        for cardinality in ('north', 'south', 'east', 'west'):
            for i in range(0, 4):
                tiles.append(MahjongTile(tiletype='honour', subtype='wind', numchar=cardinality))

        for flower in ('plum', 'orchid', 'chrysanthemum', 'bamboo'):
            tiles.append(MahjongTile(tiletype='flower', subtype='flower', numchar=flower))
        for season in ('summer', 'spring', 'autumn', 'winter'):
            tiles.append(MahjongTile(tiletype='flower', subtype='season', numchar=season))

        return tiles

    def initialise_players(self):
        """
        Add all players into the game
        """
        player1 = RandomBot(1)
        player2 = RandomBot(2)
        player3 = RandomBot(3)
        player4 = RandomBot(4)
        self.players = [player1, player2, player3, player4]

    def initialise_player_hands(self, starting_number: int):
        """
        Starting number is the index of the player we start with
        Give 13 tiles to each player, then replace with 13 tiles, and then give
        a 14th tile to the first person to play.
        """
        # clear player hands
        current_player_number = starting_number
        current_player = self.players[current_player_number]
        while len(self.players[starting_number].hidden_hand) < 14:
            self.players[current_player_number].add_tile(self.draw_tile())
            current_player_number += 1
            current_player_number %= 4
            current_player = self.players[current_player_number]
        for player_redraw in self.players:  # TODO: Fix this to go in right order, while loop ntof or loop

            last_tile = player_redraw.hidden_hand.pop()
            while last_tile.tiletype == 'flower':
                print("FLOWER REDRAW PLAYER " + str(player_redraw.player_id))
                last_tile = self.draw_tile()

            player_redraw.add_tile(last_tile)

    def setup_game(self):
        """
        Shuffle tiles and deal them to players
        """
        print("SETUP")
        random.shuffle(self.tiles)
        self.initialise_player_hands(0)
        self.current_player_no = 0
        self.current_player = self.players[self.current_player_no]

        self.discard_tile(self.current_player.discard_tile(self))
        print("SETUP COMPLETE")

    def play_round(self):
        """
        Play one round of a MahjongGame to the end until a draw or win
        """
        game_over = False
        while not game_over and len(self.tiles) != 0:
            action_taken = False
            temp_player = self.current_player

            if self.latest_tile is not None:
                temp_player_number = (self.current_player_no + 1) % 4
                temp_player = self.players[temp_player_number]

                for i in range(0, 3):
                    temp_player = self.players[temp_player_number]
                    if temp_player.decide_pong(self.latest_tile) or temp_player.decide_add_kong(self.latest_tile):
                        print("Player " + str(temp_player.player_id) + "decided to pong")
                        break
                    if temp_player.decide_win(self.latest_tile):
                        game_over = True
                        print("CLAIMED WIN")
                        break

                    temp_player_number += 1
                    temp_player_number %= 4
                if not action_taken and self.players[temp_player_number].decide_sheung(self.latest_tile):
                    action_taken = True
            if action_taken:
                temp_player.discard_tile(self)
                self.next_turn(temp_player)
            else:
                self.current_player.draw_tile(self)
                self.current_player.discard_tile(self)
                self.next_turn()
        print("==================")
        print("GAME DRAW")
        for player in game.players:
            player.print_hand()

    def draw_tile(self) -> MahjongTile:
        """
        Return a tile and remove it from the deck
        """
        return self.tiles.pop()

    def discard_tile(self, discarded_tile: MahjongTile):
        """
        Add the latest tile to the discarded pile and set the latest discarded tile
        to this
        """
        self.latest_tile = discarded_tile
        self.discarded_tiles.append(discarded_tile)

    def next_turn(self, player_skip: Optional[Player] = None):
        """

        :param player_skip:
        """
        if player_skip:
            self.current_player_no = player_skip.player_id
            self.current_player = self.players[self.current_player_no]
        self.current_player_no = (self.current_player_no + 1) % 4
        self.current_player = self.players[self.current_player_no]


class Player:
    """
    Represents a player in a MahjongGame
    """
    player_id: int
    hidden_hand: List[MahjongTile]  # assume sorted
    revealed_sets: List[List[MahjongTile]] = []
    total_score: int
    fan: int
    flowers: List[MahjongTile]

    def __init__(self, player_id):
        self.player_id = player_id
        self.hidden_hand = []
        self.total_score = 0

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

    def draw_tile(self, game_state: MahjongGame):
        """
        Draw a tile and redraw if flower, or check if the player can
        make any decisions with the drawn tile outside of discarding,
        otherwise, add the tile to hand
        """
        drawn_tile = game_state.draw_tile()
        while drawn_tile.subtype in ('flower', 'season'):
            self.revealed_sets.append([drawn_tile])
            drawn_tile = game_state.draw_tile()
        if self.decide_add_kong(drawn_tile):
            print("YOU KONGED")
        elif self.decide_win(drawn_tile):
            print("YOU WIN!!!!")
        else:
            self.add_tile(drawn_tile)
            print("Player " + str(self.player_id) + " put the following tile into your hand")
            print(drawn_tile)

    def check_winning_hand(self) -> bool:
        """
        Check whether the player currently has a winning hand
        """
        possible_hands = []
        i = 0
        while i < len(self.hidden_hand) - 1:  # TODO: stuck in a loop here (idk if it's looped rn so hold on to
            tile = self.hidden_hand[i]  # TODO: this thought)
            potential_hand = []
            if self.hidden_hand[i + 1] == tile:  # check all possible combinations of 'eyes' first for efficiency
                remaining_hand = self.hidden_hand.copy()
                potential_hand.append([remaining_hand.pop(i), remaining_hand.pop(i)])

                if self.can_fit_into_set(remaining_hand, potential_hand):
                    potential_hand += self.revealed_sets
                    possible_hands.append(potential_hand)

            i += 1
        # print(possible_hands)
        # if possible_hands:
        #     for hand in possible_hands:
        #         print("HAND")
        #         for set in hand:
        #             print("SET")
        #             for tile in set:
        #                 print(tile)
        #             print("END SET")
        #         print("HAND END")
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
    def filter_by_fan(self, potential_hand: List[List[MahjongTile]], wind) -> int:
        """
        Sort the winning hands by number of fan
        """
        fan = 0
        # check flowers TODO: Figure out later
        # count honours
        honour_sets = []
        wind_sets = []

        i = 0
        while i < len(potential_hand):
            if potential_hand[i][0].subtype == 'honour':
                honour_sets.append(potential_hand.pop(i))
            elif potential_hand[i][0].subtype == 'wind':
                wind_sets.append(potential_hand.pop(i))
            i += 1
        # great dragon

        # TODO: Figure out later
        # small dragon
        # TODO: Figure out later
        # count honour by fan
        fan += len([full_set for full_set in honour_sets if len(full_set) > 2])
        # check wind (current wind)
        fan += len([full_set for full_set in honour_sets if len(full_set) > 2 and full_set[0].numchar == wind])
        # great winds
        # TODO: Figure out later
        # small winds
        # TODO: Figure out later
        # dui dui wu
        if all(first_tile == second_tile for first_tile, second_tile in potential_hand):
            fan += 3
            # assuming possible hands is structured correctly and can only contain a straight or a triplet
        elif all(first_tile.numchar == second_tile.numchar + 1 for first_tile, second_tile in potential_hand):  #ping wu
            fan += 1  # need to isolate the eye somehow
        # qing yat sik
        if all(potential_hand[i][0].subtype == potential_hand[i + 1][0].subtype for i in
               range(0, len(potential_hand) - 1)):
            if len(honour_sets) == 0 and len(wind_sets) == 0:
                fan += 5
            else:
                fan += 3

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

        # binary search
        index = bisect.bisect_left(self.hidden_hand,
                                   MahjongTile(tiletype=latest_tile.tiletype,
                                               subtype=latest_tile.subtype,
                                               numchar=latest_tile.numchar - 2)
                                   )
        upper_bound = MahjongTile(tiletype=latest_tile.tiletype,
                                  subtype=latest_tile.subtype,
                                  numchar=latest_tile.numchar + 2)
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

    def decide_add_kong(self, latest_tile: MahjongTile) -> bool:
        """
        Base functions check if a kong is possible. All inheriting functions
        should implement functionality of removing the tiles, and whether to
        go through with it
        """
        index = 0
        while index < len(self.hidden_hand) - 2 and self.hidden_hand[index] != latest_tile:
            index += 1
        if index == len(self.hidden_hand) - 2:
            return False
        elif self.hidden_hand[index + 1] != latest_tile or self.hidden_hand[index + 2] != latest_tile:
            return False

        return True

    def decide_win(self, latest_tile) -> bool:
        """
        Base functions check if a win is can be claimed. All inheriting functions
        should implement functionality of deciding whether to claim or not
        """
        self.add_tile(latest_tile)
        if not self.check_winning_hand():
            self.hidden_hand.remove(latest_tile)
            return False
        return True

    def decide_sheung(self, latest_tile: MahjongTile) -> bool:
        """
        Base functions check if a sheung can be claimed. All inheriting functions
        should implement functionality of deciding whether to claim or not and
        actually claiming it
        """
        possible_sheungs = self.show_all_possible_sheungs(latest_tile)
        if all(sheung is None for sheung in possible_sheungs):
            return False

        return True

    def decide_pong(self, discarded_tile: MahjongTile) -> bool:
        """
        Base functions check if a pong is can be claimed. All inheriting functions
        should implement functionality of deciding whether to claim or not and executing
        the claim
        """
        index = bisect.bisect_left(self.hidden_hand, discarded_tile)
        if self.hidden_hand[index] != discarded_tile or (self.hidden_hand[index + 1] != discarded_tile and
                                                         self.hidden_hand[index - 1] != discarded_tile):
            return False

        return True

    def discard_tile(self, game_state: MahjongGame) -> MahjongTile:
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


class RandomBot(Player):
    def decide_pong(self, tile: MahjongTile):
        if not super().decide_add_kong(tile):
            return False
        is_pong = random.choice([True, False])
        if is_pong:
            self.hidden_hand.remove(tile)
            self.hidden_hand.remove(tile)  # TODO: im lazy to implement efficient removal right now using sorted
            self.revealed_sets.append([tile, tile, tile])

        return is_pong

    def decide_add_kong(self, latest_tile) -> bool:
        if not super().decide_add_kong(latest_tile):
            return False

        is_kong = random.choice([True, False])  # doesn't work because check if kong
        if is_kong:
            self.hidden_hand.remove(latest_tile)
            self.hidden_hand.remove(latest_tile)
            self.hidden_hand.remove(latest_tile)  # TODO: im lazy to implement efficient removal right now using sorted
            self.revealed_sets.append([latest_tile, latest_tile, latest_tile])
        return is_kong

    def decide_win(self, latest_tile):
        return super().decide_win(latest_tile)
        # always claim win when possible

    def decide_sheung(self, latest_tile) -> bool:
        possible_sheungs = self.show_all_possible_sheungs(latest_tile)
        if all(sheung is None for sheung in possible_sheungs):
            return False
        is_sheung = random.choice([True, False])
        if is_sheung:
            decided_sheung = random.choice([indices for indices in possible_sheungs if indices is not None])
            for i in range(0, len(decided_sheung)):
                self.hidden_hand.pop(decided_sheung[i] - i)

        return is_sheung

    def discard_tile(self, game_state: MahjongGame) -> MahjongTile:
        removed_tile = random.choice(self.hidden_hand)
        self.hidden_hand.remove(removed_tile)
        print("PLAYER " + str(self.player_id) + " DISCARDED")
        print(removed_tile)
        return removed_tile


class YesBot(Player):
    def decide_pong(self, tile: MahjongTile):
        if not super().decide_pong(tile):
            return False

        self.hidden_hand.remove(tile)
        self.hidden_hand.remove(tile)  # TODO: im lazy to implement efficient removal right now using sorted
        self.revealed_sets.append([tile, tile, tile])

        return True

    def decide_add_kong(self, latest_tile) -> bool:
        if not super().decide_add_kong(latest_tile):
            return False
        self.hidden_hand.remove(latest_tile)
        self.hidden_hand.remove(latest_tile)
        self.hidden_hand.remove(latest_tile)  # TODO: im lazy to implement efficient removal right now using sorted
        self.revealed_sets.append([latest_tile, latest_tile, latest_tile])
        return True

    def decide_win(self, latest_tile):
        return super().decide_win(latest_tile)

    def decide_sheung(self, latest_tile) -> bool:
        possible_sheungs = self.show_all_possible_sheungs(latest_tile)

        if all(sheung is None for sheung in possible_sheungs):
            return False

        decided_sheung = random.choice([indices for indices in possible_sheungs if indices is not None])
        for i in range(0, len(decided_sheung)):
            self.hidden_hand.pop(decided_sheung[i] - i)

        return True

    def discard_tile(self, game_state: MahjongGame) -> MahjongTile:
        removed_tile = random.choice(self.hidden_hand)
        self.hidden_hand.remove(removed_tile)
        print("PLAYER " + str(self.player_id) + " DISCARDED")
        print(removed_tile)
        return removed_tile


class BasicBot(Player):
    def decide_pong(self, tile: MahjongTile):
        if not super().decide_pong(tile):
            return False

        self.hidden_hand.remove(tile)
        self.hidden_hand.remove(tile)  # TODO: im lazy to implement efficient removal right now using sorted
        self.revealed_sets.append([tile, tile, tile])

        return True

    def decide_add_kong(self, latest_tile) -> bool:
        if not super().decide_add_kong(latest_tile):
            return False
        self.hidden_hand.remove(latest_tile)
        self.hidden_hand.remove(latest_tile)
        self.hidden_hand.remove(latest_tile)  # TODO: im lazy to implement efficient removal right now using sorted
        self.revealed_sets.append([latest_tile, latest_tile, latest_tile])
        return True

    def decide_win(self, latest_tile):
        return super().decide_win(latest_tile)

    def decide_sheung(self, latest_tile) -> bool:
        possible_sheungs = self.show_all_possible_sheungs(latest_tile)

        if all(sheung is None for sheung in possible_sheungs):
            return False

        decided_sheung = random.choice([indices for indices in possible_sheungs if indices is not None])
        for i in range(0, len(decided_sheung)):
            self.hidden_hand.pop(decided_sheung[i] - i)

        return True

    def discard_tile(self, game_state: MahjongGame) -> MahjongTile:
        removed_tile = random.choice(self.hidden_hand)
        self.hidden_hand.remove(removed_tile)
        print("PLAYER " + str(self.player_id) + " DISCARDED")
        print(removed_tile)
        return removed_tile


if __name__ == "__main__":
    game = MahjongGame()
    game.play_round()

    # MahjongGame.test_win_scenario()
    # MahjongGame.test_win_claim()

# TODO: Need to play the next player - doesn't work right now
