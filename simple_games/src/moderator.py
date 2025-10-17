"""
Moderator class for orchestrating game rounds.
"""

import random
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from .game import Game
from .player import Player
from .game_state import GameState
from .topics import Message, Topic


class Moderator:
    """The orchestrator for each round of play."""
    
    def __init__(self, game: Game, players: List[Player], state: GameState, seed: int = None):
        self.game = game
        self.players = {p.name: p for p in players}
        self.state = state
        
        if seed is not None:
            random.seed(seed)
        
        # Validate setup
        if len(players) != game.get_num_players():
            raise ValueError(f"Number of players ({len(players)}) doesn't match game ({game.get_num_players()})")
        
        for player in players:
            if player.num_actions != game.get_num_actions():
                raise ValueError(f"Player {player.name} has {player.num_actions} actions, but game requires {game.get_num_actions()}")
    
    def play_round(self):
        """Execute one round of the game."""
        self.state.current_round += 1
        self.state.status = "running"
        self.state.record_event("round_start", {"round": self.state.current_round})

        # Step 1: Prepare private messages for each player
        messages = self._prepare_messages()

        # Step 2: Collect policies and chain of thought from each player
        policy_messages, chains_of_thought = self._collect_policies_with_cot(messages)

        # Step 3: Sample actions from policies
        actions = self._sample_actions(policy_messages)

        # Step 4: Compute payoffs
        rewards = self._compute_payoffs(actions)

        # Step 5: Update player histories
        self._update_histories(policy_messages, rewards)

        # Step 6: Record results, including chain of thought
        self._record_round_results(actions, rewards, policy_messages, chains_of_thought)

        # Step 7: Update regrets for regret-based players
        self._update_regrets(actions, rewards)
    
    def _prepare_messages(self) -> List[Message]:
        """Prepare private messages for each player with their history."""
        messages = []
        
        for player_name, player in self.players.items():
            message = Message(
                sender="moderator",
                receiver=player_name,
                topic=Topic(f"private:{player_name}"),
                content={
                    "history": player.history,
                    "round": self.state.current_round,
                    "total_rounds": self.state.num_rounds,
                    "game_info": {
                        "num_actions": self.game.get_num_actions(),
                        "num_players": self.game.get_num_players(),
                        "sequential": self.state.sequential
                    }
                }
            )
            messages.append(message)
        
        return messages
    
    def _collect_policies_with_cot(self, messages: List[Message]) -> Tuple[List[Message], Dict[str, str]]:
        """Collect policy responses and chain of thought from all players."""
        policy_messages = []
        chains_of_thought = {}

        if self.state.sequential:
            # Sequential play: query players one by one
            for message in messages:
                player = self.players[message.receiver]
                policy_msg = player.handle_message(message, self.state)
                policy_messages.append(policy_msg)
                cot = policy_msg.content.get("chain_of_thought", "")
                chains_of_thought[player.name] = cot
                # Record policy selection event with chain of thought
                self.state.record_event("policy_selected", {
                    "player": player.name,
                    "policy": policy_msg.content["policy"],
                    "chain_of_thought": cot,
                    "sequential": True
                })
        else:
            # Simultaneous play: query all players at once
            for message in messages:
                player = self.players[message.receiver]
                policy_msg = player.handle_message(message, self.state)
                policy_messages.append(policy_msg)
                cot = policy_msg.content.get("chain_of_thought", "")
                chains_of_thought[player.name] = cot
            # Record all policy selections with chain of thought
            for policy_msg in policy_messages:
                self.state.record_event("policy_selected", {
                    "player": policy_msg.sender,
                    "policy": policy_msg.content["policy"],
                    "chain_of_thought": policy_msg.content.get("chain_of_thought", ""),
                    "sequential": False
                })
        return policy_messages, chains_of_thought
    
    def _sample_actions(self, policy_messages: List[Message]) -> Dict[str, int]:
        """Sample actions from the collected policies."""
        actions = {}
        
        for policy_msg in policy_messages:
            player_name = policy_msg.sender
            policy = policy_msg.content["policy"]
            
            # Validate policy
            if len(policy) != self.game.get_num_actions():
                raise ValueError(f"Policy length {len(policy)} doesn't match game actions {self.game.get_num_actions()}")
            
            # Normalize policy (handle floating point errors)
            total = sum(policy)
            if total > 0:
                policy = [p / total for p in policy]
            else:
                policy = [1.0 / len(policy)] * len(policy)
            
            # Sample action
            action = self._sample_from_policy(policy)
            actions[player_name] = action
            
            self.state.record_event("action_sampled", {
                "player": player_name,
                "policy": policy,
                "action": action
            })
        
        return actions
    
    def _sample_from_policy(self, policy: List[float]) -> int:
        """Sample an action from a probability distribution."""
        return random.choices(range(len(policy)), weights=policy)[0]
    
    def _compute_payoffs(self, actions: Dict[str, int]) -> Dict[str, float]:
        """Compute payoffs for all players based on their actions."""
        # Convert actions to list in player order
        action_list = [actions[player_name] for player_name in self.state.players]
        
        # Get payoffs from game
        payoffs = self.game.get_payoffs(action_list)
        
        # Convert to dictionary
        rewards = {}
        for i, player_name in enumerate(self.state.players):
            rewards[player_name] = payoffs[i]
        
        # Record payoff computation
        self.state.record_event("payoffs_computed", {
            "actions": actions,
            "rewards": rewards
        })
        
        return rewards
    
    def _update_histories(self, policy_messages: List[Message], rewards: Dict[str, float]):
        """Update each player's history with their policy and reward."""
        for policy_msg in policy_messages:
            player_name = policy_msg.sender
            player = self.players[player_name]
            policy = policy_msg.content["policy"]
            reward = rewards[player_name]
            
            player.update_history(policy, reward)
    
    def _record_round_results(self, actions: Dict[str, int], rewards: Dict[str, float], 
                            policy_messages: List[Message], chains_of_thought: Dict[str, str]):
        """Record the complete results of the round, including chain of thought."""
        # Store policies and chain of thought for this round
        policies = {msg.sender: msg.content["policy"] for msg in policy_messages}
        cots = {msg.sender: msg.content.get("chain_of_thought", "") for msg in policy_messages}

        round_data = {
            "round": self.state.current_round,
            "actions": actions,
            "rewards": rewards,
            "policies": policies,
            "chain_of_thought": cots
        }

        self.state.round_history.append(round_data)

        self.state.record_event("round_end", round_data)
    
    def _update_regrets(self, actions: Dict[str, int], rewards: Dict[str, float]):
        """Update regrets for players that use regret-based algorithms."""
        # This is a simplified version - in practice, you'd need to compute
        # counterfactual payoffs for each action
        for player_name, player in self.players.items():
            if hasattr(player, 'update_regrets'):
                action_taken = actions[player_name]
                # For now, just pass the actual reward (would need counterfactuals for full regret)
                player.update_regrets(action_taken, [rewards[player_name]] * player.num_actions)
    
    def get_player_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all players."""
        stats = {}
        
        for player_name, player in self.players.items():
            stats[player_name] = {
                "total_reward": player.total_reward,
                "average_reward": player.get_average_reward(),
                "num_rounds": len(player.history),
                "last_policy": player.get_last_policy()
            }
            
            # Add strategy-specific stats
            if hasattr(player, 'get_average_strategy'):
                stats[player_name]["average_strategy"] = player.get_average_strategy()
            if hasattr(player, 'regrets'):
                stats[player_name]["regrets"] = player.regrets
        
        return stats
    
    def __repr__(self) -> str:
        return f"Moderator(game={self.game}, players={list(self.players.keys())}, state={self.state})"

