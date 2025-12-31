from typing import List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
from collections import deque


class MahjongModel:
    """
    Inject this to share action selection logic
    """

    def __init__(self, network: nn.Module, learning_rate: float = 0.01, batch_size: int = 32,
                 max_buffer_size: int = 10000):
        """
        MahjongModel handles updating of the model
        """
        self.network = network
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.replay_buffer = deque(maxlen=max_buffer_size)
        self.optimizer = optim.Adam(self.network.parameters(), lr=learning_rate)

    def store_experience(self, experience: Tuple[np.ndarray, int, float, np.ndarray, bool]):
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
        Update the model using the experiences stored in the replay buffer.
        """
        if len(self.replay_buffer) < self.batch_size:
            return

        batch = self.sample_batch()
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.tensor(np.array(states), dtype=torch.float32)
        actions = torch.tensor(actions, dtype=torch.long)
        rewards = torch.tensor(rewards, dtype=torch.float32)
        next_states = torch.tensor(np.array(next_states), dtype=torch.float32)
        dones = torch.tensor(dones, dtype=torch.float32)

        # Get predictions from the neural network
        policy_preds, value_preds = self.network(states)

        # LOSS FUNCTION:
        # for the policy-based, since this is a classificaiton class of probabilities
        # we will use cross-entropy loss
        # for the value-based, we can use MSE
        policy_loss = nn.CrossEntropyLoss()(policy_preds, actions)
        value_loss = nn.MSELoss()(value_preds.squeeze(), rewards)

        # TODO: perhaps weight this
        total_loss = policy_loss + value_loss

        # Perform backpropagation and optimization
        self.optimizer.zero_grad()
        total_loss.backward()
        self.optimizer.step()

    def reset(self):
        """
        reset replay buffer
        """
        self.replay_buffer.clear()
