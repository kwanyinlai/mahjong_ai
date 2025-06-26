from __future__ import annotations

import random
from typing import Union, List, Optional


class Tiles:
    tiletype: str
    subtype: str
    numchar: Union[int,str]
    discarded: bool = False
    discarded_by: Optional[Player] = None

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
        current_player_number = starting_number
        current_player = self.players[current_player_number]
        while len(self.players[starting_number].hand) < 14:
            self.players[starting_number].hand = self.players[starting_number].hand.get(self.tiles.pop(), 0) + 1
            current_player_number += 1
            current_player %= 4
            current_player = self.players[current_player_number]
        self.players[starting_number].hidden_hand = self.players[starting_number].hidden_hand.get(self.tiles.pop(), 0) + 1



    def setup_game(self):
        # Shuffle tiles and deal them to players
        random.shuffle(self.tiles)
        self.initialise_player_hands(0)
        self.current_player_no = 0
        self.current_player = self.players[self.current_player_no]


    def play_turn(self):
        next_player = self.current_player
        while True:
            if self.latest_tile:
                for temp_player in self.players:
                    if temp_player.check_pong(self.latest_tile): # or check_sheung what not
                        self.next_turn(temp_player)
                        break
                    # temp_player.check_sheung(self.latest_tile)
                    # temp_player.check_discard_kong(self.latest_tile)

            # action = current_player.decide_action(self)
            # self.process_action(action)
            # if self.check_game_over():
            #     break
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
    hidden_hand: dict
    revealed_sets: List[List[Tiles]]
    score: int

    def __init__(self, player_id):
        self.player_id = player_id
        self.hidden_hand = {}
        self.score = 0

    def decide_action(self, game_state: MahjongGame):
        return "action"

    def check_pong(self, discarded_tile: Tiles) -> Optional[Tiles]:
        if discarded_tile in self.hidden_hand and self.hidden_hand[discarded_tile] == 2:
            print("You can pong")
        return None


    def discard_tile(self) -> Tiles:
        return None


if __name__ == "__main__":
    game = MahjongGame()
    for player in game.players:
        print(player.hidden_hand)
    game.play_turn()