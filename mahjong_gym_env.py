import gym
from gym import spaces
import numpy as np
from mahjong_game import MahjongGame


class MahjongEnv(gym.Env):
    game: MahjongGame

    def __init__(self, players, circle_wind):
        super().__init__()
        self.game = MahjongGame(players, circle_wind)

        self.action_space = spaces.Discrete(14)
        # 1 - 14: discard tiles 1 to 14
        # 15 claim win
        # 16 claim pong
        # 17 claim sheung
        # 18 claim kong

        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(451,),  # size of get_state
            dtype=np.float32
        )

    def get_observation(self):
        state = self.game.get_state()
        return np.array(state, dtype=np.float32)

    def reset(self):
        self.game.setup_game()
        return self.get_observation()

    def step(self, action):
        raise NotImplementedError

    def render(self, mode='human'):
        raise NotImplementedError
        # implement visuals

    def close(self):
        pass

    def get_valid_actions(self):
        return self.game.get_valid_actions()
