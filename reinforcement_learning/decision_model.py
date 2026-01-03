from typing import List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
from collections import deque

from mahjong_environment.mahjong_actions import MahjongActions
from reinforcement_learning.montecarlo_sampling import MonteCarloTreeSearch
from reinforcement_learning.neural_network import PolicyValueNetwork


class MahjongModel:
    """
    Inject this to share action selection logic
    """

    def __init__(self, network: PolicyValueNetwork, learning_rate: float = 0.01, batch_size: int = 32,
                 max_buffer_size: int = 10000):
        """
        :param network: network with policy-value head
        :param learning_rate: learning rate for Adam optimizer
        :param batch_size: number of experiences sampled per update
        :param max_buffer_size: maximum size of replay buffer
        """
        self.network = network
        self.batch_size = batch_size
        self.replay_buffer = deque(maxlen=max_buffer_size)
        self.optimizer = optim.Adam(self.network.parameters(), lr=learning_rate)

    def select_action(self, observation: np.ndarray, legal_actions: List[int], player_id: int) -> MahjongActions:
        """

        :param observation: masked observation from public state (with hidden public information)
        :param legal_actions: set of legal actions that can be made (MahjongActions)
        :return: the integer corresponding to the MahjongActions enumerator
        """
        if legal_actions == [MahjongActions.PASS]:
            return MahjongActions.PASS  # only one legal action, so return it
        mcts = MonteCarloTreeSearch(
            player_id=player_id,
            network=self.network,
            num_simulations=100,
            c_puct=1.0
        )

        # must take unmasked observation
        best_action = mcts.search(
            root_state=observation,
            player_id=player_id
        )

        return MahjongActions(best_action[1])

        # TODO: mask observation for direct sampling
        # observation to tensor
        obs_tensor = torch.tensor(observation, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():  # no learning just selecting
            policy_logits, _ = self.network(obs_tensor)

        # Mask illegal actions
        policy = policy_logits.squeeze().cpu().numpy()
        policy[~np.isin(np.arange(len(policy)), legal_actions)] = -1e9  # for masking, reference
        # to softmax which should expect -1e9 as opposed to 0 for true masking to 0 == False

        # Sample from policy
        probs = torch.softmax(torch.tensor(policy), dim=0).numpy()  # probabilities
        return np.random.choice(len(probs), p=probs)  # select from probabilities

    def push_experience(self, experience: Tuple[np.ndarray, int, float]):
        """
        Store experience in the replay buffer
        """
        self.replay_buffer.append(experience)

    def sample_batch(self) -> List:
        """
        Sample a batch of experiences from the replay buffer
        """
        return random.sample(self.replay_buffer, min(len(self.replay_buffer), self.batch_size))

    def update_model(self):
        """
        Update the model using the experiences stored in the replay buffer if
        buffer is greater than initialised batch size
        """
        if len(self.replay_buffer) < self.batch_size:
            return

        batch = self.sample_batch()
        states, actions, values = zip(*batch)  # only store state, best action, final outcome

        # tensor = higher dimen matrix
        states = torch.tensor(np.array(states), dtype=torch.float32)

        actions = torch.tensor(actions, dtype=torch.long)

        values = torch.tensor(values, dtype=torch.float32)

        policy_logits, value_preds = self.network(states)

        # log softmax
        log_probs = torch.log_softmax(policy_logits, dim=1)
        # actual chosen
        chosen_log_probs = log_probs.gather(
            1, actions.unsqueeze(1)
        ).squeeze(1)
        # calculate advantage, i.e. delta prediction from actual result
        advantages = values - value_preds.squeeze().detach()
        # minmising loss, log of positive-negative advantge
        policy_loss = -(chosen_log_probs * advantages).mean()

        # MSE, delta(prediction - actual)^2
        value_loss = nn.MSELoss()(value_preds.squeeze(), values)

        weighting = 1.0  # TODO: determien weighting
        total_loss = policy_loss + weighting * value_loss

        # backpropagation
        self.optimizer.zero_grad()  # clear old gradients from prev training
        total_loss.backward()  # step through prev
        self.optimizer.step()  # weight update

    def reset(self):
        """
        Reset the replay buffer
        """
        self.replay_buffer.clear()
