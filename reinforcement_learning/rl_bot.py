import numpy as np
from mahjong_environment.player import Player


class RLAgent(Player):
    """
    Wrapper class for a decision model adapted for Players
    """

    def __init__(self,
                 mahjong_model,
                 player_id=0,
                 player_order=0):
        super().__init__(player_id, player_order)
        self.decision_model = mahjong_model

    def select_actions(self, legal_actions, observation: np.ndarray):
        """
        Select an action
        :param observation:
        :return:
        """
        return self.decision_model.select_action(observation, legal_actions)

    def push_experience(self, experience):
        """
        Store this experience into the replay buffer
        :param experience:
        """
        self.decision_model.push_experience(experience)

    def update_model(self) -> None:
        """
        Update the model using the replay buffer if replay buffer is of
        sufficient size
        :return:
        """
        self.decision_model.update_model()
