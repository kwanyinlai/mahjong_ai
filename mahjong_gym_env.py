"""
mahjong_gym_env - wrapper class to adapt for the gymnasium environment
"""

from typing import Dict, Optional, Tuple

import gymnasium
from gymnasium import spaces
import numpy as np

from mahjong_actions import MahjongActions
from mahjong_game import MahjongGame
from rl_bot import RLAgent
from tile import MahjongTile


class MahjongEnvironmentAdapter(gymnasium.Env):
    """
    An adapter class for a Mahjong game which stores reference to the single
    RL in the game
    """
    game: MahjongGame
    controlling_player_id: int
    is_discard: bool = True  # if it is a discard turn, True, otherwise interrupt is False

    def __init__(self, players, circle_wind, controlling_player_id):
        super().__init__()
        self.game = MahjongGame(players, circle_wind)
        self.controlling_player_id = controlling_player_id

        self.action_space = spaces.Discrete(21)
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
            shape=(451,),  # size of get_state
            dtype=np.float32
        )

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
        self.game.setup_game()
        self.game.current_player_no = 0
        self.game.current_player = self.game.players[0]
        return self.get_observation()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Move the environment for a single step
        """
        rl_player = self.game.players[self.controlling_player_id]
        assert isinstance(rl_player, RLAgent)
        # make sure our controlling player is actually an RL agent

        reward = 0.0
        info = {}

        if self.game.current_player == rl_player and self.is_discard:
            reward, info = self._step_our_discard(reward, info, rl_player, action)
        elif self.game.current_player == rl_player and not self.is_discard:
            end_turn, reward, info = self._step_other_player_interrupt(reward, info, rl_player, action)
            if end_turn:
                self.is_discard = not self.is_discard
                obs = self.get_observation()
                done = self.game.game_over
                return obs, reward, done, info
        elif self.game.current_player != rl_player and self.is_discard:
            # other players discard
            state = self.game.get_state()
            self.game.discard_tile(self.game.current_player, state)
        else:
            end_turn, reward, info = self._step_our_interrupt(reward, info, rl_player, action)
            if end_turn:
                self.is_discard = not self.is_discard
                obs = self.get_observation()
                done = self.game.game_over
                return obs, reward, done, info

        if not self.game.game_over and not self.is_discard:
            self.game.next_turn()
            self.game.draw_tile(self.game.current_player)
        self.is_discard = not self.is_discard
        obs = self.get_observation()
        done = self.game.game_over
        return obs, reward, done, info

    def close(self):
        pass

    def _map_int_to_action(self, player, action) -> Tuple[Optional[str], Optional[Tuple]]:
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

    def _step_our_discard(self, reward, info, rl_player, action):
        tile_to_discard = rl_player.hidden_hand[action]
        self.game.discard_tile(rl_player, self.game.get_state(), tile=tile_to_discard)

        return reward, info

    def _step_other_player_interrupt(self, reward, info, rl_player, action):
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
        actioning_player_id, action_to_execute, possible_indices = self.game.resolve_actions(action_queue)

        is_interrupted = self.game.execute_interrupt(actioning_player_id, action_to_execute, possible_indices)
        if not is_interrupted:
            # sanity check
            for player in self.game.players:
                if len(player.hidden_hand) % 3 != 1 and not self.game.game_over:
                    player.print_hand()
                    raise ValueError("The players do not have the right number of tiles in hand")
            return False, reward, info
        else:
            return True, reward, info

    def _step_our_interrupt(self, reward, info, rl_player, action):
        action_queue = []
        for i in range(0, 4):
            if i == self.game.current_player_no:
                continue
            elif i == self.controlling_player_id:
                if action == MahjongActions.PASS:
                    continue
                action_is_valid = self.game.validate_actions(rl_player, action)
                if not action_is_valid:
                    reward -= 1.0
                    action_str = None
                    print(action)
                    raise RuntimeError("We should not be permitted to make invalid actions")
                else:
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
            return False, reward, info
        else:
            return True, reward, info
