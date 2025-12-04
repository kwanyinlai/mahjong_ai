from __future__ import annotations

import json
import random
import bisect
from typing import Dict, Union, List, Optional, Tuple

import numpy as np

from mahjong_actions import MahjongActions
from player import Player
from tile import MahjongTile


class MahjongGame:
    """
    Represents one Mahjong Game
    """
    tiles: List[MahjongTile]
    players: List[Player]
    current_player_no: int
    current_player: Player
    discarding_player: Player
    discarded_tiles: List[MahjongTile]
    latest_tile: MahjongTile = None
    game_over: bool
    winner: Player = None
    log: List[Dict]
    circle_wind: str

    def __init__(self, players: List[Player], circle_wind):
        ordered_players = []
        i = 0
        while i < 4:
            for player in players:
                if player.player_order == i:
                    ordered_players.append(player)
                    break
            i += 1
        self.players = ordered_players
        self.log = []  # {id, state, broad decision, decision value, reward, next state, game over}
        self.discarded_tiles = []
        self.game_over = False
        self.circle_wind = circle_wind
        self.tiles = MahjongGame.initialize_tiles()
        self.setup_game()

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

    def initialise_player_hands(self):
        """
        Starting number is the index of the player we start with
        Give 13 tiles to each player, then replace with 13 tiles, and then give
        a 14th tile to the first person to play.
        """
        # clear player hands
        current_player_number = 0
        while len(self.players[0].hidden_hand) < 14:
            self.players[current_player_number].add_tile(self.tiles.pop())
            # print(f"CURR: {len(self.players[current_player_number].hidden_hand)}")
            current_player_number += 1
            current_player_number %= 4

        for player_redraw in self.players:
            while player_redraw.hidden_hand[len(player_redraw.hidden_hand) - 1].tiletype == 'flower':
                last_tile = player_redraw.hidden_hand.pop()
                while last_tile.tiletype == 'flower':
                    player_redraw.flowers.append(last_tile)
                    # print("FLOWER REDRAW PLAYER " + str(player_redraw.player_id))
                    last_tile = self.tiles.pop()
                player_redraw.add_tile(last_tile)
        self.current_player_no = 0
        self.current_player = self.players[0]
        state = self.get_state()

    def setup_game(self):
        """
        Shuffle tiles and deal them to players
        """
        # print("SETUP")

        random.shuffle(self.tiles)
        self.initialise_player_hands()
        self.current_player_no = 0
        self.current_player = self.players[self.current_player_no]
        self.discarded_tiles = []

        # print("SETUP COMPLETE")

    # ============================= GAMEPLAY ========================================

    def play_round(self) -> Player | None:
        """
        Play one round of a MahjongGame to the end until a draw or win. Return
        the winner.
        """
        self.winner = None
        self.game_over = False
        print("GAME START")

        while not self.game_over and len(self.tiles) != 0:
            actioning_player_id, action_to_execute, possible_indices = self.play_turn()
            is_interrupted = self.execute_interrupt(actioning_player_id, action_to_execute, possible_indices)
            if not is_interrupted:
                for player in self.players:
                    if len(player.hidden_hand) % 3 != 1 and not self.game_over:
                        player.print_hand()
                        raise ValueError("The players do not have the right number of tiles in hand")

                if not self.game_over:
                    self.next_turn()
                    self.draw_tile(self.current_player)

            if self.game_over:
                break

        if len(self.tiles) == 0:
            print("==================")
            print("GAME DRAW")
            for player in self.players:
                player.print_hand()
            return None
        else:
            print("==================")
            print(f"Player {self.winner.player_id} won")
            self.winner.print_hand()

            if self.current_player is self.winner:
                scores = self.convert_score(self.winner.highest_fan, -1, self.winner.player_id)
                print("Self draw")
            else:
                if self.discarding_player is self.winner:
                    raise ValueError
                scores = self.convert_score(self.winner.highest_fan, self.discarding_player.player_order,
                                            self.winner.player_order)
                print("Discard win")
            if (scores[0] + scores[1] + scores[2] + scores[3]) != 0:
                print(scores)
                raise ValueError("Scores do not add up to zero.")
            for i in range(4):
                self.players[i].score += scores[i]
            return self.winner

    def draw_tile(self, player: Player) -> Optional[MahjongTile]:
        """
        Draw a tile from the pile, redraw on any flowers, and
        automatically claim add_kong or win. Return the drawn tile.
        :param player: the player who is drawing
        :return: the drawn tile
        """
        drawn_tile = self.tiles.pop()
        state = self.get_state()
        print(f"Player {player.player_id} has drawn {drawn_tile}")
        while drawn_tile.tiletype == "flower" and len(self.tiles) != 0:
            player.flowers.append(drawn_tile)
            drawn_tile = self.tiles.pop()
            print(f"Player {player.player_id} has redrawn a flower to {drawn_tile}")

        if drawn_tile.tiletype == "flower":
            player.flowers.append(drawn_tile)
            return None

        if (player.decide_win(drawn_tile, self.circle_wind, self.current_player_no, state)
                and Player.decide_win(player, drawn_tile, self.circle_wind, self.current_player_no, state)):
            self.game_over = True
            self.winner = player
            print(f"Player {player.player_id} has claimed a win")
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
        while Player.decide_add_kong(player, drawn_tile, state) and player.decide_add_kong(drawn_tile, state) and len(
                self.tiles) > 0:
            for _ in range(3):
                self.players[self.current_player_no].hidden_hand.remove(drawn_tile)

            self.players[self.current_player_no].revealed_sets.append([drawn_tile,
                                                                       drawn_tile,
                                                                       drawn_tile,
                                                                       drawn_tile])
            print(f"Player {player.player_id} has claimed a kong")
            print(f"Player {player.player_id} is redrawing")
            latest_tile = self.draw_tile(player)
            return latest_tile

        self.latest_tile = latest_tile
        player.add_tile(drawn_tile)
        # print("Player " + str(player.player_id) + " put the following tile into your hand")
        # print(drawn_tile)
        return drawn_tile

    def play_turn(self) -> Tuple[Optional[int], Optional[str], Optional[List]]:
        """
        Execute actions in the turn in this order
        1. Discard the tile for current player
        2. Check if any other players want to respond to discard
        3. Sort all actions
        4. Return action with the highest priority
        :return: action with the highest priority, or None if no one wants to make actions
        """
        state = self.get_state()
        self.discard_tile(self.current_player, state)
        action_queue = []
        for i in range(0, 4):
            if i == self.current_player_no:
                continue
            player = self.players[i]
            queued_action = player.prepare_action(self.latest_tile, self.circle_wind, self.current_player_no)
            if queued_action is not None:
                action_queue.append(queued_action)

        return self.resolve_actions(action_queue)

    def execute_interrupt(self, actioning_player_id: Optional[int], action_to_execute: Optional[str],
                          possible_indices: Optional[List[int]]) -> bool:
        """
        Execute the interrupt if the action is not None, and return whether any
        action was executed.

        :param actioning_player_id: the player who is interrupting, None if no interrupt
        :param action_to_execute: the action they made, None if no action
        :param possible_indices: indices for sheung only for reference not for comparison
        :return: return True if we performed some computaiton, otherwise False
        """
        if actioning_player_id is not None:
            state = self.get_state()
            actioning_player = self.players[actioning_player_id]
            for player in self.players:
                if player.player_id == actioning_player_id:
                    actioning_player = player
                    break
            if action_to_execute == "win":
                self.game_over = True
                self.winner = actioning_player
                self.log.append({
                    "player_id": actioning_player.player_id,
                    "state": state,
                    "action_type": "win",
                    "is_claim": True,
                    "reward": 0.0,
                    "gameover": True
                })
                return True
            elif action_to_execute == "kong":
                print(f"Kong is called by Player {actioning_player}")
                for _ in range(0, 3):
                    actioning_player.hidden_hand.remove(self.latest_tile)
                actioning_player.revealed_sets.append([self.latest_tile] * 4)
                self.log.append({
                    "player_id": actioning_player.player_id,
                    "state": state,
                    "action_type": "kong",
                    "is_claim": True,
                    "reward": 0.0,
                    "gameover": False
                })
                self.current_player_no = actioning_player.player_order
                self.current_player = actioning_player
                self.draw_tile(actioning_player)
                return True
            elif action_to_execute == "pong":
                print(f"Pong is called by Player {actioning_player_id}")
                for _ in range(2):
                    actioning_player.hidden_hand.remove(self.latest_tile)
                actioning_player.revealed_sets.append([self.latest_tile] * 3)
                self.log.append({
                    "player_id": actioning_player.player_id,
                    "state": state,
                    "action_type": "pong",
                    "is_claim": True,
                    "reward": 0.0,
                    "gameover": False
                })
                self.current_player_no = actioning_player.player_order
                self.current_player = self.players[self.current_player_no]
                return True
            elif action_to_execute == "sheung":
                print(f"Sheung is called by Player {actioning_player_id}")
                indices = possible_indices
                i1, i2 = sorted(indices, reverse=True)

                sheung_tile_1 = actioning_player.hidden_hand.pop(i1)
                sheung_tile_2 = actioning_player.hidden_hand.pop(i2)

                actioning_player.revealed_sets.append([sheung_tile_1, sheung_tile_2, self.latest_tile])
                self.log.append({
                    "player_id": actioning_player.player_id,
                    "state": state,
                    "action_type": "sheung",
                    "is_claim": True,
                    "reward": 0.0,
                    "gameover": False
                })
                self.current_player_no = actioning_player.player_order
                self.current_player = self.players[self.current_player_no]
                return True
        return False

    def discard_tile(self, player: Player, state: np.ndarray = None, tile=None):
        """
        Add the latest tile to the discarded pile and set the latest discarded tile
        to the given tile. Update the game log as necessary.

        :param player: the player who discarded the tile
        :param state: the current game state
        :param tile: the tile that was discarded
        """
        if tile is not None:
            self.discarded_tiles.append(tile)
            self.discarding_player = player
            print(f"Player {player.player_id} discarded {tile}")
            player.hidden_hand.remove(tile)
            player.discard_pile.append(tile)
            self.latest_tile = tile
            self.log.append({
                "player_id": self.current_player.player_id,
                "state": state,
                "action_type": "discard",
                "is_claim": True,
                "reward": 0.0,
                "gameover": False
            })
            return

        discarded_tile = player.discard_tile(state)
        self.latest_tile = discarded_tile
        self.discarded_tiles.append(discarded_tile)
        self.discarding_player = player
        print(f"Player {player.player_id} discarded {discarded_tile}")
        player.hidden_hand.remove(discarded_tile)
        player.discard_pile.append(discarded_tile)
        self.log.append({
            "player_id": self.current_player.player_id,
            "state": state,
            "action_type": "discard",
            "is_claim": True,
            "reward": 0.0,
            "gameover": False
        })
        if len(player.revealed_sets) * 3 + len(player.hidden_hand) != 13:
            player.print_hand()
            raise ValueError

    def next_turn(self, player_skip: int = None):
        """
        Move the turn count to the next player, and update
        current_player and current_player_no

        :param player_skip: the player_id of the person to skip to,
                            if unfilled, then move to the next player
                            consecutively
        """
        if player_skip:
            self.current_player_no = player_skip
            self.current_player = self.players[self.current_player_no]
            return
        self.current_player_no = (self.current_player_no + 1) % 4
        self.current_player = self.players[self.current_player_no]

    def convert_score(self, fan: int, discard_player: int, winning_player: int) -> List[int]:
        """
        Return a size-4 list of ints representing the score gained or lost
        by the player in each given position correspdoning to game.players.

        :param fan: the fan of the winning player
        :param discard_player: the position of the player who discarded the last tile,
                                if discard_player is -1, then the winning player won by
                                self-draw
        :param winning_player: the position of the winning player
        :return: a list of scores to add to each player
        """
        if discard_player == winning_player:
            raise ValueError
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

    # ===================== STATE ENCODING ============================================

    def get_player_state(self, player: Player) -> np.ndarray:
        """
        Calculate the state of a player's hand and return
        :param player: the player whose state to calculation
        :return: a (103, ) numpy array containing information about the game state
        """
        hidden = player.encode_hidden_hand()  # 34
        revealed = player.encode_revealed_hand()  # 34
        discards = player.encode_discarded_pile()  # 34
        potential_fan = np.array([Player.potential_fan(
            player.revealed_sets,
            player.flowers,
            self.circle_wind,
            player.player_order
        ) / 20.0], dtype=np.float32)  # 1, max fan is 20

        # 34*3 + 1 = 103
        return np.concatenate([hidden, revealed, discards, potential_fan])

    def get_state(self) -> np.ndarray:
        """
        Generate an array representing all information about
        the current game state and return it.
        :return: a size (451, ) numpy array containing information about game state
        """
        players = self.players
        player_states = [self.get_player_state(player) for player in players]
        player_states_vec = np.concatenate([ps.flatten() for ps in player_states])  # 4 * 103

        latest_tile_vec = np.zeros(34, dtype=np.float32)  # 34
        if self.latest_tile is not None:
            latest_tile_vec[self.latest_tile.to_index()] = 1.0

        tiles_remaining = np.array([len(self.tiles) / 144], dtype=np.float32)  # 1,
        # normalised since HK Mahjong uses 144 tiles

        current_turn = np.zeros(len(players), dtype=np.float32)  # 4
        current_turn[self.current_player.player_order] = 1.0

        state = np.concatenate([
            player_states_vec,
            latest_tile_vec,
            tiles_remaining,
            current_turn
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

    @staticmethod
    def reward_function(winloss: int, score: int) -> float:
        """

        :param winloss:
        :param score:
        :return:
        """
        return winloss * score

    def resolve_actions(self, actions: List[Tuple[Optional[int], Optional[str], Optional[Tuple[int, int]]]]) \
            -> Tuple[Optional[int], Optional[str], Optional[Tuple[int]]]:
        """
        Return the highest priority item ONLY (in terms of order of action). Mutates
        the actions list to be sorted.
        :param actions: the list of actions, with each item being a 3-tuple containing 1.
                        the player's ID 2. the string action they intend to make and 3. an
                        optional 2-tuple of indices (for sheungs only and not for comparison)
        :return: the item with the highest action priority
        """
        if not actions:
            return None, None, None

        def sort_actions(item):
            """

            :param item:
            :return:
            """
            player_id, action, indices = item

            if player_id is None:
                return -100, -100
            distance = (self.current_player_no - player_id) % 4
            if action == "win":
                return 4, -distance
            if action == "kong":
                return 3, -distance
            if action == "pong":
                return 2, -distance
            if action in {"lower sheung", "middle sheung", "upper sheung", "sheung"}:
                return 1, -distance
            raise ValueError("Invalid action")

        actions.sort(key=sort_actions, reverse=True)
        return actions[0]

    def validate_actions(self, player: Player, action) -> bool:
        """
        Validate a player's choice of action

        :param player: the player whose turn it is to act
        :param action: the action they selected
        :return: return True if move is valid, otherwise False
        """
        if action == "win":
            return Player.decide_win(player, self.latest_tile, self.circle_wind, self.current_player_no)
        elif action == "pong":
            return Player.decide_pong(player, self.latest_tile)
        elif action == "kong":
            return Player.decide_add_kong(player, self.latest_tile)
        elif action == "lower sheung":
            return Player.show_all_possible_sheungs(player, self.latest_tile)[0] is not None
        elif action == "middle sheung":
            return Player.show_all_possible_sheungs(player, self.latest_tile)[1] is not None
        elif action == "upper sheung":
            return Player.show_all_possible_sheungs(player, self.latest_tile)[2] is not None
        return False

    def get_legal_actions(self, discard_turn: bool, player: Player) -> List[int]:
        """
        Return a list of legal actions a player can make at any given moment
        :param discard_turn: whether it is the player's turn to act or if they
                             are responding to another player's discard
        :param player: the player who wants to act
        :return: a list of numerical actions (corresponding to enumerator MahjongActions
                 which the player can legally make
        """
        legal_actions = []

        if discard_turn:
            # player can only discard
            legal_actions.extend(range(len(player.hidden_hand)))
        else:
            # a player can only respond to the move, or pass
            action_map = {
                MahjongActions.WIN: "win",
                MahjongActions.ADD_KONG: "kong",
                MahjongActions.PONG: "pong",
                MahjongActions.LOWER_SHEUNG: "lower sheung",
                MahjongActions.MIDDLE_SHEUNG: "middle sheung",
                MahjongActions.UPPER_SHEUNG: "upper sheung"
            }

            for action_id, action_str in action_map.items():
                if self.validate_actions(player, action_str):
                    legal_actions.append(action_id)

            legal_actions.append(MahjongActions.PASS)

        return legal_actions


"""
        LEGACY PLAY TURN CODE FOR REFERENCE ONLY

        # check_sheung, action_taken = self.check_interrupt(state)
        # if not action_taken and check_sheung and self.latest_tile is not None:  # kong takes latest tile
        #     sheung = self.current_player.decide_sheung(self.latest_tile, state)
        #     if sheung is not None:
        #         print(f"Sheung is called by Player {self.current_player.player_id}")
        #         sheung_tiles = [self.current_player.hidden_hand[sheung[0]],
        #                         self.current_player.hidden_hand[sheung[1]]
        #                         ]
        #         bisect.insort(sheung_tiles, self.latest_tile)
        #         self.current_player.revealed_sets.append(sheung_tiles)
        #         self.current_player.hidden_hand.pop(sheung[0])
        #         self.current_player.hidden_hand.pop(sheung[1] - 1)
        #         self.log.append({
        #             "player_id": self.current_player.player_id,
        #             "state": state,
        #             "action_type": "sheung",
        #             "is_claim": True,
        #             "reward": 0.0,
        #             "gameover": False
        #         })
        #         self.discard_tile(self.current_player, state)
        #
        #     else:
        #         if self.draw_tile(self.current_player) is None:
        #             return
        #         self.discard_tile(self.current_player, state)
        #         self.log.append({
        #             "player_id": self.current_player.player_id,
        #             "state": state,
        #             "action_type": "discard",
        #             "is_claim": False,
        #             "reward": 0.0,
        #             "gameover": False
        #         })
        # elif not action_taken:
        #     if self.game_over:
        #         return
        #     if not action_taken and self.draw_tile(self.current_player) is None:
        #         return
        #     self.discard_tile(self.current_player, state)
        #     self.log.append({
        #         "player_id": self.current_player.player_id,
        #         "state": state,
        #         "action_type": "discard",
        #         "is_claim": False,
        #         "reward": 0.0,
        #         "gameover": False
        #     })
"""
