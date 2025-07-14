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
        suit_order = {'circle': 0, 'bamboo': 1, 'number': 2, 'wind': 3, 'dragon': 4, 'flower': 5}
        if self.subtype != other.subtype:
            return suit_order[self.subtype] < suit_order[other.subtype]
        return self.numchar < other.numchar


class MahjongGame:

    tiles: List[Tiles]
    players: List[Player]
    current_player_no: int
    current_player: Player
    discarded_tiles: List[Tiles]
    latest_tile: Tiles = None
    game_over: bool

    def __init__(self):
        self.players = [Player(i) for i in range(4)]
        self.tiles = MahjongGame.initialize_tiles()
        self.setup_game()

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
        player1 = RandomBot(1)
        player2 = RandomBot(2)
        player3 = RandomBot(3)
        player4 = RandomBot(4)
        self.players = [player1, player2, player3, player4]

    def initialise_player_hands(self, starting_number: int):
        # clear player hands
        current_player_number = starting_number
        current_player = self.players[current_player_number]
        while len(self.players[starting_number]._hidden_hand) < 14:
            self.players[current_player_number].add_tile(self.draw_tile())
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
        while i < len(self._hidden_hand) - 1: # TODO: stuck in a loop here
            tile = self._hidden_hand[i]
            potential_hand = []
            if self._hidden_hand[i+1] == tile: # check all possible combinations of 'eyes' first for efficiency
                remaining_hand = self._hidden_hand.copy()
                potential_hand.append([remaining_hand.pop(i), remaining_hand.pop(i)])

                if self.can_fit_into_set(remaining_hand, potential_hand):
                    potential_hand += self.revealed_sets
                    possible_hands.append(potential_hand)

            i+=1
        return possible_hands is not []

    def check_thirteen_orphans(self, remaining_hand, potential_hand):
        # checking edge case
        pass

    def can_fit_into_set(self, remaining_hand: List[Tiles], potential_hand: List[List[Tiles]]):
        if len(remaining_hand)==0:
            return True
        else:
            print(len(remaining_hand))
            tile = remaining_hand[0] # always checks pong first. this approach does appear to work logically speaking
                                        # because of the sorted hand clears edge cases but
                                        #  not rigorously proven so possibly bugs CAUTION
            if len(remaining_hand) >= 3 and remaining_hand[1] == tile and remaining_hand[2] == tile:
                for j in range(0,3):
                     remaining_hand.pop(0)
                potential_hand.append([tile, tile, tile])
                return self.can_fit_into_set(remaining_hand, potential_hand)
            if self.check_sheung(remaining_hand, tile, potential_hand):
                return self.can_fit_into_set(remaining_hand, potential_hand)

            return False

    @staticmethod
    def check_sheung(remaining_hand: List[Tiles], selected_tile: Tiles, potential_hand: List[List[Tiles]]):
        # only check ascending sheung for consistency
        # assumes the tile exists in the remaining hand
        # mutates if True
        if not (selected_tile.tiletype == "suit" and selected_tile.numchar <= 7):
            return False
        index = bisect.bisect_left(remaining_hand, selected_tile)
        indices = [index, -1, -1]
        target_tile = Tiles(tiletype = selected_tile.tiletype,
                            subtype = selected_tile.subtype,
                            numchar = selected_tile.numchar+2)
        while index < len(remaining_hand) and remaining_hand[index] < target_tile:
            if remaining_hand[index].numchar == target_tile.numchar + 1:
                indices = index
            elif remaining_hand[index].numchar == target_tile.numchar + 2:
                indices = index
            index += 1

        if indices[1] == -1 or indices[2] == -1:
            return False
        else:
            potential_hand.append([remaining_hand.pop(indices[0]),
                                  remaining_hand.pop(indices[0]-1),
                                  remaining_hand.pop(indices[1]-2)])
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

    def show_all_possible_sheungs(self, latest_tile: Tiles) -> (Tuple[Tuple[int, int] | None,
                                                                Tuple[int, int] | None, Tuple[int, int] | None]):
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




    def decide_add_kong(self, latest_tile: Tiles) -> bool:
        index = bisect.bisect_left(self._hidden_hand, latest_tile)
        print("???")
        if (self._hidden_hand[index] != latest_tile or
            (self._hidden_hand[index + 1] != latest_tile and self._hidden_hand[index+2] != latest_tile) or
            (self._hidden_hand[index+1] != latest_tile and self._hidden_hand[index-1] != latest_tile) or
            (self._hidden_hand[index-1] != latest_tile and self._hidden_hand[index-2] != latest_tile)
           ):
            return False
        return True

    def decide_win(self, latest_tile, game_state) -> bool:
        print("!!!")
        if not self.check_winning_hand():
            return False
        return True
        # mutate game_state.game_over to determine whether the win is claimed

    def decide_sheung(self, latest_tile: Tiles) -> bool:
        possible_sheungs = self.show_all_possible_sheungs(latest_tile)
        if all(sheung is None for sheung in possible_sheungs):
            return False

        return True

    def decide_pong(self, discarded_tile: Tiles) -> bool:

        index = bisect.bisect_left(self._hidden_hand, discarded_tile)
        if self._hidden_hand[index] != discarded_tile or (self._hidden_hand[index + 1] != discarded_tile and
                                                          self._hidden_hand[index -1] != discarded_tile):
            return False

        return True
    def discard_tile(self, game_state: MahjongGame) -> Tiles:
        return True

    def add_tile(self, drawn_tile: Tiles):
        bisect.insort(self._hidden_hand, drawn_tile)

class RandomBot(Player):
    def decide_pong(self, tile: Tiles):
        super().decide_pong(tile)
        is_pong = random.choice([True, False])
        if is_pong:
            self._hidden_hand.remove(tile)
            self._hidden_hand.remove(tile) # TODO: im lazy to implement efficient removal right now using sorted
            self.revealed_sets.append([tile, tile, tile])

        return is_pong

    def decide_add_kong(self, latest_tile) -> bool:
        super().decide_add_kong(latest_tile)
        is_kong = random.choice([True, False])
        if is_kong:
            self._hidden_hand.remove(latest_tile)
            self._hidden_hand.remove(latest_tile)
            self._hidden_hand.remove(latest_tile)  # TODO: im lazy to implement efficient removal right now using sorted
            self.revealed_sets.append([latest_tile, latest_tile, latest_tile])
        return is_kong


    def decide_win(self, latest_tile, game_state):
        super().decide_win(latest_tile, game_state)
        return random.choice([True, False])

    def decide_sheung(self, latest_tile) -> bool:
        possible_sheungs = self.show_all_possible_sheungs(latest_tile)
        if all(sheung is None for sheung in possible_sheungs):
            return False
        is_sheung = random.choice([True, False])
        if is_sheung:
            decided_sheung = random.choice([indices for indices in possible_sheungs if indices is not None])
            for i in range (0, len(decided_sheung)):
                self._hidden_hand.pop(decided_sheung[i] - i)

        return is_sheung


    def discard_tile(self, game_state: MahjongGame) -> Tiles:
        removed_tile = random.choice(self._hidden_hand)
        self._hidden_hand.remove(removed_tile)
        return removed_tile



if __name__ == "__main__":
    game = MahjongGame()
    print("hi")
    for player in game.players:
        print(player._hidden_hand)
    game.play_turn()

