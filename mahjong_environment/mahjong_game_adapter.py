"""
mahjong_gym_env - wrapper class to adapt for the gymnasium environment
"""

from typing import Dict, List, Optional, Tuple

import gymnasium
from gymnasium import spaces
import numpy as np

from mahjong_actions import MahjongActions
from mahjong_environment.player import Player
from mahjong_game import MahjongGame
from reinforcement_learning.rl_bot import RLAgent
from tile import MahjongTile


class MahjongEnvironmentAdapter(gymnasium.Env):
    """
    An adapter class for a Mahjong game which stores reference to the single
    RL in the game
    """
    game: MahjongGame
    is_discard: bool = True  # if it is a discard turn, True, otherwise interrupt is False

    def __init__(self, players: List[Player] = None, circle_wind: str = '', game=None):
        super().__init__()
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
            shape=(MahjongGame.state_size,),  # size of get_state
            dtype=np.float32
        )
        if game is not None:
            self.game = game
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
        self.is_discard = True
        self.game.current_player_no = 0
        self.game.current_player = self.game.players[0]
        return self.get_observation()

    def step(self, actions: List[int]) -> Tuple[np.ndarray, List[float], bool]:
        """
        Move the environment for a single step
        """

        reward = [0, 0, 0, 0]
        acting_player_index = -1

        if self.is_discard:
            for i in range(4):
                if not actions[i]:
                    acting_player_index = i
                    break
            assert acting_player_index != -1
            acting_player = self.game.players[acting_player_index]
            reward = self._step_discard(reward, acting_player, actions[acting_player_index])
            self.last_actioning_player = acting_player
        else:
            end_turn, reward = self._step_player_interrupt(reward, actions)
            if end_turn:
                self.is_discard = True
                obs = self.get_observation()
                done = self.game.game_over
                return obs, reward, done

        if not self.game.game_over and not self.is_discard:
            self.game.next_turn()
            self.game.draw_tile(self.game.current_player)
        self.is_discard = not self.is_discard
        obs = self.get_observation()
        done = self.game.game_over
        return obs, reward, done

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

    def _step_discard(self, reward, acting_player, action):
        tile_to_discard = acting_player.hidden_hand[action]
        self.game.discard_tile(acting_player, self.game.get_state(), tile=tile_to_discard)

        return reward

    def _step_player_interrupt(self, reward, actions):
        # consider interrupts by other players
        actioning_player_id, action_to_execute, possible_indices = self.game.resolve_actions(actions)
        self.last_actioning_player = self.game.players[actioning_player_id]
        is_interrupted = self.game.execute_interrupt(actioning_player_id, action_to_execute, possible_indices)
        if not is_interrupted:
            # sanity check
            for player in self.game.players:
                if len(player.hidden_hand) % 3 != 1 and not self.game.game_over:
                    player.print_hand()
                    raise ValueError("The players do not have the right number of tiles in hand")
            return False, reward
        else:
            return True, reward
