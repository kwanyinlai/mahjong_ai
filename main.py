from __future__ import annotations

import random
from typing import Union, List, Optional


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

class MahjongGame:

    tiles: List[Tiles]
    players: List[Player]
    current_player_no: int
    current_player: Player
    discarded_tiles: List[Tiles]
    latest_tile: Tiles

    def __init__(self):
        self.players = [Player(i) for i in range(4)]
        self.tiles = self.initialize_tiles()
        self.setup_game()
        print(len(self.tiles))

    def initialize_tiles(self) -> List[Tiles]:
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
        next_player = self.current_player
        while True:
            if self.latest_tile is not None:
                for temp_player in self.players:
                    if temp_player.check_pong(self.latest_tile): # or check_sheung what not
                        self.next_turn(temp_player)
                        break
                    # temp_player.check_sheung(self.latest_tile)
                    # temp_player.check_discard_kong(self.latest_tile)

            # action = current_player.make_action(self)
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
    _hidden_hand: dict
    revealed_sets: List[List[Tiles]]
    total_score: int
    fan: int

    def __init__(self, player_id):
        self.player_id = player_id
        self._hidden_hand = {}
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
        self._hidden_hand = {tile1: 2, tile2:3, tile3:1, tile4: 2, tile5:5, tile6:1, tile9: 3}

    def make_action(self, game_state: MahjongGame):

        self.draw_tile(game_state)
        # calculate fan
        # check game over
        # check draw kong
        # check flower


        self.discard_tile()

        # calculate current hand fan


    def check_pong(self, discarded_tile: Tiles) -> Optional[Tiles]:
        if discarded_tile in self._hidden_hand and self._hidden_hand[discarded_tile] == 2:
            print("You can pong")
        return None


    def discard_tile(self) -> Tiles:
        raise NotImplementedError() # implement decision making logic or player input

    def draw_tile(self, game_state: MahjongGame):
        drawn_tile = game_state.draw_tile()
        self._hidden_hand[drawn_tile] = self._hidden_hand.get(drawn_tile, 0) + 1


    def check_winning_hand(self) -> bool:
        possible_hands = []
        loop = self._hidden_hand.copy()
        for tile, count in loop.items():
            print("check")
            print(tile, count)
            potential_hand = []
            if count >= 2:
                remaining_hand = self._hidden_hand.copy()
                potential_hand.append([tile, tile])
                remaining_hand[tile] -= 2
                if self.can_fit_into_set(remaining_hand, potential_hand):
                    possible_hands.append(potential_hand)
        print(possible_hands)
        return possible_hands is not None

    def can_fit_into_set(self, remaining_hand, potential_hand: List[List[Tiles]]):
        if all(tile_count == 0 for tile_count in remaining_hand.values()):
            return True

        else:
            for tile, count in remaining_hand.items():
                print(tile)
                print(count)

                # issue with mutating and for loop
                if count >= 3:
                    remaining_hand[tile] -= 3
                    potential_hand.append([tile, tile, tile])
                    print(potential_hand)
                    return self.can_fit_into_set(remaining_hand, potential_hand)
                if count >= 1 and self.check_sheung(remaining_hand, tile, potential_hand):
                    return self.can_fit_into_set(remaining_hand, potential_hand)
                if count == 0:
                    pass
                else:
                    return False
            raise IndexError

    def check_sheung(self, remaining_hand: dict[Tiles, int], selected_tile: Tiles, potential_hand: List[List[Tiles]]):
        # only check ascending sheung for consistency
        # assumes the tile exists in the remaining hand
        # mutates if True
        first_tile = Tiles(tiletype=selected_tile.tiletype, subtype=selected_tile.subtype, numchar=selected_tile.numchar + 1)
        second_tile = Tiles(tiletype=selected_tile.tiletype, subtype=selected_tile.subtype, numchar=selected_tile.numchar + 2)
        if selected_tile.tiletype == "suit" and selected_tile.numchar <= 7:
            if any(first_tile == tile for tile, count in remaining_hand.items() if count >= 1):
                if any(second_tile == tile
                       for tile, count in remaining_hand.items() if count >= 1):
                    remaining_hand[selected_tile] -= 1
                    remaining_hand[first_tile] -= 1
                    remaining_hand[second_tile] -= 1
                    potential_hand.append([selected_tile, first_tile, second_tile])
                    return True
            return False
        else:
            return False

if __name__ == "__main__":
    # game = MahjongGame()
    # for player in game.players:
    #     print(player.hidden_hand)
    # game.play_turn()
    player1 = Player(1)
    player1.set_hand()
    print(player1._hidden_hand)
    player1.check_winning_hand()