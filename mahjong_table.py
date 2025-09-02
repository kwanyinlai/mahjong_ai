from __future__ import annotations

from typing import List

from ai_bot import BasicBot
from mahjong_game import MahjongGame
from player import Player


class MahjongTable:
    """
    Represents a series of games
    """
    circle_wind: str = "east"
    starting_player: Player
    players: List[Player]

    def __init__(self):
        self.circle_wind = "east"
        self.players = [BasicBot(i) for i in range(4)]
        self.starting_player = self.players[0]

    def start_table(self):
        """
        Start a table
        """
        round_no = 1
        player_start = 0
        while round_no != 5:
            game = MahjongGame(self.players)
            winner = game.play_round()
            if winner is not self.starting_player:
                player_start += 1
                if player_start == 4:
                    player_start = 0
                    round_no += 1

# TODO: Support multithreading
