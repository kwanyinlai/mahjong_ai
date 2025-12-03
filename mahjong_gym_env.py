from typing import Optional, Tuple

import gymnasium
from gymnasium import spaces
import numpy as np
from mahjong_game import MahjongGame
from rl_bot import RLAgent
from tile import MahjongTile


class MahjongEnvironmentAdapter(gymnasium.Env):
    """
    .
    """
    game: MahjongGame
    controlling_player_id: int

    def __init__(self, players, circle_wind, controlling_player_id):
        super().__init__()
        self.game = MahjongGame(players, circle_wind)
        self.controlling_player_id = controlling_player_id

        self.action_space = spaces.Discrete(20)
        # 0 - 13: discard tiles 0 to 13
        # 14 claim win
        # 15 claim kong
        # 16 claim pong
        # 17 claim lower sheung
        # 18 claim middle sheung
        # 19 claim upward sheung

        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(451,),  # size of get_state
            dtype=np.float32
        )

    def get_observation(self):
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
        return self.get_observation()

    def step(self, action: int):
        """
        A single step
        """
        rl_player = self.game.players[self.controlling_player_id]
        assert isinstance(rl_player, RLAgent)

        reward = 0.0
        info = {}

        if self.game.current_player == rl_player:
            if action < len(rl_player.hidden_hand):
                tile_to_discard = rl_player.hidden_hand[action]
                self.game.discard_tile(rl_player, self.game.get_state(), tile=tile_to_discard)
            else:
                # invalid action can only discard while it's your turn
                reward -= 1
                obs = self.get_observation()
                return obs, reward, self.game.game_over, info

            # consider interrupts
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
            else:
                obs = self.get_observation()
                done = self.game.game_over
                return obs, reward, done, info

        else:
            ## other players discard ##

            state = self.game.get_state()
            self.game.discard_tile(self.game.current_player, state)

            action_queue = []
            for i in range(0, 4):
                if i == self.game.current_player_no:
                    continue
                elif i == self.controlling_player_id:
                    action_is_valid = self.game.validate_actions(rl_player, action)
                    if not action_is_valid:
                        reward -= 1.0
                        action_str = None
                        print("INVALID ACTION")
                        print(action)
                        print(rl_player.player_id)
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
            else:
                obs = self.get_observation()
                done = self.game.game_over
                return obs, reward, done, info

        if not self.game.game_over:
            self.game.next_turn()
            self.game.draw_tile(self.game.current_player)
        obs = self.get_observation()
        done = self.game.game_over
        return obs, reward, done, info

    def render(self, mode='human'):
        raise NotImplementedError
        # implement visuals

    def close(self):
        pass

    def _map_int_to_action(self, player, action) -> Tuple[str, Optional[Tuple]]:
        match action:
            case 14:
                return "win", None
            case 15:
                return "kong", None
            case 16:
                return "pong", None
            case 17:
                current_tile = self.game.latest_tile
                tile1 = MahjongTile(current_tile.tiletype, current_tile.subtype, current_tile.numchar - 2)
                tile2 = MahjongTile(current_tile.tiletype, current_tile.subtype, current_tile.numchar - 1)
                tile1_ind = player.hidden_hand.index(tile1)
                tile2_ind = player.hidden_hand.index(tile2)
                return "lower sheung", (tile1_ind, tile2_ind)
            case 18:
                current_tile = self.game.latest_tile
                tile1 = MahjongTile(current_tile.tiletype, current_tile.subtype, current_tile.numchar - 1)
                tile2 = MahjongTile(current_tile.tiletype, current_tile.subtype, current_tile.numchar + 1)
                tile1_ind = player.hidden_hand.index(tile1)
                tile2_ind = player.hidden_hand.index(tile2)
                return "middle sheung", (tile1_ind, tile2_ind)
            case 19:
                current_tile = self.game.latest_tile
                tile1 = MahjongTile(current_tile.tiletype, current_tile.subtype, current_tile.numchar + 1)
                tile2 = MahjongTile(current_tile.tiletype, current_tile.subtype, current_tile.numchar + 2)
                tile1_ind = player.hidden_hand.index(tile1)
                tile2_ind = player.hidden_hand.index(tile2)
                return "upper sheung", (tile1_ind, tile2_ind)
        raise ValueError("Invalid action type")
