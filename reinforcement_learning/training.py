import numpy as np
import torch

from mahjong_environment.ai_bot import YesBot
from mahjong_gym_env import MahjongEnvironmentAdapter

from mahjong_environment.mahjong_game import MahjongGame
from reinforcement_learning.neural_network import PolicyValueNetwork
from reinforcement_learning.rl_bot import RLAgent
from reinforcement_learning.self_play_rl_agent import MahjongModel


class Training:
    """
    Training class for RL training
    """
    num_episodes = 1000

    def run_training_loop(self):
        """
        Run a training loop of num episodes
        :return:
        """
        network = PolicyValueNetwork(MahjongGame.state_size, hidden_layer_size=20)
        decision_model = MahjongModel(network=network)

        ai0 = RLAgent(player_id=0, player_order=0, mahjong_model=decision_model)

        ai1 = RLAgent(player_id=1, player_order=1, mahjong_model=decision_model)

        ai2 = RLAgent(player_id=2, player_order=2, mahjong_model=decision_model)

        ai3 = RLAgent(player_id=3, player_order=3, mahjong_model=decision_model)

        players = [ai0, ai1, ai2, ai3]

        env = MahjongEnvironmentAdapter(
            players=players,
            circle_wind='east',
            controlling_player_id=0
        )
        total_rewards = [0, 0, 0, 0]

        for episode in range(self.num_episodes):
            state = env.reset()  # Reset the environment at the start of each episode
            done = False
            prev_scores = [player.score for player in players]

            while not done and len(env.game.tiles) > 0:
                # ====================== NON-DISCARD PHASE =======================
                legal_actions = [[], [], [], []]
                for i in range(len(players)):
                    player = players[i]
                    our_turn = env.game.current_player == player
                    legal_actions[i] = env.game.get_legal_actions(discard_turn=False, our_turn=our_turn, player=player)

                selected_actions = [player.select_actions(legal_actions, state) for player in players]

                next_state, rewards, done = env.step(selected_actions)

                for i in range(4):
                    player = players[i]
                    player.push_experience((state, selected_actions[i], rewards[i], next_state, done))
                    player.update_model()
                state = next_state
                total_rewards = [total_rewards[i] + rewards[i] for i in range(4)]

                # ====================== DISCARD PHASE =======================
                legal_actions = [[], [], [], []]
                for i in range(len(players)):
                    player = players[i]
                    our_turn = env.game.current_player == player
                    legal_actions[i] = env.game.get_legal_actions(discard_turn=True, our_turn=our_turn, player=player)

                selected_actions = [player.select_actions(legal_actions, state) for player in players]

                next_state, rewards, done = env.step(selected_actions)

                for i in range(4):
                    player = players[i]
                    player.push_experience((state, selected_actions[i], rewards[i], next_state, done))
                    player.update_model()
                state = next_state
                total_rewards = [total_rewards[i] + rewards[i] for i in range(4)]

                if env.game.game_over:  # If the game is over, break early
                    continue

                done = env.game.game_over

            total_rewards += [players[i].score - prev_scores[i] for i in range(4)]
