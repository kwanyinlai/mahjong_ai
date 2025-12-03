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
        # 0 - 13: discard tiles 1 to 14
        # 14 claim win
        # 15 claim pong
        # 16 claim sheung
        # 17 claim kong

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

    def step(self, action: int):
        """
        Execute a single step
        :return:
        """
        player = self.game.players[self.controlling_player_id]
        assert player is RLAgent

        if self.controlling_player_id is not self.game.current_player_no:
            self.game.play_turn()



    def render(self, mode='human'):
        raise NotImplementedError
        # implement visuals

    def close(self):
        pass

    def get_valid_actions(self):
        return self.game.get_valid_actions()
