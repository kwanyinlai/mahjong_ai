from __future__ import annotations

import math
import random
import bisect
from bisect import insort_left
from typing import Union, List, Optional, Tuple

import numpy as np

from ai_bot import Player, BasicBot, YesBot, RandomBot
from tile import MahjongTile


class MahjongGame:
    """
    Represents one Mahjong Game
    """
    tiles: List[MahjongTile]
    players: List[Player]
    current_player_no: int
    current_player: Player
    discarded_tiles: List[MahjongTile]
    latest_tile: MahjongTile = None
    game_over: bool

    def __init__(self):
        self.players = [BasicBot(i) for i in range(4)]
        self.tiles = MahjongGame.initialize_tiles()
        self.setup_game()
        self.discarded_tiles = []
        self.game_over = False

    def get_state(self, player_id: int) -> np.ndarray:
        agent = self.players[player_id]

        hidden_hand_vec = np.concatenate(agent.encode_hidden_hand())
        revealed_hand_vec = np.concatenate(agent.encode_revealed_hand())

        # Discards
        discards = [player.encode_discarded_pile() for player in self.players]
        discards_vec = np.concatenate(discards)

        # Revealed
        revealed_sets = [player.encode_revealed_hand() for player in self.players if player is not agent]
        revealed_set_vec = np.concatenate(revealed_sets)

        latest_tile_vec = np.zeros(34, dtype=int)
        if self.latest_tile:
            latest_tile_vec[self.latest_tile.to_index()] = 1

        # Opponent hands
        opponent_hands = [player.encode_hidden_hand() for player in self.players if player is not agent]
        opponent_hand_vec = np.concatenate(opponent_hands)

        # Final state vector
        state_vec = np.concatenate([
            hidden_hand_vec,
            revealed_hand_vec,
            discards_vec,
            revealed_set_vec,
            latest_tile_vec,
            opponent_hand_vec
        ])

        return state_vec

    @staticmethod
    def test_sheung():
        player1 = BasicBot(1)
        player2 = BasicBot(2)
        player3 = BasicBot(3)
        player4 = BasicBot(4)
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

        tile1 = MahjongTile(tiletype="suit", subtype="circle", numchar=2)
        tile2 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=1)
        tile3 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=2)
        tile4 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=3)
        tile5 = MahjongTile(tiletype="suit", subtype="number", numchar=1)
        player1.hidden_hand = [tile1, tile1, tile1, tile5, tile5, tile5, tile2, tile2,
                               tile2, tile3, tile3, tile3, tile4, tile4]

        player1.hidden_hand.sort()

        print(player1.check_winning_hand())

    @staticmethod
    def test_fan_calc():
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
        print(Player.score_hand(player1.hidden_hand, player1.flowers, "east", 0))

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
        while len(self.players[starting_number].hidden_hand) < 14:
            self.players[current_player_number].add_tile(self.tiles.pop())
            current_player_number += 1
            current_player_number %= 4

        for player_redraw in self.players: # TODO: Fix this to go in right order, while loop ntof or loop
            last_tile = player_redraw.hidden_hand[len(player_redraw.hidden_hand)-1]
            while player_redraw.hidden_hand[len(player_redraw.hidden_hand)-1].tiletype == 'flower':
                last_tile = player_redraw.hidden_hand.pop()
                while last_tile.tiletype == 'flower':
                    player_redraw.flowers.append(last_tile)
                    print("FLOWER REDRAW PLAYER " + str(player_redraw.player_id))
                    last_tile = self.tiles.pop()
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
        self.discarded_tiles = []

        if self.discard_tile(self.current_player.discard_tile()) is not None:
            self.game_over = True
        for player in self.players:
            player.print_hand()
        print("SETUP COMPLETE")

    def check_interrupt(self) -> bool:
        """
        Check if interrupt
        :return:
        """
        temp_number = self.current_player_no
        for _ in range(4):
            win_claim, pong_claim, add_kong_claim = (
                self.players[temp_number].check_claims(self.current_player, self.latest_tile))

            if win_claim:
                self.game_over = True

                return True
            elif add_kong_claim:
                for _ in range(3):
                    self.players[temp_number].hidden_hand.remove(self.latest_tile)

                print("KONG")
                print(self.players[temp_number])
                self.players[temp_number].revealed_sets.append([self.latest_tile,
                                                                self.latest_tile,
                                                                self.latest_tile,
                                                                self.latest_tile])

                print(self.players[temp_number].player_id)
                self.players[temp_number].discard_tile()
                self.current_player.discard_tile()
                self.next_turn(temp_number)
                return True
            elif pong_claim:
                print("PONG")
                for _ in range(2):
                    self.players[temp_number].hidden_hand.remove(self.latest_tile)
                self.players[temp_number].revealed_sets.append([self.latest_tile,
                                                                self.latest_tile,
                                                                self.latest_tile])

                print(self.players[temp_number].player_id)
                self.players[temp_number].discard_tile()
                self.next_turn(temp_number)
                return True
            temp_number = (temp_number + 1) % 4
        return False

    def play_round(self):
        """
        Play one round of a MahjongGame to the end until a draw or win
        """
        self.game_over = False
        while not self.game_over and len(self.tiles) != 0:
            action_taken = self.check_interrupt()
            print(action_taken)
            if not action_taken:
                sheung = self.current_player.decide_sheung(self.latest_tile)
                if sheung is not None:
                    sheung_tiles = [self.current_player.hidden_hand[sheung[0]],
                                    self.current_player.hidden_hand[sheung[1]]
                                    ]

                    bisect.insort(sheung_tiles, self.latest_tile)
                    self.current_player.revealed_sets.append(sheung_tiles)
                    self.current_player.hidden_hand.pop(sheung[0])
                    self.current_player.hidden_hand.pop(sheung[1] - 1)
                    self.current_player.discard_tile()

                else:
                    if self.draw_tile(self.current_player) is None:
                        break
                    self.current_player.discard_tile()

            self.next_turn()  #TODO: Pongs and kongs are added to everyone's revealed hand

        if len(self.tiles) == 0:
            print("==================")
            print("GAME DRAW")
            for player in game.players:
                player.print_hand()
        else:
            print("==================")
            print(" GAME WIN ")
            for player in self.players:
                player.print_hand()

    def draw_tile(self, player: Player) -> MahjongTile:
        """
        Add a tile to the player's hands and return
        """

        drawn_tile = self.tiles.pop()
        while drawn_tile.tiletype == "flower" and len(self.tiles) != 0:
            player.flowers.append(drawn_tile)
            drawn_tile = self.tiles.pop()
            print("REDRAW FLOWER")
        if player.decide_win(drawn_tile):
            self.game_over = True
            print("WINNN")
            print(player.player_id)
            return None
        player.add_tile(drawn_tile)
        print("Player " + str(player.player_id) + " put the following tile into your hand")
        print(drawn_tile)

        return drawn_tile

    def discard_tile(self, discarded_tile: MahjongTile):
        """
        Add the latest tile to the discarded pile and set the latest discarded tile
        to this
        """
        self.latest_tile = discarded_tile
        self.discarded_tiles.append(discarded_tile)
        print("Player discarded")
        print(discarded_tile)

    def next_turn(self, player_skip: Optional[int] = None):
        """

        :param player_skip:
        """
        if player_skip:
            self.current_player_no = player_skip
            self.current_player = self.players[self.current_player_no]
        self.current_player_no = (self.current_player_no + 1) % 4
        self.current_player = self.players[self.current_player_no]


if __name__ == "__main__":
    game = MahjongGame()
    game.play_round()

    # while not game.win:
    #     game.play_round()
    #     game = MahjongGame()
    # MahjongGame.test_fan_calc()

    # MahjongGame.test_win_scenario()
    # MahjongGame.test_win_claim()

# TODO: Need to play the next player - doesn't work right now
# TODO: Check self draw wins
