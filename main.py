from __future__ import annotations

import random
import bisect
from typing import Union, List, Optional, Tuple


class Tiles:
    tiletype: str
    subtype: str
    numchar: Union[int,str]
    discarded: bool = False
    discarded_by: Optional[Player] = None

    def __hash__(self):
        return hash((self.tiletype, self.subtype, self.numchar))

    def __init__(self, tiletype: str, subtype: str, numchar: Union[int, str] = -1 ):
        tiletype = tiletype.lower()
        if tiletype not in ('suit', 'honour', 'flower'):
            raise ValueError("Invalid tile type")
        else:
            self.tiletype = tiletype
        if tiletype == 'suit' and subtype not in ('circle', 'bamboo', 'number'):
            raise ValueError("Invalid subtype")
        elif tiletype == 'honours' and subtype not in ('wind', 'dragon'):
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

    def __eq__(self, other: Tiles):
        return self.tiletype == other.tiletype and self.subtype == other.subtype and self.numchar == other.numchar

    def __str__(self):
        return self.tiletype + self.subtype + str(self.numchar)

    def __lt__(self, other: Tiles):
        suit_order = {'circle': 0, 'bamboo': 1, 'number': 2, 'wind': 3, 'dragon': 4}
        if self.subtype != other.subtype:
            return suit_order[self.subtype] < suit_order[other.subtype]
        return self.numchar < other.numchar


class MahjongGame:

    tiles: List[Tiles]
    players: List[Player]
    current_player_no: int
    current_player: Player
    discarded_tiles: List[Tiles]
    latest_tile: Tiles
    game_over: bool

    def __init__(self):
        self.players = [Player(i) for i in range(4)]
        self.tiles = MahjongGame.initialize_tiles()
        self.setup_game()
        print(len(self.tiles))

    @staticmethod
    def initialize_tiles() -> List[Tiles]:
        tiles = []
        for suit in ('circle', 'bamboo', 'number'):
            for i in range(1,10):
                for j in range(1,5):
                    tiles.append(Tiles(tiletype='suit', subtype=suit, numchar=j))

        for colour in ('red','green','white'):
            for i in range(0,4):
                tiles.append(Tiles(tiletype='honour', subtype='dragon', numchar=colour))

        for cardinality in ('north','south','east','west'):
            for i in range(0,4):
                tiles.append(Tiles(tiletype='honour', subtype='wind', numchar=cardinality))

        for flower in ('plum','orchid','chrysanthemum', 'bamboo'):
            tiles.append(Tiles(tiletype='flower', subtype='flower', numchar=flower))
        for season in ('summer','spring','autumn', 'winter'):
            tiles.append(Tiles(tiletype='flower', subtype='season', numchar=season))

        return tiles

    def initialise_players(self):
        player1 = Player(1)
        player2 = Player(2)
        player3 = Player(3)
        player4 = Player(4)
        self.players = [player1, player2, player3, player4]

    def initialise_player_hands(self, starting_number: int):
        # clear player hands
        current_player_number = starting_number
        current_player = self.players[current_player_number]
        while len(self.players[starting_number]._hidden_hand) < 14:
            self.players[starting_number].draw_tile(self)
            current_player_number += 1
            current_player_number %= 4
            current_player = self.players[current_player_number]
        self.players[starting_number].draw_tile(self)


    def setup_game(self):
        # Shuffle tiles and deal them to players
        random.shuffle(self.tiles)
        self.initialise_player_hands(0)
        self.current_player_no = 0
        self.current_player = self.players[self.current_player_no]


    def play_turn(self):
        game_over = False
        while not game_over:
            action_taken = True
            temp_player = self.current_player
            if self.latest_tile is not None:
                temp_player_number = (self.current_player_no + 1) % 4
                temp_player = self.players[temp_player_number]


                for i in range(0,3):
                    temp_player = self.players[temp_player_number]

                    if temp_player.decide_pong(self.latest_tile) or temp_player.decide_add_kong(self.latest_tile):
                        break
                    if temp_player.decide_win(self.latest_tile):
                       game_over = True
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

    def draw_tile(self) -> Tiles:
        return self.tiles.pop()

    def discard_tile(self, discarded_tile: Tiles):
        self.latest_tile = discarded_tile
        self.discarded_tiles.append(discarded_tile)

    def next_turn(self, player_skip: Optional[Player] = None):
        if player_skip:
            self.current_player_no = player_skip.player_id
            self.current_player = self.players[self.current_player_no]
        self.current_player_no = (self.current_player_no + 1) % 4
        self.current_player = self.players[self.current_player_no]

