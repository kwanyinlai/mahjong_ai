import torch
from torch import nn


class PolicyValueNetwork(nn.Module):

    # notes to self about neural networks:
    # we pass the input through each 'layer' of the function
    # this is represented by nn.Sequential

    # Linear() is a weighted average Wx + b (W is the weight matrix, b is the bias)
    # some Linear function F: R^{state_sze} -> R^{number_of_nodes}

    # ReLU() is a 'rectified linear unit'
    # i.e. F(x) = max(0,x) to remove negative values

    # first layer ompresses output, then we have 3 hidden layers

    def __init__(self, state_size: int, action_space: int, hidden_layer_size: int = 128):
        # POLICY NEURAL NETWORK
        super(PolicyValueNetwork, self).__init__()

        self.policy_input_layer = nn.Linear(state_size, hidden_layer_size)
        self.policy_output_layer = nn.Linear(hidden_layer_size, action_space)
        # mapping the state to action probabilities

        # TODO: We can define more layers later
        # VALUE NEURAL NETWORK
        self.value_input_layer = nn.Linear(state_size, hidden_layer_size)
        self.value_output_layer = nn.Linear(hidden_layer_size, 1)
        # mapping the state to a singel value evaluation

    def forward(self, state):
        """

        :param state:
        :return:
        """
        # defining policy value heads
        policy_out = torch.relu(self.policy_input_layer(state))
        policy_out = self.policy_output_layer(policy_out)

        value_out = torch.relu(self.value_input_layer(state))
        value_out = self.value_output_layer(value_out)

        return policy_out, value_out
