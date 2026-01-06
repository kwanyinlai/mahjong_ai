from mahjong_environment.mahjong_actions import MahjongActions
from mahjong_environment.mahjong_game import MahjongGame
from mahjong_environment.mahjong_game_adapter import MahjongEnvironmentAdapter
from reinforcement_learning.neural_network import PolicyValueNetwork
from reinforcement_learning.rl_bot import RLAgent
from reinforcement_learning.decision_model import MahjongModel


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
        network = PolicyValueNetwork(state_size=MahjongGame.state_size,
                                     action_space=21,  # TODO: rdefine in constant
                                     hidden_layer_size=20)
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

        for _ in range(self.num_episodes):
            episode_memory = [[], [], [], []]
            state = env.reset()  # Reset the environment at the start of each episode
            done = False
            prev_scores = [player.score for player in players]
            turn_no = 1  # for debugging only
            while not done and len(env.game.tiles) > 0:
                print(f"=================TURN {turn_no}===================")
                print(f"It is player {env.game.current_player_no}'s turn to discard")
                # ====================== ====================== ======================
                # ====================== DISCARD PHASE ===========================
                # ====================== ====================== ======================
                state = env.game.get_state()
                legal_actions = [[], [], [], []]
                env.game.is_discard = True
                for i in range(len(players)):
                    player = players[i]
                    our_turn = env.game.current_player == player
                    legal_actions[i] = env.game.get_legal_actions(discard_turn=True, our_turn=our_turn, player=player)

                selected_actions = [(i, MahjongActions(player.select_actions(legal_actions[i], state)))
                                    for i, player in enumerate(players)]
                # TODO: Mask public state before passing to decision model
                for i in range(4):
                    if selected_actions[i][1] == 20:
                        continue
                    print(f"Player {i} chose action {MahjongActions(selected_actions[i][1])}")
                    print(f"Player {i}'s hand before is:")
                    print([str(tile) for tile in env.game.current_player.hidden_hand])
                    print("Discard pile is:")
                    print([str(tile) for tile in env.game.current_player.discard_pile])
                next_state, done = env.step_with_all_actions(selected_actions)

                env.game.is_discard = False
                for i in range(4):
                    if selected_actions[i][1] == 20:
                        continue
                    print(f"The tile {env.game.latest_tile} was discarded")  # TODO: discarding is not working
                    # properly always
                    print(f"Player {i}'s after hand is:")
                    print([str(tile) for tile in env.game.current_player.hidden_hand])
                    print("Discard pile is:")
                    print([str(tile) for tile in env.game.current_player.discard_pile])

                if env.game.last_acting_player is not None:
                    actioning_player_id = env.game.last_acting_player.player_id
                    episode_memory[actioning_player_id].append(
                        (state, selected_actions[actioning_player_id][1])
                    )

                state = next_state

                # ====================== ====================== ======================
                # ====================== NON-DISCARD PHASE ===========================
                # ====================== ====================== ======================
                legal_actions = [[], [], [], []]
                state = env.game.get_state()
                for i in range(len(players)):
                    player = players[i]
                    our_turn = env.game.current_player == player
                    legal_actions[i] = env.game.get_legal_actions(discard_turn=False, our_turn=our_turn, player=player)

                selected_actions = [(i, player.select_actions(legal_actions[i], state))
                                    for i, player in enumerate(players)]

                next_state, done = env.step_with_all_actions(selected_actions)
                env.game.is_discard = True

                print(f"Respond to discard")
                # print(selected_actions)
                if all(action[1] == 20 for action in selected_actions):
                    print("No response")
                else:
                    print(f"Player {env.game.last_acting_player.player_id} interrupted with {env.game.last_action}")

                if env.game.last_acting_player is not None:
                    actioning_player_id = env.game.last_acting_player.player_id
                    episode_memory[actioning_player_id].append(
                        (state, selected_actions[actioning_player_id][1])
                    )

                if env.game.game_over:  # If the game is over, break early
                    continue

                done = env.game.game_over
                turn_no += 1
                print(f"\nThere are {len(env.game.tiles)} remaining")

                # TODO: the number of tiles remaning doesn't seem to always go down
            print("Did the game conclude in a win? " + str(env.game.game_over))
            final_rewards = [
                players[i].score - prev_scores[i]
                for i in range(4)
            ]

            for i in range(4):
                for (s, a) in episode_memory[i]:
                    decision_model.push_experience((s, a, final_rewards[i]))

            decision_model.update_model()

            for i in range(4):
                total_rewards[i] += final_rewards[i]