class Player:

    player_id: int
    _hidden_hand: List[Tiles] # assume sorted
    revealed_sets: List[List[Tiles]]
    total_score: int
    fan: int

    def __init__(self, player_id):
        self.player_id = player_id
        self._hidden_hand = []
        self.total_score = 0

    def set_hand(self):
        # for testing
        tile1 = Tiles(tiletype="suit", subtype="circle", numchar=1)
        tile2 = Tiles(tiletype="suit", subtype="circle", numchar=2)
        tile3 = Tiles(tiletype="suit", subtype="circle", numchar=3)
        tile4 = Tiles(tiletype="suit", subtype="circle", numchar=4)
        tile5 = Tiles(tiletype="suit", subtype="circle", numchar=5)
        tile6 = Tiles(tiletype="suit", subtype="circle", numchar=6)
        tile7 = Tiles(tiletype="suit", subtype="circle", numchar=7)
        tile8 = Tiles(tiletype="suit", subtype="circle", numchar=8)
        tile9 = Tiles(tiletype="suit", subtype="circle", numchar=9)
        self._hidden_hand = [tile1, tile1, tile2, tile2, tile2, tile3, tile4, tile4, tile5, tile5, tile5, tile5, tile5, tile6, tile9, tile9, tile9]


    def draw_tile(self, game_state: MahjongGame):
        drawn_tile = game_state.draw_tile()
        while drawn_tile.subtype == 'flower':
            self.revealed_sets.append([drawn_tile])
            drawn_tile = game_state.draw_tile()
        if self.decide_add_kong(drawn_tile):
            pass
        elif self.decide_win(drawn_tile, game_state):
            pass
        else:
            self.add_tile(drawn_tile)


    def check_winning_hand(self) -> bool:
        possible_hands = []
        i = 0
        while i < len(self._hidden_hand):
            tile = self._hidden_hand[i]
            potential_hand = []
            if self._hidden_hand[i+1] == tile: # check all possible combinations of 'eyes' first for efficiency
                remaining_hand = self._hidden_hand.copy()
                potential_hand.append([remaining_hand.pop(i), remaining_hand.pop(i)])
                i-=1

                if self.can_fit_into_set(remaining_hand, potential_hand):
                    potential_hand += self.revealed_sets
                    possible_hands.append(potential_hand)

            i+=1


        # printing for debugging
        for hand in possible_hands:
            print("====================")
            for i in hand:
                print("[")
                for j in i:
                    print(j)
                print("]")
            print("====================")


        return possible_hands is not []

    def check_thirteen_orphans(self, remaining_hand, potential_hand):
        # checking edge case
        pass

    def can_fit_into_set(self, remaining_hand, potential_hand: List[List[Tiles]]):
        if all(tile_count == 0 for tile_count in remaining_hand.values()):
            return True
        else:
            for tile, count in remaining_hand.items():

                # issue with mutating and for loop
                if count >= 3:
                    remaining_hand[tile] -= 3
                    potential_hand.append([tile, tile, tile])
                    return self.can_fit_into_set(remaining_hand, potential_hand)
                if count >= 1 and self.check_sheung(remaining_hand, tile, potential_hand):
                    return self.can_fit_into_set(remaining_hand, potential_hand)
                if count == 0:
                    pass
                else:
                    return False
            raise IndexError

    @staticmethod
    def check_sheung(remaining_hand: List[Tiles], selected_tile: Tiles, potential_hand: List[List[Tiles]]):
        # only check ascending sheung for consistency
        # assumes the tile exists in the remaining hand
        # mutates if True
        first_tile = Tiles(tiletype=selected_tile.tiletype, subtype=selected_tile.subtype, numchar=selected_tile.numchar + 1)
        second_tile = Tiles(tiletype=selected_tile.tiletype, subtype=selected_tile.subtype, numchar=selected_tile.numchar + 2)
        if selected_tile.tiletype == "suit" and selected_tile.numchar <= 7:
            if any(first_tile == tile for tile, count in remaining_hand.items() if count >= 1):
                if any(second_tile == tile for tile in remaining_hand):
                    remaining_hand[selected_tile] -= 1
                    remaining_hand[first_tile] -= 1
                    remaining_hand[second_tile] -= 1
                    potential_hand.append([selected_tile, first_tile, second_tile])
                    return True
            return False
        else:
            return False

    @staticmethod
    def filter_by_fan(self, potential_hand: List[List[Tiles]]) -> int:
        fan = 0
        # check flowers
        # count honours
        # great dragon

        # small dragon
        # count honour by fan

        # check wind (current wind)
        # great winds
        # small winds
        # count by winds and circle
        # dui dui wu
        if all(first_tile == second_tile  for first_tile, second_tile in potential_hand):
            fan += 3
            # assuming possible hands is structured correctly and can only contain a straight or a triplet
        elif all(first_tile.numchar == second_tile.numchar + 1 for first_tile, second_tile in potential_hand ): #ping wu
            fan += 1 # need to isolate the eye somehow
        # qing yat sik

        # wun yat sik
        return fan

    def show_all_possible_sheungs(self, latest_tile: Tiles) -> Tuple[Tuple[int, int] | None, Tuple[int, int] | None, Tuple[int, int] | None]:
        # return a 3 item tuple with None if the corresponding sheung is not possible, else the indices in
        # self._hidden_hand of the corresponding tiles necessary to form the sheung
        # first is for lower sheung, second for middle sheung, third for upper sheung
        sequenced_tiles = [-1, -1, -1, -1]

        # binary search
        index = bisect.bisect_right(self._hidden_hand,
                                    Tiles(tiletype=latest_tile.tiletype,
                                         subtype=latest_tile.subtype,
                                         numchar=latest_tile.numchar - 2)
                                    )
        upper_bound =  Tiles(tiletype=latest_tile.tiletype,
                                         subtype=latest_tile.subtype,
                                         numchar=latest_tile.numchar + 2)
        while index < len(self._hidden_hand) and self._hidden_hand[index] < upper_bound:
            if self._hidden_hand[index].numchar == latest_tile.numchar - 2:
                sequenced_tiles[0] = index
            elif self._hidden_hand[index].numchar == latest_tile.numchar - 1:
                sequenced_tiles[1] = index
            elif self._hidden_hand[index].numchar == latest_tile.numchar + 1:
                sequenced_tiles[2] = index
            elif self._hidden_hand[index].numchar == latest_tile.numchar + 2:
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




    def decide_add_kong(self, latest_tile) -> bool:
        if self._hidden_hand[latest_tile] != 3:
            return False
        raise NotImplementedError

    def decide_win(self, latest_tile, game_state) -> bool:
        if not self.check_winning_hand():
            return False
        raise NotImplementedError
        # mutate game_state.game_over to determine whether the win is claimed

    def decide_sheung(self, latest_tile: Tiles) -> bool:
        possible_sheungs = self.show_all_possible_sheungs(latest_tile)
        if not possible_sheungs:
            return False
        raise NotImplementedError

    def decide_pong(self, discarded_tile: Tiles) -> bool:
        if self._hidden_hand[discarded_tile] <= 2:
            return False
        raise NotImplementedError

    def discard_tile(self, game_state: MahjongGame) -> Tiles:
        raise NotImplementedError # implement decision making logic or player input

    def add_tile(self, drawn_tile):
        bisect.insort(self._hidden_hand, drawn_tile)


if __name__ == "__main__":
    # game = MahjongGame()
    # for player in game.players:
    #     print(player.hidden_hand)
    # game.play_turn()
    player1 = Player(1)
    player1.set_hand()
    player1.check_winning_hand()