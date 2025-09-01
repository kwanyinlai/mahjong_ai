import gymnasium as gym
from gymnasium import spaces
import numpy as np

class MahjongEnvironment(gym.env):
    def step(self, action: int):

        player = self.players[self.current_player_no]

        indices = [i for i, tile in enumerate(player.hidden_hand) if tile.to_index() == action]
        if not indices:
            raise ValueError(f"Invalid discard: player does not have {action}")

        discarded_tile = player.hidden_hand.pop(indices[0])
        player.discard_pile.append(discarded_tile)
        self.latest_tile = discarded_tile

        # Advance turn
        self.current_player_no = (self.current_player_no + 1) % 4
        next_player = self.players[self.current_player_no]

        # Next player draws tile
        if len(self.tiles) > 0:
            drawn_tile = self.tiles.pop(0)
            next_player.hidden_hand.append(drawn_tile)
            done = False
            reward = 0
        else:
            done = True
            reward = 0

        next_state = self.get_state(self.current_player_no)
        return next_state, reward, done, {}
