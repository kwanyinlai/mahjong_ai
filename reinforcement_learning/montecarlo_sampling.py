from __future__ import annotations

import math
from typing import Dict, Optional, Tuple
import numpy as np
import torch

from mahjong_environment.mahjong_actions import MahjongActions
from mahjong_environment.mahjong_game import MahjongGame
from mahjong_environment.mahjong_game_adapter import MahjongEnvironmentAdapter
from reinforcement_learning.neural_network import PolicyValueNetwork


class MonteCarloTreeNode:
    """
    Tree node in Monte-Carlo Search Tree
    """
    state: np.ndarray
    transition: Tuple[int, MahjongActions]
    parent: MonteCarloTreeNode = None
    children: Dict[Tuple[int, MahjongActions], MonteCarloTreeNode]
    visits: int
    value_sum: float
    prior: float

    def __init__(self, state: np.ndarray,
                 transition: Optional[Tuple[int, MahjongActions]] = None,
                 parent: Optional[MonteCarloTreeNode] = None):
        self.state = state
        self.transition = transition
        self.parent = parent
        self.children = {}
        self.visits = 0
        self.value_sum = 0.0
        self.prior = 0.0  # using PUCT (predictor + upper confidence bound)

    @property
    def value(self) -> float:
        return self.value_sum / self.visits if self.visits > 0 else 0.0


