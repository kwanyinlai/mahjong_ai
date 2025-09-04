from __future__ import annotations

import json
import math
import random
import bisect
from typing import Dict, Union, List, Optional, Tuple

import numpy as np

from player import Player
from ai_bot import BasicBot, YesBot, RandomBot
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
    winner: Player = None
    log: List[Dict]
    circle_wind: str

    def __init__(self, players: List[Player], circle_wind):
        self.players = players
        self.log = []  # {id, state, broad decision, decision value, reward, next state, game over}
        self.tiles = MahjongGame.initialize_tiles()
        self.setup_game()
        self.discarded_tiles = []
        self.game_over = False
        self.circle_wind = circle_wind

    @staticmethod
    def initialize_tiles() -> List[MahjongTile]:
        """
        Initialises the set of tiles that can be drawn in a game
        """
        tiles = []
        for suit in ('circle', 'bamboo', 'number'):
            for i in range(1, 10):
                for j in range(1, 5):
                    tiles.append(MahjongTile(tiletype='suit', subtype=suit, numchar=i))

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

        for player_redraw in self.players:
            last_tile = player_redraw.hidden_hand[len(player_redraw.hidden_hand) - 1]
            while player_redraw.hidden_hand[len(player_redraw.hidden_hand) - 1].tiletype == 'flower':
                last_tile = player_redraw.hidden_hand.pop()
                while last_tile.tiletype == 'flower':
                    player_redraw.flowers.append(last_tile)
                    # print("FLOWER REDRAW PLAYER " + str(player_redraw.player_id))
                    last_tile = self.tiles.pop()
            player_redraw.add_tile(last_tile)

    def setup_game(self):
        """
        Shuffle tiles and deal them to players
        """
        # print("SETUP")

        random.shuffle(self.tiles)
        self.initialise_player_hands(0)
        self.current_player_no = 0
        self.current_player = self.players[self.current_player_no]
        self.discarded_tiles = []

        if self.discard_tile(self.current_player) is not None:
            self.game_over = True  # todo: why??

        # print("SETUP COMPLETE")

    # GAMEPLAY ===========================================================================
    # ====================================================================================
    # ====================================================================================

    def check_interrupt(self, state: np.ndarray = None) -> Tuple[bool, bool]:
        """
        Check if should check sheung, and if to interrupt turn flow (bool 1 and
        2 respectively)
        :return:
        """
        temp_number = self.current_player_no
        for i in range(4):
            win_claim, pong_claim, add_kong_claim = (
                self.players[temp_number].check_claims(self.circle_wind, i, self.latest_tile, state))

            if win_claim:
                self.game_over = True
                self.winner = self.players[temp_number]
                self.log.append({
                    "player_id": self.current_player.player_id,
                    "state": state,
                    "action_type": "win",
                    "is_claim": True,
                    "reward": 0.0,
                    "gameover": True
                })
                return False, True
            elif add_kong_claim:
                for _ in range(3):
                    self.players[temp_number].hidden_hand.remove(self.latest_tile)

                self.players[temp_number].revealed_sets.append([self.latest_tile,
                                                                self.latest_tile,
                                                                self.latest_tile,
                                                                self.latest_tile])

                self.log.append({
                    "player_id": self.current_player.player_id,
                    "state": state,
                    "action_type": "kong",
                    "is_claim": True,
                    "reward": 0.0,
                    "gameover": False
                })

                self.next_turn((temp_number - 1) % 4)

                return False, False
            elif pong_claim:
                for _ in range(2):
                    self.players[temp_number].hidden_hand.remove(self.latest_tile)
                self.players[temp_number].revealed_sets.append([self.latest_tile,
                                                                self.latest_tile,
                                                                self.latest_tile])

                # print(self.players[temp_number].player_id)
                self.log.append({
                    "player_id": self.current_player.player_id,
                    "state": state,
                    "action_type": "pong",
                    "is_claim": True,
                    "reward": 0.0,
                    "gameover": False
                })
                self.discard_tile(self.players[temp_number])

                self.next_turn(temp_number)

                return True, True
            temp_number = (temp_number + 1) % 4
        return True, False

    def play_round(self) -> Player | None:
        """
        Play one round of a MahjongGame to the end until a draw or win. Return
        the winner.
        """
        self.winner = None
        self.game_over = False
        while not self.game_over and len(self.tiles) != 0:
            state = self.get_state()
            check_sheung, action_taken = self.check_interrupt(state)
            # print(action_taken)
            if not action_taken and check_sheung:  # kong takes latest tile
                sheung = self.current_player.decide_sheung(self.latest_tile, state)
                if sheung is not None:
                    sheung_tiles = [self.current_player.hidden_hand[sheung[0]],
                                    self.current_player.hidden_hand[sheung[1]]
                                    ]
                    bisect.insort(sheung_tiles, self.latest_tile)
                    self.current_player.revealed_sets.append(sheung_tiles)
                    self.current_player.hidden_hand.pop(sheung[0])
                    self.current_player.hidden_hand.pop(sheung[1] - 1)
                    self.log.append({
                        "player_id": self.current_player.player_id,
                        "state": state,
                        "action_type": "sheung",
                        "is_claim": True,
                        "reward": 0.0,
                        "gameover": False
                    })
                    self.discard_tile(self.current_player, state)
                else:
                    if self.draw_tile(self.current_player) is None:
                        break
                    self.discard_tile(self.current_player, state)
                    self.log.append({
                        "player_id": self.current_player.player_id,
                        "state": state,
                        "action_type": "discard",
                        "is_claim": False,
                        "reward": 0.0,
                        "gameover": False
                    })
            self.next_turn()

        if len(self.tiles) == 0:
            print("==================")
            print("GAME DRAW")
            for player in self.players:
                player.print_hand()
            return None
        else:
            print("==================")
            print("GAME WIN ")
            for player in self.players:
                player.print_hand()
            # TODO: self draw and what not
            if self.current_player is self.winner:
                scores = self.convert_score(self.winner.highest_fan, -1, self.winner.player_id)
                print("SELF DRAW")
            else:
                scores = self.convert_score(self.winner.highest_fan, self.current_player_no, self.winner.player_id)
                print("DISCARD WIN")
            for i in range(4):
                self.players[i].score += scores[i]
            return self.winner

    def draw_tile(self, player: Player) -> MahjongTile:
        """
        Add a tile to the player's hands and return
        """
        drawn_tile = self.tiles.pop()
        state = self.get_state()
        while drawn_tile.tiletype == "flower" and len(self.tiles) != 0:
            player.flowers.append(drawn_tile)
            drawn_tile = self.tiles.pop()
            # print("REDRAW FLOWER")
        if player.decide_win(drawn_tile, self.circle_wind, self.current_player_no, state):
            self.game_over = True
            self.winner = player
            print("WINNN")
            print(player.player_id)
            state = self.get_state()
            self.log.append({
                "player_id": self.current_player.player_id,
                "state": state,
                "action_type": "win",
                "is_claim": True,
                "reward": 0.0,
                "gameover": True
            })
            return None
        latest_tile, self.latest_tile = self.latest_tile, drawn_tile
        state = self.get_state()
        while player.decide_add_kong(drawn_tile, state) and len(self.tiles) > 0:
            state = self.get_state()
            for _ in range(3):
                self.players[self.current_player_no].hidden_hand.remove(drawn_tile)

            self.players[self.current_player_no].revealed_sets.append([drawn_tile,
                                                                       drawn_tile,
                                                                       drawn_tile,
                                                                       drawn_tile])
            self.draw_tile(player)
        self.latest_tile = latest_tile
        player.add_tile(drawn_tile)
        # print("Player " + str(player.player_id) + " put the following tile into your hand")
        # print(drawn_tile)
        return drawn_tile

    def discard_tile(self, player: Player, state: np.ndarray = None):
        """
        Add the latest tile to the discarded pile and set the latest discarded tile
        to this
        """

        discarded_tile = player.discard_tile(state)
        self.latest_tile = discarded_tile
        self.discarded_tiles.append(discarded_tile)

        player.hidden_hand.remove(discarded_tile)  # TODO: occasional bug here but so infrequent
        # TODO: that it's hard to detec tht ereason??
        # print("PLAYER " + str(player.player_id) + " DISCARDED")
        # print(discarded_tile)
        player.discard_pile.append(discarded_tile)
        self.log.append({
            "player_id": self.current_player.player_id,
            "state": state,
            "action_type": "discard",
            "is_claim": True,
            "reward": 0.0,
            "gameover": False
        })

    def next_turn(self, player_skip: Optional[int] = None):
        """

        :param player_skip:
        """
        if player_skip:
            self.current_player_no = player_skip
            self.current_player = self.players[self.current_player_no]
        self.current_player_no = (self.current_player_no + 1) % 4
        self.current_player = self.players[self.current_player_no]

    def convert_score(self, fan: int, discard_player: int, winning_player: int) -> List[int]:
        """
        Return a list of ints representing the score gained or lost
        by the player in the given position. If discard_player is
        -1 then
        """
        match fan:
            case 0:
                if discard_player == -1:
                    return [0, 0, 0, 0]
                else:
                    scores = [0, 0, 0, 0]
                    scores[winning_player] = 4
                    scores[discard_player] = -4
                    return scores
            case 1:
                if discard_player == -1:
                    score = [-4, -4, -4, -4]
                    score[winning_player] = 4 * 3
                    return score
                else:
                    scores = [0, 0, 0, 0]
                    scores[winning_player] = 8
                    scores[discard_player] = -8
                    return scores
            case 2:
                if discard_player == -1:
                    score = [-8, -8, -8, -8]
                    score[winning_player] = 8 * 3
                    return score
                else:
                    scores = [0, 0, 0, 0]
                    scores[winning_player] = 16
                    scores[discard_player] = -16
                    return scores
            case 3:
                if discard_player == -1:
                    score = [-16, -16, -16, -16]
                    score[winning_player] = 16 * 3
                    return score
                else:
                    scores = [0, 0, 0, 0]
                    scores[winning_player] = 32
                    scores[discard_player] = -32
                    return scores
            case 4 | 5 | 6:
                if discard_player == -1:
                    score = [-32, -32, -32, -32]
                    score[winning_player] = 32 * 3
                    return score
                else:
                    scores = [0, 0, 0, 0]
                    scores[winning_player] = 64
                    scores[discard_player] = -64
                    return scores
            case 7 | 8 | 9:
                if discard_player == -1:
                    score = [-64, -64, -64, -64]
                    score[winning_player] = 64 * 3
                    return score
                else:
                    scores = [0, 0, 0, 0]
                    scores[winning_player] = 128
                    scores[discard_player] = -128
                    return scores
            case _:
                if discard_player == -1:
                    score = [-128, -128, -128, -128]
                    score[winning_player] = 128 * 3
                    return score
                else:
                    scores = [0, 0, 0, 0]
                    scores[winning_player] = 256
                    scores[discard_player] = -256
                    return scores

    # TESTING METHODS ====================================================================
    # ====================================================================================
    # ====================================================================================

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
        print(Player.score_hand(player1.revealed_sets, player1.flowers, "east", 0))

        # STATE ===========================================================================

    def get_state(self):
        """

        :param latest_tile:
        :return:
        """
        # TODO: Restructure this to put all of one player's information together
        # TODO: probably not important to keep in same position if has current player's turn
        hidden_vec = []
        revealed_vec = []
        discards_vec = []
        hand_potential = []
        for player in self.players:
            hidden = player.encode_hidden_hand()
            revealed = player.encode_revealed_hand()
            discards = player.encode_discarded_pile()
            hidden_vec.append(hidden)
            revealed_vec.append(revealed)
            discards_vec.append(discards)
            potential_fan = Player.potential_fan(player.revealed_sets,
                                                 player.flowers,
                                                 self.circle_wind,
                                                 player.player_order)

        hidden_vec = np.concatenate(hidden_vec)
        revealed_vec = np.concatenate(revealed_vec)
        discards_vec = np.concatenate(discards_vec)

        latest_tile_vec = np.zeros(34, dtype=int)
        if self.latest_tile is not None:
            latest_tile_vec[self.latest_tile.to_index()] = 1

        # Tiles remaining in the wall
        tiles_remaining = np.array([len(self.tiles)])

        current_turn = np.array([self.current_player_no])

        state = np.concatenate([
            hidden_vec,  # 34 * 4
            revealed_vec,  # 34 * 4
            discards_vec,  # 34 * 4
            latest_tile_vec,  # 34 * 1
            tiles_remaining,  # 1
            current_turn  # 1
        ])

        return state

    def finish_episode(self, player_id: int, winloss: int, fan: int):
        """
        win -> winloss = 1
        loss -> winloss = -1
        draw -> winloss = 0
        """
        reward = MahjongGame.reward_function(winloss, fan)
        for step in self.log:
            if step["player_id"] == player_id:
                step["reward"] = reward
                step["gameover"] = True

    def log_to_json(self, filepath):
        """
        Conver the log to a jSOn file
        :return:
        """
        test = []
        for action in self.log:
            test.append({
                "player_id": action.get("player_id"),
                "state": action["state"].tolist(),
                "action_type": action["action_type"],
                "action": action["action"],
                "reward": action["reward"],
                "done": action["gameover"]
            })

        with open(filepath, "w") as f:
            json.dump(test, f)

    @staticmethod
    def reward_function(winloss: int, score: int) -> float:
        """

        :param winloss:
        :param fan:
        :return:
        """
        return winloss * score
