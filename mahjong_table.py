from __future__ import annotations

from typing import Dict, List

from ai_bot import BasicBot
from mahjong_game import MahjongGame
from player import Player


class MahjongTable:
    """
    Represents a series of games
    """
    circle_wind: Dict[int, str] = {1: "east", 2: "south", 3: "west", 4: "north"}
    starting_player: Player
    players: List[Player]

    def __init__(self):
        self.players = [BasicBot(i) for i in range(4)]
        self.starting_player = self.players[0]

    def start_table(self):
        """
        Start a table
        """
        round_no = 1
        player_start = 0
        while round_no < 5:
            print("ROUND " + str(round_no))
            game = MahjongGame(self.players, self.circle_wind[round_no])
            winner = game.play_round()
            for player in self.players:
                player.soft_reset()
            if winner is not self.starting_player and winner is not None:
                player_start += 1
                for player in self.players:
                    player.player_order = (player.player_order + 1) % 4
                if player_start == 4:
                    player_start = 0
                    round_no += 1

# TODO: Support multithreading
