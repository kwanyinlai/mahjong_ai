from ai_bot import YesBot
from mahjong_gym_env import MahjongEnvironmentAdapter
from policy import SimplePolicy
from rl_bot import RLAgent


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
        agent = RLAgent(policy=SimplePolicy(), player_id=0, player_order=0)

        ai1 = YesBot(player_id=1, player_order=1)
        ai2 = YesBot(player_id=2, player_order=2)
        ai3 = YesBot(player_id=3, player_order=3)

        players = [agent, ai1, ai2, ai3]

        env = MahjongEnvironmentAdapter(
            players=players,
            circle_wind='east',
            controlling_player_id=0
        )

        for episode in range(self.num_episodes):
            state = env.reset()
            done = False
            total_reward = 0
            print(done)
            print(len(env.game.tiles))
            prev_score = agent.score
            while not done and len(env.game.tiles) > 0:
                # NON-DISCARD STEP
                our_turn = env.game.current_player == agent
                legal_actions = env.game.get_legal_actions(discard_turn=True, our_turn=our_turn, player=agent)
                print(legal_actions)
                action = agent.select_actions(legal_actions, state)
                next_state, reward, done, info = env.step(action)
                agent.push_experience((state, action, reward, next_state, done))
                agent.update_model()
                state = next_state
                total_reward += reward

                # DISCARD STEP
                legal_actions = env.game.get_legal_actions(discard_turn=False, our_turn=our_turn, player=agent)
                print(legal_actions)
                action = agent.select_actions(legal_actions, state)
                next_state, reward, done, info = env.step(action)
                agent.push_experience((state, action, reward, next_state, done))
                agent.update_model()
                state = next_state
                if env.game.game_over:
                    continue

                print()
                print("NUM TILES = " + str(len(env.game.tiles)))
                print()
                done = env.game.game_over
                total_reward += reward
            total_reward += agent.score - prev_score
            print(f"Episode {episode + 1}/{self.num_episodes}, Total Reward: {total_reward}")
