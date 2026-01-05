from __future__ import annotations

import random
from typing import Dict, Union, List, Optional, Tuple

import numpy as np

from mahjong_environment.mahjong_actions import MahjongActions
from mahjong_environment.player import Player
from mahjong_environment.tile import MahjongTile


class MahjongGame:
    """
    Represents one Mahjong Game
    """
    state_size = 920
    tiles: List[MahjongTile]
    players: List[Player]
    current_player_no: int
    current_player: Player
    discarding_player: Player = None
    discarded_tiles: List[MahjongTile]
    latest_tile: MahjongTile = None
    game_over: bool
    last_acting_player: Player = None
    last_action: MahjongActions
    winner: Optional[Player] = None
    log: List[Dict]
    circle_wind: str = 'east'
    is_discard: bool = True

    def __init__(self, players: List[Player], circle_wind: str):
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

    def setup_game(self):
        """
        Shuffle tiles and deal them to players
        """
        # print("SETUP")
        self.tiles = MahjongGame.initialize_tiles()
        random.shuffle(self.tiles)
        self.initialise_player_hands()
        self.current_player_no = 0
        self.current_player = self.players[self.current_player_no]
        self.discarded_tiles = []
        self.game_over = False

        # print("SETUP COMPLETE")

    # ============================= GAMEPLAY ========================================

    # WARNING THE BELOW IS LEGACY
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
        self.last_acting_player = player
        drawn_tile = self.tiles.pop()
        state = self.get_state()
        # print(f"Player {player.player_id} has drawn {drawn_tile}")
        while drawn_tile.tiletype == "flower" and len(self.tiles) != 0:
            player.flowers.append(drawn_tile)
            drawn_tile = self.tiles.pop()
            # print(f"Player {player.player_id} has redrawn a flower to {drawn_tile}")

        if drawn_tile.tiletype == "flower":
            player.flowers.append(drawn_tile)
            return None

        # if (player.decide_win(drawn_tile, self.circle_wind, self.current_player_no, state)
        #         and Player.decide_win(player, drawn_tile, self.circle_wind, self.current_player_no, state)):
        if Player.decide_win(player, drawn_tile, self.circle_wind, self.current_player_no, state):
            self.game_over = True
            self.winner = player
            print(f"Player {player.player_id} has claimed a win")
            print(player.player_id)
            self.last_action = MahjongActions.WIN
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

        else:

            latest_tile, self.latest_tile = self.latest_tile, drawn_tile

            state = self.get_state()
            while Player.decide_add_kong(player, drawn_tile, state) and player.decide_add_kong(drawn_tile,
                                                                                               state) and len(
                self.tiles) > 0:
                for _ in range(3):
                    self.players[self.current_player_no].hidden_hand.remove(drawn_tile)

                self.players[self.current_player_no].revealed_sets.append([drawn_tile,
                                                                           drawn_tile,
                                                                           drawn_tile,
                                                                           drawn_tile])
                # print(f"Player {player.player_id} has claimed a kong")
                # print(f"Player {player.player_id} is redrawing")
                latest_tile = self.draw_tile(player)

                self.last_acting_player = player
                self.last_action = MahjongActions.ADD_KONG

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

    def execute_interrupt(self, actioning_player_id: Optional[int], action_to_execute: Optional[int]) -> bool:
        """
        Execute the interrupt if the action is not None, and return whether any
        action was executed.

        :param actioning_player_id: the player who is interrupting, None if no interrupt
        :param action_to_execute: the action they made, None if no action
        :return: return True if we performed some computaiton, otherwise False
        """

        if actioning_player_id is not None:
            state = self.get_state()

            if 15 <= action_to_execute <= 19:  # if the interrupt is not a win claim
                self.last_acting_player.discard_pile.pop()  # we stole the tile so remove from discard pile

            actioning_player = self.players[actioning_player_id]
            self.last_acting_player = actioning_player
            for player in self.players:
                if player.player_id == actioning_player_id:
                    actioning_player = player
                    break
            if action_to_execute == MahjongActions.WIN:
                print("WE HAVE WON")
                self.game_over = True
                self.winner = actioning_player
                self.last_action = MahjongActions.WIN
                return True
            elif action_to_execute == MahjongActions.ADD_KONG:
                # print(f"Kong is called by Player {actioning_player}")
                for _ in range(0, 3):
                    actioning_player.hidden_hand.remove(self.latest_tile)
                actioning_player.revealed_sets.append([self.latest_tile] * 4)
                self.current_player_no = actioning_player.player_order
                self.current_player = actioning_player
                self.last_action = MahjongActions.ADD_KONG
                self.draw_tile(actioning_player)
                self.is_discard = True
                return True
            elif action_to_execute == MahjongActions.PONG:
                # print(f"Pong is called by Player {actioning_player_id}")
                for _ in range(2):
                    actioning_player.hidden_hand.remove(self.latest_tile)
                actioning_player.revealed_sets.append([self.latest_tile] * 3)
                self.current_player_no = actioning_player.player_order
                self.current_player = self.players[self.current_player_no]
                self.last_action = MahjongActions.PONG
                self.is_discard = True
                return True
            elif 17 <= action_to_execute <= 19:
                # print(f"Sheung is called by Player {actioning_player_id}")
                indices = self.find_indices(action_to_execute, executing_player=self.players[actioning_player_id])
                i1, i2 = sorted(indices, reverse=True)
                sheung_tile_1 = actioning_player.hidden_hand.pop(i1)
                sheung_tile_2 = actioning_player.hidden_hand.pop(i2)
                actioning_player.revealed_sets.append([sheung_tile_1, sheung_tile_2, self.latest_tile])
                self.current_player_no = actioning_player.player_order
                self.current_player = self.players[self.current_player_no]
                self.last_action = MahjongActions.UPPER_SHEUNG  # doesn't matter what the action is, just that it is a
                # sheung

                self.is_discard = True

                return True
        return False

    def discard_tile(self, player: Player, state: np.ndarray = None, tile=None):
        """
        Add the latest tile to the discarded pile and set the latest discarded tile
        to the given tile.

        :param player: the player who discarded the tile
        :param state: the current game state
        :param tile: the tile that was discarded
        """
        if tile is not None:
            self.discarded_tiles.append(tile)
            self.discarding_player = player
            # print(f"Player {player.player_id} discarded {tile}")
            self.last_acting_player = player
            self.last_action = MahjongActions.DISCARD_TILE_1  # doesn't matter what kind of discard, just that it is a discard
            player.hidden_hand.remove(tile)
            player.discard_pile.append(tile)
            self.latest_tile = tile
        else:
            discarded_tile = player.discard_tile(state)
            self.latest_tile = discarded_tile
            self.discarded_tiles.append(discarded_tile)
            self.discarding_player = player
            self.last_acting_player = player
            self.last_action = MahjongActions.DISCARD_TILE_1  # doesn't matter what kind of discard, just that it is a discard
            player.hidden_hand.remove(discarded_tile)
            player.discard_pile.append(discarded_tile)

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
        :return: a (115, ) numpy array containing information about the game state
        """
        hidden = player.encode_hidden_hand()  # 34 (136 / 4, where 136 is number of tiles - flowers)
        # encoding this to train on complete information, then we can mask it out
        revealed = player.encode_revealed_hand()  # 34 * 4
        discards = player.encode_discarded_pile()  # 34
        flower_set = player.encode_flower_set()  # 8
        potential_fan = np.array([Player.potential_fan(
            player.revealed_sets,
            player.flowers,
            self.circle_wind,
            player.player_order
        ) / 20.0], dtype=np.float32)  # 1, max fan is 20
        seat_wind_vec = np.zeros(4, dtype=np.float32)  # 4
        seat_wind_index = player.player_order % 4  # simplified to always assume constant seat wind
        # corresponding to order
        seat_wind_vec[seat_wind_index] = 1.0

        # 34*3 + 8 + 4 + 1 = 217
        return np.concatenate([hidden, revealed, discards, flower_set, seat_wind_vec, potential_fan])

    def get_state(self) -> np.ndarray:
        """
        Generate an array representing all information about
        the current game state and return it.
        :return: a size (MahjongGame.state_size, ) numpy array containing information about game state
        """
        players = self.players
        player_states = [self.get_player_state(player) for player in players]
        player_states_vec = np.concatenate([ps.flatten() for ps in player_states])  # 4 * 217

        latest_tile_vec = np.zeros(34, dtype=np.float32)  # 34
        if self.latest_tile is not None:
            latest_tile_vec[self.latest_tile.to_index()] = 1.0

        discarding_player_vec = np.zeros(4, dtype=np.float32)
        if self.discarding_player is not None:
            discarding_player_vec[self.discarding_player.player_id] = 1.0
        # 4

        tiles_remaining = np.array([len(self.tiles) / 144], dtype=np.float32)  # 1,
        # normalised since HK Mahjong uses 144 tiles

        current_turn = np.zeros(len(players), dtype=np.float32)  # 4
        current_turn[self.current_player.player_order] = 1.0

        circle_wind_vec = np.zeros(4, dtype=np.float32)
        circle_wind_mapping = {'east': 0, 'south': 1, 'west': 2, 'north': 3}
        circle_wind_vec[circle_wind_mapping[self.circle_wind]] = 1.0  # 4

        last_acting_player_vec = np.zeros(4, dtype=np.float32)
        if self.last_acting_player is not None:
            last_acting_player_vec[self.last_acting_player.player_id] = 1.0  # 4

        is_discard_vec = np.array([float(self.is_discard)], dtype=np.float32)

        state = np.concatenate([
            player_states_vec,
            latest_tile_vec,
            discarding_player_vec,
            tiles_remaining,
            current_turn,
            circle_wind_vec,
            last_acting_player_vec,
            is_discard_vec
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

    def resolve_actions(self, actions: List[Tuple[Optional[int], Optional[MahjongActions]]]) -> (
            Tuple[Optional[int], Optional[MahjongActions]]):
        """
        Return the highest priority item ONLY (in terms of order of action). Mutates
        the actions list to be sorted.
        :param actions: the list of actions, with each item being a 2-tuple containing 1.
                        the player's ID 2. the MahjongActions action they intend to make
        :return: the item with the highest action priority
        """
        if not actions:
            return None, None

        def sort_actions(item):
            """

            :param item:
            :return:
            """
            # player_id, action, indices = item
            player_id, action = item

            distance = (self.current_player_no - player_id) % 4
            if action == 14:
                return 4, -distance
            if action == 15:
                return 3, -distance
            if action == 16:
                return 2, -distance
            if 17 <= action <= 19:
                return 1, -distance
            if action == 20:
                return -100, -100
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
        if self.latest_tile is None:
            return False
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

    def get_legal_actions(self, discard_turn: bool, our_turn: bool, player: Player) -> List[int]:
        """
        Return a list of legal actions a player can make at any given moment
        :param discard_turn: whether it is the player's turn to act or if they
                             are responding to another player's discard
        :param player: the player who wants to act
        :return: a list of numerical actions (corresponding to enumerator MahjongActions
                 which the player can legally make
        """
        legal_actions = []

        if discard_turn and our_turn:
            # player can only discard
            legal_actions.extend(range(len(player.hidden_hand)))
        elif discard_turn or (our_turn and not discard_turn):
            legal_actions = [MahjongActions.PASS]
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

    @staticmethod
    def reconstruct_game(state: np.ndarray, injected_decision_model: Optional[MahjongModel] = None) -> Tuple[
        MahjongGame, bool]:
        """
        Reconstruct a MahjongGame from the given state array.

        :param state: A numpy array representing the game state.
        :return: A new MahjongGame instance reconstructed from the state.
        """
        game = object.__new__(MahjongGame)
        players = []
        player_states_vec = state[:868]  # 217 * 4 = 868 values correspond to all player states

        total_tiles = np.zeros(34, dtype=np.float32)  # 34
        # 217 size state
        for i in range(4):
            player_start_index = i * 217
            player_end_index = (i + 1) * 217
            player_state = player_states_vec[player_start_index:player_end_index]
            total_tiles += player_state[: 34]  # hidden hand

            total_tiles += player_state[34: 34 * 2]   # revealed_set 1
            total_tiles += player_state[34 * 2: 34 * 3]  # revealed_set 2
            total_tiles += player_state[34 * 3: 34 * 4]  # revealed_set 3
            total_tiles += player_state[34 * 4: 34 * 5]  # revealed_set 4

            total_tiles += player_state[34 * 5: 34 * 6]  # discarded_pile

            assert len(total_tiles) <= 50

            player = Player.player_from_player_state(
                player_state, i, i
            )

            players.append(player)
            player_state_regenerated = game.get_player_state(player)
            assert all(player_state_regenerated[i] == player_state[i] for i in range(len(player_state_regenerated) - 5))
        # for i in range(len(total_tiles)):
        #     if total_tiles[i] > 1.0:
        #         print(f"ERROR TILE {i}")
        #         assert all(tile <= 1.0 for tile in total_tiles), "Invalid tile counts detected during reconstruction." + str(tile)

        # print(total_tiles)
        latest_tile_vec = state[868:902]
        if all(latest_tile == 0.0 for latest_tile in latest_tile_vec):
            latest_tile = None
        else:
            latest_tile_index = np.argmax(latest_tile_vec)
            latest_tile = MahjongTile.index_to_tile(
                int(latest_tile_index)
            )


        discarding_player_vec = state[902:906]
        discarding_player_id = np.argmax(discarding_player_vec)
        discarding_player = players[discarding_player_id]

        tiles_remaining = int(state[906] * 144)  # might be redundant information??

        current_turn_vec = state[907:911]
        current_player_id = np.argmax(current_turn_vec)
        current_player = players[current_player_id]

        # Rebuild circle wind information
        circle_wind_vec = state[911:915]  # The next 4 values are for the circle wind
        circle_wind_index = np.argmax(circle_wind_vec)
        circle_wind_mapping = {0: 'east', 1: 'south', 2: 'west', 3: 'north'}
        circle_wind = circle_wind_mapping[int(circle_wind_index)]

        last_acting_player_vec = state[915:919]
        last_acting_player_index = np.argmax(last_acting_player_vec)
        last_acting_player = players[last_acting_player_index]
        is_discard = bool(state[919:920][0])



        game.players = players

        game.tiles = MahjongGame.initialize_tiles()
        assert len(game.tiles) == 144
        tile_count = {}
        for tile in game.tiles:
            if tile in tile_count:
                tile_count[tile] += 1
            else:
                tile_count[tile] = 1
        # assert all(count == 4 or (count == 1 and tile.tiletype == 'flower') for tile, count in tile_count.items())
        # for player in game.players:
        #     for tile in player.hidden_hand:
        #         game.tiles.remove(tile)
        #     for tile_set in player.revealed_sets:
        #         for tile in tile_set:
        #             game.tiles.remove(tile)

        # print(f"\nInitial tile pool size: {len(game.tiles)}")

        # Track what we're removing
        tiles_to_remove = []

        all_discarded = []

        for player_idx, player in enumerate(game.players):
            # print(f"\nPlayer {player_idx}:")
            # print(f"  Hidden hand: {len(player.hidden_hand)} tiles")
            # print(f"  Revealed sets: {sum(len(s) for s in player.revealed_sets)} tiles")
            # print(f"  Flowers: {len(player.flowers)} tiles")
            # print(f"  Discard pile: {len(player.discard_pile)} tiles")

            # Hidden hand
            for tile in player.hidden_hand:
                tiles_to_remove.append(('hidden', player_idx, tile))

            # Revealed sets
            for tile_set in player.revealed_sets:
                for tile in tile_set:
                    tiles_to_remove.append(('revealed', player_idx, tile))

            # Flowers
            for flower in player.flowers:
                assert flower.tiletype == 'flower'
                tiles_to_remove.append(('flower', player_idx, flower))

            # Discard pile
            for tile in player.discard_pile:
                tiles_to_remove.append(('discard', player_idx, tile))
                all_discarded.append(tile)

        # assert len(tiles_to_remove) <= 144
        for _, _, tile in tiles_to_remove:
            tile_count[tile] -= 1
        # assert all(count >= 0 for count in tile_count.values())

        tile_count = {}
        for _, _, tile in tiles_to_remove:
            if tile not in tile_count:
                tile_count[tile] = 1
            else:
                tile_count[tile] += 1

        # assert all(count <= 4 for count in tile_count.values())

        # Now try to remove tiles and catch the problematic one
        removed_tiles_so_far = 0
        for source, player_idx, tile in tiles_to_remove:
            try:
                removed_tiles_so_far += 1
                game.tiles.remove(tile)
            except ValueError:
                print(f"\n!!! ERROR: Cannot remove tile from {source} of player {player_idx}")
                print(f"    Latest tile: {game.latest_tile}")
                for player in game.players:
                    player.all_tiles()
                print(f"    Tile: {tile}")
                print(f"    Tile details: type={tile.tiletype}, subtype={tile.subtype}, numchar={tile.numchar}")

                # Check if any similar tiles exist
                matching_tiles = [t for t in game.tiles if t == tile]
                print(f"    Matching tiles in pool: {len(matching_tiles)}")

                # Count this tile type
                tile_count = sum(1 for t in game.tiles if t.tiletype == tile.tiletype
                                 and t.subtype == tile.subtype and t.numchar == tile.numchar)
                print(f"    This tile type count in pool: {tile_count}")

                # Show total tiles remaining
                print(f"    Total tiles in pool: {len(game.tiles)}")
                print(f"    Total tiles removed so far: {removed_tiles_so_far}")

                raise

        # print(f"\nFinal tile pool size: {len(game.tiles)}")

        game.current_player = current_player
        game.current_player_no = current_player.player_order
        game.latest_tile = latest_tile
        game.discarding_player = discarding_player
        game.game_over = False
        game.last_acting_player = last_acting_player
        game.circle_wind = 'east'  # circle_wind

        game.is_discard = is_discard
        game.discarded_tiles = []

        return game, is_discard

    def find_indices(self, action_to_execute: MahjongActions, executing_player: Player):
        """
        Action must be a SHEUNG action. Return the indices of the two other tiles making up the
        sheung
        :param action_to_execute:
        :return:
        """
        if action_to_execute == MahjongActions.LOWER_SHEUNG:
            tile1 = MahjongTile(tiletype=self.latest_tile.tiletype, subtype=self.latest_tile.subtype,
                                numchar=self.latest_tile.numchar - 2)
            tile2 = MahjongTile(tiletype=self.latest_tile.tiletype, subtype=self.latest_tile.subtype,
                                numchar=self.latest_tile.numchar - 1)
        elif action_to_execute == MahjongActions.MIDDLE_SHEUNG:
            tile1 = MahjongTile(tiletype=self.latest_tile.tiletype, subtype=self.latest_tile.subtype,
                                numchar=self.latest_tile.numchar - 1)
            tile2 = MahjongTile(tiletype=self.latest_tile.tiletype, subtype=self.latest_tile.subtype,
                                numchar=self.latest_tile.numchar + 1)
        else:
            tile1 = MahjongTile(tiletype=self.latest_tile.tiletype, subtype=self.latest_tile.subtype,
                                numchar=self.latest_tile.numchar + 1)
            tile2 = MahjongTile(tiletype=self.latest_tile.tiletype, subtype=self.latest_tile.subtype,
                                numchar=self.latest_tile.numchar + 2)
        return executing_player.hidden_hand.index(tile1), executing_player.hidden_hand.index(tile2)

    def find_legal_transitions(self):
        legal_actions_by_player = [self.get_legal_actions(
            discard_turn=self.is_discard,
            our_turn=player == self.current_player,
            player=player)
            for player in self.players
        ]
        for i in range(4):
            legal_actions_by_player[i].pop()  # remove the PASS option for everyone
        return [(i, legal_actions_by_player[i][j]) for i in range(4) for j in range(len(legal_actions_by_player[i]))]
