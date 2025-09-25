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
        self.players = [BasicBot(i, i) for i in range(4)]
        self.starting_player = self.players[0]

    def start_table(self):
        """
        Start a table
        """
        round_no = 1
        player_start = 0
        for i in range(4):
            self.players[i].player_order = i
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

    def run_concurrent_games(self):
        """
        Run MahjongGame instances concurrently using multiprocessing
        :return:
        """
        # ROUND
        game1 = MahjongGame(self.players, self.circle_wind[0])
        game2 = MahjongGame(self.players, self.circle_wind[1])
        game3 = MahjongGame(self.players, self.circle_wind[2])
        game4 = MahjongGame(self.players, self.circle_wind[3])
        pass


# TODO: Support multithreading


"""
Reference Code from main.py

table = MahjongTable()
    table.start_table()
    for player in table.players:
        print(f"Final score for Player {player.player_id}: {player.score}")

"""
