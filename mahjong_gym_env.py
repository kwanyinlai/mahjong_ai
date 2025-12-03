import gym
from gym import spaces
import numpy as np
from mahjong_game import MahjongGame
from rl_bot import RLAgent


class MahjongEnviornmentAdapter(gym.Env):
    """
    .
    """
    game: MahjongGame
    controlling_player_id: int

    def __init__(self, players, circle_wind, controlling_player_id):
        super().__init__()
        self.game = MahjongGame(players, circle_wind)
        self.controlling_player_id = controlling_player_id

        self.action_space = spaces.Discrete(18)
        # 0 - 13: discard tiles 0 to 13
        # 14 claim win
        # 15 claim kong
        # 16 claim pong
        # 17 claim sheung

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

    def reset(self):
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
                action_str = self._map_int_to_action(action)
                self.game.execute_interrupt(self.controlling_player_id, action_str)
                if action_str == "win":
                    reward = 1.0
                    self.game.game_over = True
                elif action_str in ["pong", "kong"]:
                    reward = 0.1
                elif action_str == "sheung":
                    reward = -0.1

            if not self.game.game_over:
                self.game.next_turn()
                self.game.draw_tile(self.game.current_player)

            obs = self.get_observation()
            return obs, reward, self.game.game_over, info

        else:
            actioning_player_id, suggested_action = self.game.play_turn()
            if actioning_player_id is not None and actioning_player_id != self.controlling_player_id:
                self.game.execute_interrupt(actioning_player_id, suggested_action)

            if self.game.current_player == rl_player or self.game.game_over:
                obs = self.get_observation()
                done = self.game.game_over
                return obs, reward, done, info

            if actioning_player_id is None:
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

    def _map_int_to_action(self, action) -> str:
        match action:
            case 14:
                return "win"
            case 15:
                return "kong"
            case 16:
                return "pong"
            case 17:
                return "sheung"
        raise ValueError("Invalid action type")