class MonteCarloTreeSearch:
    """
    Monte Carlo Tree Search using policy value network
    """

    def __init__(self,
                 player_id: int,
                 network: PolicyValueNetwork,
                 num_simulations=50,
                 c_puct=1.0,
                 rollout_depth=5,
                 num_actions_to_consider=5,
                 num_determinisations=10
                 ):
        self.network = network
        self.num_simulations = num_simulations
        self.c_puct = c_puct
        self.rollout_depth = rollout_depth
        self.num_actions_to_consider = num_actions_to_consider
        self.player_id = player_id
        self.num_determinisations = num_determinisations

    def search(self, root_state: np.ndarray, player_id: int) -> tuple[int, MahjongActions]:
        transition_visits = {}
        transition_values = {}
        # root = MonteCarloTreeNode(root_state)
        # self.expand_node(root)
        #
        # for _ in range(self.num_simulations):
        #     node = root
        #     path = [node]
        #
        #     # select
        #     while node.children:
        #         node = self.select_child(node)
        #         path.append(node)
        #
        #     # expand
        #     if not node.children and node.visits > 0:
        #         self.expand_node(node)
        #
        #     value = self.rollout(node.state, player_id, depth=self.rollout_depth)
        #
        #     # backpropagation
        #     for n in reversed(path):
        #         n.visits += 1
        #         n.value_sum += value
        #
        # # most visited
        # best_action = max(root.children.items(), key=lambda x: x[1].visits)[0]
        # return best_action
        for _ in range(self.num_determinisations):
            # sample possible world (currently just grabs the same state) TODO: build determinise_state func
            determinised_state = self.determinise_state(root_state, player_id)

            # MCTS
            root = MonteCarloTreeNode(determinised_state)
            self.expand_node(root, player_id)

            # sims_per_determinisation = max(1, self.num_simulations // self.num_determinisations)
            sims_per_determinisation = 1  # for debugging only TODO: delete when done

            for _ in range(sims_per_determinisation):
                node = root
                path = [node]

                # select children
                while node.children:
                    node = self.select_child(node)
                    path.append(node)

                # expand
                if not node.children and node.visits > 0:
                    self.expand_node(node, player_id)

                # rollout to end of game or up to max depth
                value = self.rollout(node.state, player_id, depth=self.rollout_depth)

                # backpropagation
                for n in reversed(path):
                    n.visits += 1
                    n.value_sum += value

            # aggregate across determinisations (just one for now) TODO:
            for transition, child in root.children.items():
                if transition not in transition_visits:
                    transition_visits[transition] = 0
                    transition_values[transition] = 0.0
                transition_visits[transition] += child.visits
                transition_values[transition] += child.value_sum

        # filter out to only actions for our player
        filtered_transition_visits = {
            transition: visits
            for transition, visits in transition_visits.items()
            if transition[0] == player_id
        }
        # if no actions just pass
        if filtered_transition_visits == {}:
            return (player_id, MahjongActions.PASS)
        else:
            # select the best
            best_transition = max(filtered_transition_visits.items(), key=lambda x: x[1])[0]
            return best_transition

    def select_child(self, node: MonteCarloTreeNode) -> MonteCarloTreeNode:
        """
        using PUCT
        """
        total_visits = sum(child.visits for child in node.children.values())
        best_score = -float("inf")
        best_child = None

        for transition, child in node.children.items():
            q = child.value
            u = self.c_puct * child.prior * math.sqrt(total_visits + 1) / (1 + child.visits)
            score = q + u
            if score > best_score:
                best_score = score
                best_child = child

        return best_child

    def expand_node(self, node: MonteCarloTreeNode, player_id: int):
        """
        expand node
        """
        game, is_discard = MahjongGame.reconstruct_game(node.state)
        legal_transitions = game.find_legal_transitions()

        # Get policy from network using observable state
        obs = self.hide_hidden_information(node.state, player_id)
        obs_tensor = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            policy_logits, _ = self.network(obs_tensor)
        policy = policy_logits.squeeze().cpu().numpy()

        for transition in legal_transitions:
            next_state = self.simulate_transition(node.state, transition)
            child_node = MonteCarloTreeNode(
                state=next_state,
                transition=transition,
                parent=node
            )
            # Map transition to policy index
            # Assuming transition is (player_id, action_index)
            actioner_id, action_idx = transition
            child_node.prior = policy[action_idx] if action_idx < len(policy) else 1e-6
            node.children[transition] = child_node

    def simulate_transition(self, state: np.ndarray, transition: Tuple[int, int]) -> np.ndarray:
        """
        Aapply action to state and return new state
        """
        game, is_discard = MahjongGame.reconstruct_game(state)
        adapter = MahjongEnvironmentAdapter(game=game, discard_turn=is_discard, controlling_player_id=self.player_id)
        actioner_id, action = transition
        adapter.step_with_resolved_action(action=action, actioner_id=actioner_id)
        return adapter.game.get_state()

    def rollout(self, current_state: np.ndarray, player_id: int, depth: int) -> float:
        """
        Guided rollout using policy
        """
        for _ in range(depth):
            assert all(element <= 1 for element in current_state)
            game, is_discard = MahjongGame.reconstruct_game(current_state)
            legal_transitions = game.find_legal_transitions()

            if not legal_transitions:
                break

            # policy from network
            obs = self.hide_hidden_information(current_state, player_id)
            obs_tensor = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)

            with torch.no_grad():
                policy_logits, value_tensor = self.network(obs_tensor)
            policy = policy_logits.squeeze().cpu().numpy()

            # mask illegal transition prevent selection
            self.mask_illegal_transitions(policy, legal_transitions)

            # convert?
            policy_exp = np.exp(policy - np.max(policy))
            probs = policy_exp / policy_exp.sum()

            # select top-k transitions for stochastic rollout
            top_k = min(self.num_actions_to_consider, len(legal_transitions))

            # obtain action indices (removing player_id) and get the probability
            legal_action_indices = [transition[1] for transition in legal_transitions]
            legal_probs = probs[legal_action_indices]

            if legal_probs.sum() == 0:
                # uniform distribution over legal actions if all zero
                legal_probs = np.ones(len(legal_action_indices)) / len(legal_action_indices)
            else:
                legal_probs = legal_probs / legal_probs.sum()
            # fetch our top k
            top_indices = np.argsort(legal_probs)[-top_k:]
            top_probs = legal_probs[top_indices]
            top_probs = top_probs / top_probs.sum()

            # sample from top k rather than picking top
            selected_idx = np.random.choice(top_indices, p=top_probs)
            selected_transition = legal_transitions[selected_idx]

            # simulate
            current_state = self.simulate_transition(current_state, selected_transition)

        # evaluate using value network
        obs = self.hide_hidden_information(current_state, player_id)
        obs_tensor = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            _, value_tensor = self.network(obs_tensor)
        value = value_tensor.squeeze().cpu().item()

        return value

    @staticmethod
    def hide_hidden_information(state, player_id):
        return state.copy()  # can add masking later based on player_id

    @staticmethod
    def mask_illegal_actions(policy, legal_actions):
        mask = np.zeros_like(policy)
        mask[legal_actions] = 1.0
        policy *= mask
        if policy.sum() > 0:
            policy /= policy.sum()
        else:
            policy[legal_actions] = 1.0 / len(legal_actions)

    def determinise_state(self, state: np.ndarray, player_id: int) -> np.ndarray:
        """
        Generate a random possible state for our game
        """
        # TODO: implement determinisations
        # visible_tiles = self.get_visible_tiles(state, player_id)
        # unknown_tiles = np.ndarray() - visible_tiles  # TODO: bug with get_visible_tiles()

        # self.shuffle_hidden_state(state, unknown_tiles, player_id)

        return state.copy()

    @staticmethod
    def get_visible_tiles(state: np.ndarray, player_id: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Return tuple of visible tiles + claimed flowers
        :param state:
        :param player_id:
        :return:
        """
        self_visible_tiles = state[player_id * 217 + 34 * 0: player_id * 217 + 34 * 1]
        self_visible_tiles += state[player_id * 217 + 34 * 1: player_id * 217 + 34 * 2]
        self_visible_tiles += state[player_id * 217 + 34 * 2: player_id * 217 + 34 * 3]
        self_visible_tiles += state[player_id * 217 + 34 * 3: player_id * 217 + 34 * 4]
        self_visible_tiles += state[player_id * 217 + 34 * 4: player_id * 217 + 34 * 5]
        self_visible_tiles += state[player_id * 217 + 34 * 5: player_id * 217 + 34 * 6]
        # add all of our own tiles to visible set
        flowers = state[player_id * 217 + 34 * 6: player_id * 217 + 34 * 6 + 8]
        for i in range(4):
            if i == player_id:
                continue
            else:
                self_visible_tiles += state[i * 217 + 34 * 1: player_id * 217 + 34 * 2]  # first revealed set
                self_visible_tiles += state[i * 217 + 34 * 2: player_id * 217 + 34 * 3]  # first revealed set
                self_visible_tiles += state[i * 217 + 34 * 3: player_id * 217 + 34 * 4]  # first revealed set
                self_visible_tiles += state[i * 217 + 34 * 4: player_id * 217 + 34 * 5]  # first revealed set
                self_visible_tiles += state[i * 217 + 34 * 5: player_id * 217 + 34 * 6]  # discarded pile
                flowers += state[i * 217 + 34 * 6: i * 217 + 34 * 6 + 8]  # add flowers

        return self_visible_tiles, flowers

    @staticmethod
    def shuffle_hidden_state(state: np.ndarray, unknown_tiles: np.ndarray, player_id: int):
        """
        Inplace shuffle
        :param state:
        :param visible_tiles:
        :param player_id:
        :return:
        """
        # IMPORTANT, we need to maintain the sum of the hidden hand the same
        for i in range(4):
            if i == player_id:
                continue
            else:
                hidden_tile_sum = sum(state[i * 217: i * 217 + 34])
                #  TODO: randomise somehow


    @staticmethod
    def mask_illegal_transitions(policy: np.ndarray, legal_transitions: list) -> None:
        """
        Mask out illegal transitions in the policy
        """
        mask = np.zeros_like(policy)

        # set legal transitions to 1
        for actioner, action in legal_transitions:
            if action < len(policy):
                mask[action] = 1.0
        policy *= mask

        # renormalise
        if policy.sum() > 0:
            policy /= policy.sum()
        else:
            # Uniform distribution over legal transitions if all are zero
            for actioner, action in legal_transitions:
                if action < len(policy):
                    policy[action] = 1.0 / len(legal_transitions)
