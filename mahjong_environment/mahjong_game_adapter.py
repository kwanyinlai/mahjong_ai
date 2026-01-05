"""
mahjong_gym_env - wrapper class to adapt for the gymnasium environment
"""

from typing import Dict, List, Optional, Tuple

from gymnasium import spaces  # TODO???
import numpy as np

from mahjong_environment.mahjong_actions import MahjongActions
from mahjong_environment.player import Player
from mahjong_environment.mahjong_game import MahjongGame
from reinforcement_learning.rl_bot import RLAgent
from mahjong_environment.tile import MahjongTile


# TODO: need to model the game step-wise, by querying everyone for
# TODO: win claim, then kong claim, then pong claim, then sheung claim
# TODO: then proceed to draw + discard


class MahjongEnvironmentAdapter:
    """
    An adapter class for a Mahjong game which stores reference to the single
    RL in the game
    """
    game: MahjongGame
    is_discard: bool = True  # if it is a discard turn, True, otherwise interrupt is False
    controlling_player_id: int

    def __init__(self, controlling_player_id: int, players: List[Player] = None, circle_wind: str = '', game=None,
                 discard_turn=True):
        super().__init__()
        self.action_space = spaces.Discrete(21)
        self.controlling_player_id = controlling_player_id
        # 0 - 13: discard tiles 0 to 13
        # 14 claim win
        # 15 claim kong
        # 16 claim pong
        # 17 claim lower sheung
        # 18 claim middle sheung
        # 19 claim upward sheung
        # 20 for pass (no action)
        # all of these corresponds to enum in MahjongActions (mahjong_actions.py)

        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(MahjongGame.state_size,),  # size of get_state
            dtype=np.float32
        )
        if game is not None:
            self.game = game
            self.game.is_discard = discard_turn
        else:
            self.game = MahjongGame(players, circle_wind)

    def get_observation(self) -> np.ndarray:
        """
        Return the state of the game
        :return:
        """
        state = self.game.get_state()
        return np.array(state, dtype=np.float32)

    def reset(self) -> np.ndarray:
        """
        Reset the game state
        :return:
        """

        for player in self.game.players:
            player.soft_reset()
        self.game.setup_game()
        self.game.is_discard = True
        self.game.current_player_no = 0
        self.game.current_player = self.game.players[0]
        return self.get_observation()


    def step(self, action: int) -> Tuple[np.ndarray, bool]:
        """
        Move the environment for a single step.
        Alternates between DISCARD phase (is_discard=True) and INTERRUPT phase (is_discard=False).

        DISCARD phase: Current player discards a tile
        INTERRUPT phase: Other players respond to the discard (win/kong/pong/sheung/pass)
        """
        rl_player = self.game.players[self.controlling_player_id]
        assert isinstance(rl_player, RLAgent)

        # ==================== DISCARD PHASE ====================
        if self.game.is_discard:
            # Handle discard by current player
            if self.game.current_player == rl_player:
                # RL player discards
                self._step_our_discard(rl_player, action)
            else:
                # Other player discards
                state = self.game.get_state()
                self.game.discard_tile(self.game.current_player, state)

            # Transition to interrupt phase
            self.game.is_discard = False
            obs = self.get_observation()
            done = self.game.game_over
            return obs, done

        # ==================== INTERRUPT PHASE ====================
        else:
            # Determine who handles the interrupt
            if self.game.current_player == rl_player:
                # RL player just discarded, other players respond
                end_turn = self._step_other_player_interrupt(rl_player, action)
            else:
                # Other player discarded, RL player responds
                end_turn = self._step_our_interrupt(rl_player, action)

            if end_turn:
                # Someone interrupted with kong/pong/sheung/win
                # The interrupt handler already updated game state
                # Just transition back to discard phase
                self.game.is_discard = True
            else:
                # Everyone passed, no interrupt
                # Advance to next player and draw tile
                self.game.is_discard = True
                self.game.next_turn()
                if not self.game.game_over:
                    self.game.draw_tile(self.game.current_player)

            obs = self.get_observation()
            done = self.game.game_over
            return obs, done

    def step_with_resolved_action(self, actioner_id: int, action: int) -> Tuple[np.ndarray, bool]:
        """
        Force apply the action without performing checks.
        Follows the same discard/interrupt phase pattern.

        :param actioner_id: The player performing the action
        :param action: The action to perform (0-13 for discard, 14-20 for claims)
        :return:
        """
        actioning_player = self.game.players[actioner_id]

        # ==================== DISCARD PHASE ====================
        if self.game.is_discard:
            # Action must be a discard (0-13)
            assert 0 <= action <= 13, f"Expected discard action (0-13), got {action}"
            self._step_discard(actioner_id, action)

            # Transition to interrupt phase
            self.game.is_discard = False
            obs = self.get_observation()
            done = self.game.game_over
            return obs, done

        # ==================== INTERRUPT PHASE ====================
        else:
            if action == MahjongActions.PASS:
                # Everyone passed, advance turn
                self.game.is_discard = True
                self.game.next_turn()
                if not self.game.game_over:
                    self.game.draw_tile(self.game.current_player)
            else:
                # Someone interrupted
                end_turn = self._step_exact_interrupt(actioner_id, action)
                self.game.is_discard = True

                if not end_turn:
                    # Interrupt didn't end turn (shouldn't happen with resolved actions)
                    self.game.next_turn()
                    if not self.game.game_over:
                        self.game.draw_tile(self.game.current_player)

            obs = self.get_observation()
            done = self.game.game_over
            return obs, done

    def step_with_resolved_action(self, actioner_id: int, action: int) -> Tuple[np.ndarray, bool]:
        """
        Force apply the action without performing checks.
        Follows the same discard/interrupt phase pattern.

        :param actioner_id: The player performing the action
        :param action: The action to perform (0-13 for discard, 14-20 for claims)
        :return: Observation and done flag
        """
        actioning_player = self.game.players[actioner_id]

        # ==================== DISCARD PHASE ====================
        if self.game.is_discard:
            # Action must be a discard (0-13)
            assert 0 <= action <= 13, f"Expected discard action (0-13), got {action}"
            self._step_discard(actioner_id, action)

            # Transition to interrupt phase
            self.game.is_discard = False
            obs = self.get_observation()
            done = self.game.game_over
            return obs, done

        # ==================== INTERRUPT PHASE ====================
        else:
            if action == MahjongActions.PASS:
                # Everyone passed, advance turn
                self.game.is_discard = True
                self.game.next_turn()
                if not self.game.game_over:
                    self.game.draw_tile(self.game.current_player)
            else:
                # Someone interrupted
                end_turn = self._step_exact_interrupt(actioner_id, action)
                self.game.is_discard = True

                if not end_turn:
                    # Interrupt didn't end turn (shouldn't happen with resolved actions)
                    self.game.next_turn()
                    if not self.game.game_over:
                        self.game.draw_tile(self.game.current_player)

            obs = self.get_observation()
            done = self.game.game_over
            return obs, done

    def step_with_all_actions(self, actions: List[Tuple[int, int]]) -> Tuple[np.ndarray, bool]:
        """
        Take in all players' actions for the current phase.

        :param actions: List of (player_id, action) tuples for each player, in order
        :return:
        """
        # ==================== DISCARD PHASE ====================
        if self.game.is_discard:
            # Find who is discarding
            acting_player_index = -1
            for i in range(4):
                if actions[i] is not None and actions[i][1] != MahjongActions.PASS:
                    acting_player_index = actions[i][0]
                    break

            assert acting_player_index != -1, "No valid discard action found"
            assert acting_player_index == self.game.current_player_no, \
                f"Expected current player {self.game.current_player_no} to discard, got {acting_player_index}"

            action_value = actions[acting_player_index][1]
            assert 0 <= action_value <= 13, f"Expected discard action (0-13), got {action_value}"

            self._step_discard(acting_player_index, action_value)

            # Transition to interrupt phase
            self.game.is_discard = False
            obs = self.get_observation()
            done = self.game.game_over
            return obs, done

        # ==================== INTERRUPT PHASE ====================
        else:
            # Collect all non-pass actions
            action_queue = []
            for i in range(4):
                if actions[i] is not None and actions[i][1] != MahjongActions.PASS:
                    action_queue.append(actions[i])

            if action_queue:
                # Someone interrupted, resolve priority
                end_turn = self._step_player_interrupt(action_queue)
                self.game.is_discard = True

                if not end_turn:
                    # No actual interrupt executed, advance turn
                    self.game.next_turn()
                    if not self.game.game_over:
                        self.game.draw_tile(self.game.current_player)
            else:
                # Everyone passed
                self.game.is_discard = True
                self.game.next_turn()
                if not self.game.game_over:
                    self.game.draw_tile(self.game.current_player)

            obs = self.get_observation()
            done = self.game.game_over
            return obs, done

    def _map_int_to_action(self, player, action) -> Tuple[Optional[str], Optional[Tuple]]:
        if 0 <= action <= 13:
            return None, None
        match action:
            case MahjongActions.WIN:
                return "win", None
            case MahjongActions.ADD_KONG:
                return "kong", None
            case MahjongActions.PONG:
                return "pong", None
            case MahjongActions.LOWER_SHEUNG:
                current_tile = self.game.latest_tile
                tile1 = MahjongTile(current_tile.tiletype, current_tile.subtype, current_tile.numchar - 2)
                tile2 = MahjongTile(current_tile.tiletype, current_tile.subtype, current_tile.numchar - 1)
                tile1_ind = player.hidden_hand.index(tile1)
                tile2_ind = player.hidden_hand.index(tile2)
                return "lower sheung", (tile1_ind, tile2_ind)
            case MahjongActions.MIDDLE_SHEUNG:
                current_tile = self.game.latest_tile
                tile1 = MahjongTile(current_tile.tiletype, current_tile.subtype, current_tile.numchar - 1)
                tile2 = MahjongTile(current_tile.tiletype, current_tile.subtype, current_tile.numchar + 1)
                tile1_ind = player.hidden_hand.index(tile1)
                tile2_ind = player.hidden_hand.index(tile2)
                return "middle sheung", (tile1_ind, tile2_ind)
            case MahjongActions.UPPER_SHEUNG:
                current_tile = self.game.latest_tile
                tile1 = MahjongTile(current_tile.tiletype, current_tile.subtype, current_tile.numchar + 1)
                tile2 = MahjongTile(current_tile.tiletype, current_tile.subtype, current_tile.numchar + 2)
                tile1_ind = player.hidden_hand.index(tile1)
                tile2_ind = player.hidden_hand.index(tile2)
                return "upper sheung", (tile1_ind, tile2_ind)
            case MahjongActions.PASS:
                return None, None
        raise ValueError("Invalid action type")

    def _step_discard(self, acting_player_id, action):
        assert 0 <= action <= 14
        acting_player = self.game.players[acting_player_id]
        tile_to_discard = acting_player.hidden_hand[action]
        self.game.discard_tile(acting_player, self.game.get_state(), tile=tile_to_discard)

    def _step_player_interrupt(self, actions: List[Tuple[int, MahjongActions]]) -> bool:
        # consider interrupts by other players
        actioning_player_id, action_to_execute = self.game.resolve_actions(actions)
        self.last_actioning_player = self.game.players[actioning_player_id]
        is_interrupted = self.game.execute_interrupt(actioning_player_id, action_to_execute)
        if not is_interrupted:
            # sanity check
            for player in self.game.players:
                if len(player.hidden_hand) % 3 != 1 and not self.game.game_over:
                    player.print_hand()
                    raise ValueError("The players do not have the right number of tiles in hand")
            return False
        else:
            return True

    def _step_our_discard(self, rl_player, action):
        tile_to_discard = rl_player.hidden_hand[action]
        self.game.discard_tile(rl_player, self.game.get_state(), tile=tile_to_discard)
        self.game.is_discard = False

    def _step_other_player_interrupt(self, rl_player, action):
        # consider interrupts by other players
        action_queue = []
        for i in range(0, 4):
            if i == rl_player.player_id:
                continue
            else:
                player = self.game.players[i]
                queued_action = player.prepare_action(self.game.latest_tile,
                                                      self.game.circle_wind,
                                                      self.game.current_player_no)
                if queued_action is not None:
                    action_queue.append(queued_action)
        actioning_player_id, action_to_execute = self.game.resolve_actions(action_queue)

        is_interrupted = self.game.execute_interrupt(actioning_player_id, action_to_execute)

        if not is_interrupted:
            # sanity check
            for player in self.game.players:
                if len(player.hidden_hand) % 3 != 1 and not self.game.game_over:
                    player.print_hand()
                    raise ValueError("The players do not have the right number of tiles in hand")
            return False
        else:
            return True

    def _step_our_interrupt(self, rl_player, action):
        action_queue = []
        for i in range(0, 4):
            if i == self.game.current_player_no:
                continue
            elif i == self.controlling_player_id:
                if action == MahjongActions.PASS:
                    continue
                action_str, possible_indices = self._map_int_to_action(rl_player, action)
                if action_str is not None:
                    action_queue.append(
                        (
                            self.controlling_player_id, action_str, possible_indices
                        )
                    )
            else:
                player = self.game.players[i]
                queued_action = player.prepare_action(self.game.latest_tile,
                                                      self.game.circle_wind,
                                                      self.game.current_player_no)
                if queued_action is not None:
                    action_queue.append(queued_action)
        actioning_player_id, action_to_execute, possible_indices = self.game.resolve_actions(action_queue)
        is_interrupted = self.game.execute_interrupt(actioning_player_id, action_to_execute, possible_indices)

        if not is_interrupted:
            for player in self.game.players:
                if len(player.hidden_hand) % 3 != 1 and not self.game.game_over:
                    player.print_hand()
                    raise ValueError("The players do not have the right number of tiles in hand")
            return False
        else:
            return True

    def _step_exact_interrupt(self, actioner_id, action):

        is_interrupted = self.game.execute_interrupt(actioner_id, action)
        if not is_interrupted:
            # sanity check
            for player in self.game.players:
                if len(player.hidden_hand) % 3 != 1 and not self.game.game_over:
                    player.print_hand()
                    raise ValueError("The players do not have the right number of tiles in hand")
            return False
        else:
            return True
