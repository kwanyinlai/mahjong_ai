class ActionSelectionStrategy:
    def select(self, action_probs, legal_actions):
        """
        Select an action based on a set of legal actions and action probabiltiies
        :param action_probs:
        :param legal_actions:
        """
        raise NotImplementedError
