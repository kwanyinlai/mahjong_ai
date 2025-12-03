"""
Test class for our Mahjong logic
"""

import unittest

from ai_bot import BasicBot, YesBot
from mahjong_game import MahjongGame
from player import Player
from tile import MahjongTile


class TestMahjongLogic(unittest.TestCase):

    def test_can_sheung(self):
        player1 = BasicBot(1, 1)

        tile1 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=2)
        tile2 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=3)
        tile3 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=4)
        tile4 = MahjongTile(tiletype="suit", subtype="circle", numchar=5)
        tile5 = MahjongTile(tiletype="suit", subtype="circle", numchar=6)
        tile6 = MahjongTile(tiletype="suit", subtype="circle", numchar=7)
        tile7 = MahjongTile(tiletype="suit", subtype="number", numchar=3)
        tile8 = MahjongTile(tiletype="honour", subtype="dragon", numchar="white")
        tile9 = MahjongTile(tiletype="suit", subtype="number", numchar=6)

        player1.hidden_hand = [tile1, tile2, tile4, tile5, tile6, tile7, tile7,
                               tile7, tile8, tile8, tile8, tile9, tile9]

        player1.hidden_hand.sort()
        self.assertIs(player1.sheung_possible(tile3), True)
        self.assertIs(player1.sheung_possible(tile1), False)

    def test_can_pong(self):
        player1 = YesBot(1, 1)
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
        self.assertIs(player1.decide_pong(tile7), True)
        self.assertIs(player1.decide_pong(tile1), False)

    def test_insufficient_fan(self):
        player1 = YesBot(1, 0)
        player2 = YesBot(2, 1)
        player3 = YesBot(3, 2)
        player4 = YesBot(4, 3)
        players = [player1, player2, player3, player4]
        mahjong_game = MahjongGame(players, 'east')
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

        self.assertIs(player1.decide_win(tile1, 'east', 0), False)

    def test_fan_three_fan_is_accepted(self):
        player1 = YesBot(1, 0)
        player2 = YesBot(2, 1)
        player3 = YesBot(3, 2)
        player4 = YesBot(4, 3)
        players = [player1, player2, player3, player4]
        mahjong_game = MahjongGame(players, 'east')
        mahjong_game.players = players
        mahjong_game.initialize_tiles()
        mahjong_game.setup_game()

        tile1 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=2)
        tile2 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=2)
        tile3 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=2)
        tile4 = MahjongTile(tiletype="suit", subtype="circle", numchar=2)
        tile5 = MahjongTile(tiletype="suit", subtype="circle", numchar=2)
        tile6 = MahjongTile(tiletype="suit", subtype="circle", numchar=2)
        tile7 = MahjongTile(tiletype="suit", subtype="number", numchar=3)
        tile8 = MahjongTile(tiletype="suit", subtype="number", numchar=3)
        tile9 = MahjongTile(tiletype="suit", subtype="number", numchar=3)
        tile10 = MahjongTile(tiletype="suit", subtype="number", numchar=6)
        tile11 = MahjongTile(tiletype="suit", subtype="number", numchar=6)
        tile12 = MahjongTile(tiletype="suit", subtype="number", numchar=6)
        tile13 = MahjongTile(tiletype="suit", subtype="number", numchar=7)
        tile14 = MahjongTile(tiletype="suit", subtype="number", numchar=7)

        flower1 = MahjongTile(tiletype="flower", subtype="season", numchar="winter")

        player1.hidden_hand = [tile1, tile2, tile3, tile4, tile5, tile6, tile7, tile8,
                               tile9, tile10, tile11, tile12, tile13]
        player1.hidden_hand.sort()

        potential_hand = [
            [tile1, tile2, tile3],
            [tile4, tile5, tile6],
            [tile7, tile8, tile9],
            [tile10, tile11, tile12],
            [tile13, tile14]
        ]

        self.assertIs(Player.score_hand(potential_hand, [flower1], 'east', 0), 3)
        self.assertIs(player1.decide_win(tile14, 'east', 0), True)

    def test_fan_two_fan_is_rejected(self):
        player1 = YesBot(1, 0)
        player2 = YesBot(2, 1)
        player3 = YesBot(3, 2)
        player4 = YesBot(4, 3)
        players = [player1, player2, player3, player4]
        mahjong_game = MahjongGame(players, 'east')
        mahjong_game.players = players
        mahjong_game.initialize_tiles()
        mahjong_game.setup_game()

        tile1 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=2)
        tile2 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=3)
        tile3 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=4)
        tile4 = MahjongTile(tiletype="suit", subtype="circle", numchar=5)
        tile5 = MahjongTile(tiletype="suit", subtype="circle", numchar=6)
        tile6 = MahjongTile(tiletype="suit", subtype="circle", numchar=7)
        tile7 = MahjongTile(tiletype="honour", subtype="dragon", numchar="green")
        tile8 = MahjongTile(tiletype="honour", subtype="dragon", numchar="green")
        tile9 = MahjongTile(tiletype="honour", subtype="dragon", numchar="green")
        tile10 = MahjongTile(tiletype="honour", subtype="circle", numchar=1)
        tile11 = MahjongTile(tiletype="honour", subtype="circle", numchar=1)
        tile12 = MahjongTile(tiletype="honour", subtype="circle", numchar=1)
        tile13 = MahjongTile(tiletype="suit", subtype="number", numchar=7)
        tile14 = MahjongTile(tiletype="suit", subtype="number", numchar=7)

        player1.hidden_hand = [tile1, tile2, tile3, tile4, tile5, tile6, tile7, tile8,
                               tile9, tile10, tile11, tile12, tile13]
        player1.hidden_hand.sort()
        potential_hand = [
            [tile1, tile2, tile3],
            [tile4, tile5, tile6],
            [tile7, tile8, tile9],
            [tile10, tile11, tile12],
            [tile13, tile14]
        ]

        self.assertIs(Player.score_hand(potential_hand, [], 'east', 0), 2)
        self.assertIs(player1.decide_win(tile14, 'east', 0), False)

    def test_add_kong(self):
        player1 = YesBot(1, 1)

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
        self.assertIs(player1.decide_add_kong(tile7), True)
        self.assertIs(player1.decide_add_kong(tile1), False)

    def test_win_scenario(self):
        player1 = YesBot(1, 1)

        tile1 = MahjongTile(tiletype="suit", subtype="circle", numchar=2)
        tile2 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=1)
        tile3 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=2)
        tile4 = MahjongTile(tiletype="suit", subtype="bamboo", numchar=3)
        tile5 = MahjongTile(tiletype="suit", subtype="number", numchar=1)
        player1.hidden_hand = [tile1, tile1, tile1, tile5, tile5, tile5, tile2, tile2,
                               tile2, tile3, tile3, tile3, tile4, tile4]

        player1.hidden_hand.sort()

        self.assertIs(player1.check_winning_hand('east'), True)

    def test_fan_calc(self):
        # This is aleady implicitly tested in our earlier tests
        player1 = YesBot(1, 1)

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
        self.assertIs(Player.score_hand(player1.revealed_sets, player1.flowers, "east", 0), 0)
