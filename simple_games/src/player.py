"""
Player implementations for game agents.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
import random
import json
from .topics import Message, Topic
from .game_state import GameState


class Player(ABC):
    """Abstract base class for game players."""
    
    def __init__(self, name: str, num_actions: int):
        self.name = name
        self.num_actions = num_actions
        self.history = []  # list of (policy, reward)
        self.total_reward = 0.0
    
    @abstractmethod
    def handle_message(self, message: Message, state: GameState) -> Message:
        """
        Process incoming information and return a Message with the next policy.
        
        Args:
            message: Incoming message from moderator
            state: Current game state
            
        Returns:
            Message containing the player's policy
        """
        raise NotImplementedError
    
    def update_history(self, policy: List[float], reward: float):
        """Update player's history with new round results."""
        self.history.append((policy, reward))
        self.total_reward += reward
    
    def get_average_reward(self) -> float:
        """Get average reward across all rounds."""
        if not self.history:
            return 0.0
        return self.total_reward / len(self.history)
    
    def get_last_policy(self) -> List[float]:
        """Get the policy from the last round."""
        if not self.history:
            return [1.0 / self.num_actions] * self.num_actions
        return self.history[-1][0]
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name}, actions={self.num_actions})"


class RandomPlayer(Player):
    """Player that chooses actions uniformly at random."""
    
    def __init__(self, name: str, num_actions: int, seed: int = None):
        super().__init__(name, num_actions)
        if seed is not None:
            random.seed(seed)
    
    def handle_message(self, message: Message, state: GameState) -> Message:
        """Return a uniform random policy."""
        policy = [1.0 / self.num_actions] * self.num_actions
        
        return Message(
            sender=self.name,
            receiver="moderator",
            topic=Topic("policy"),
            content={"policy": policy, "player": self.name}
        )


class TitForTatPlayer(Player):
    """Tit-for-Tat strategy: start by cooperating, then copy opponent's last action."""
    
    def __init__(self, name: str, num_actions: int = 2, initial_action: int = 0):
        super().__init__(name, num_actions)
        self.initial_action = initial_action
        self.opponent_history = []
    
    def handle_message(self, message: Message, state: GameState) -> Message:
        """Implement Tit-for-Tat strategy."""
        # Extract opponent's last action from game state
        if state.round_history:
            last_round = state.round_history[-1]
            actions = last_round.get("actions", {})
            
            # Find opponent's action (assuming 2-player game)
            opponent_name = None
            for player_name in actions:
                if player_name != self.name:
                    opponent_name = player_name
                    break
            
            if opponent_name and opponent_name in actions:
                last_opponent_action = actions[opponent_name]
                self.opponent_history.append(last_opponent_action)
        
        # Determine next action
        if not self.opponent_history:
            # First round: use initial action
            next_action = self.initial_action
        else:
            # Copy opponent's last action
            next_action = self.opponent_history[-1]
        
        # Convert to policy (deterministic)
        policy = [0.0] * self.num_actions
        policy[next_action] = 1.0
        
        return Message(
            sender=self.name,
            receiver="moderator",
            topic=Topic("policy"),
            content={"policy": policy, "player": self.name}
        )

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
class LLMPlayer(Player):
    """Stub for LLM-based player that builds prompts and parses responses."""
    
    def __init__(self, name: str, num_actions: int, model_name: str = "gpt-4o-mini", use_cot: bool = True):
        super().__init__(name, num_actions)
        self.model_name = model_name
        self.llm = ChatOpenAI(model=model_name)
        self.prompts_sent = []
        self.use_cot = use_cot

        # Tool: select_policy (no chain_of_thought param)
        @tool
        def select_policy(policy: list) -> dict:
            """Select a pure strategy (one-hot) action from the available actions in the game. 
            Input should be a list of ints, e.g., [0, 1]."""
            return {"policy": policy}

        # Tool: select_policy_with_cot (with chain_of_thought param)
        @tool
        def select_policy_with_cot(chain_of_thought: str, policy: list) -> dict:
            """Provide a one-hot policy as a list of ints and a brief chain_of_thought. 
            Example: chain_of_thought="...reasoning...", policy=[0,1] """
            return {"chain_of_thought": chain_of_thought, "policy": policy}

        self.policy_tool = select_policy_with_cot if self.use_cot else select_policy
    
    def handle_message(self, message: Message, state: GameState) -> Message:
        """Build prompt for LLM and return a pure strategy policy, optionally with chain of thought."""
        prompt = self._build_prompt(message, state)
        self.prompts_sent.append(prompt)

        # Bind tools to the LLM
        llm_with_tools = self.llm.bind_tools([self.policy_tool])

        # Call LLM with function calling
        response = llm_with_tools.invoke([HumanMessage(content=prompt)])

        # Extract function call from response
        if response.tool_calls:
            function_call = response.tool_calls[0]
            # print(f"Function call for {self.name}: {function_call}")
            if function_call["name"] in ("select_policy", "select_policy_with_cot"):
                args = function_call["args"]
                policy_str = args["policy"]
                # Fix: handle case where policy_str is already a list/dict
                if isinstance(policy_str, str):
                    policy = json.loads(policy_str)
                else:
                    policy = policy_str
                cot = args.get("chain_of_thought", "")
            else:
                raise ValueError("Unexpected function call")
        else:
            raise ValueError("No function call in response")

        # Enforce one-hot (pure strategy) policy
        policy = self._validate_one_hot_policy(policy)

        content = {"policy": policy, "player": self.name}
        if self.use_cot:
            if not cot:
                cot = 'none/empty'
            content["chain_of_thought"] = cot

        return Message(
            sender=self.name,
            receiver="moderator",
            topic=Topic("policy"),
            content=content
        )

    def _validate_one_hot_policy(self, policy: list) -> list:
        """Ensure the policy is a valid one-hot vector of length num_actions."""
        if (
            isinstance(policy, list)
            and len(policy) == self.num_actions
            and sum(policy) == 1
            and all((p == 0 or p == 1) for p in policy)
        ):
            return policy
        # If not valid, default to uniform random pure strategy
        one_hot = [0] * self.num_actions
        idx = random.randint(0, self.num_actions - 1)
        one_hot[idx] = 1
        return one_hot
    
    def _build_prompt(self, message: Message, state: GameState) -> str:
        """Build a prompt for the LLM based on current game state."""
        prompt_parts = [
            f"You are playing a repeated game as player {self.name}.",
            f"You have {self.num_actions} actions available: {list(range(self.num_actions))}.",
            f"Current round: {state.current_round + 1} of {state.num_rounds}.",
        ]

        if self.history:
            prompt_parts.append(f"\nYour history of n_rounds: {len(self.history)}:")
            for i, (policy, reward) in enumerate(self.history):
                prompt_parts.append(f"  Round {i+1}: Policy {policy}, Reward {reward:.2f}")

        if state.round_history:
            prompt_parts.append("\nGame history:")
            for round_data in state.round_history[-3:]:  # Last 3 rounds
                actions = round_data.get("actions", {})
                rewards = round_data.get("rewards", {})
                prompt_parts.append(f"  Round {round_data.get('round', '?')}: Actions {actions}, Rewards {rewards}")

        if self.use_cot:
            prompt_parts.append(
                "\nPlease use the select_policy_with_cot function to provide your policy as a one-hot (pure strategy) vector and a brief chain_of_thought explaining your reasoning. The policy must be a one-hot list of length {num_actions}. Example: '{{\"policy\": [0, 1], \"chain_of_thought\": \"I think action 1 is best because...\"}}'".format(num_actions=self.num_actions)
            )
            prompt_parts.append("\nRespond ONLY with a valid JSON object with keys 'policy' and 'chain_of_thought'.")
        else:
            prompt_parts.append(
                "\nPlease use the select_policy function to provide your policy as a one-hot (pure strategy) vector. The policy must be a one-hot list of length {num_actions}. Example: '{{\"policy\": [0, 1]}}'".format(num_actions=self.num_actions)
            )
            prompt_parts.append("\nRespond ONLY with a valid JSON object with key 'policy'.")
        return "\n".join(prompt_parts)
    
    
    def _validate_policy(self, policy: List[float]) -> List[float]:
        """Validate and normalize a policy to ensure it's a proper probability distribution."""
        if len(policy) != self.num_actions:
            return [1.0 / self.num_actions] * self.num_actions
        
        # Ensure all values are non-negative
        policy = [max(0.0, p) for p in policy]
        
        # Normalize to sum to 1
        total = sum(policy)
        if total > 0:
            policy = [p / total for p in policy]
        else:
            # If all zeros, return uniform random
            policy = [1.0 / self.num_actions] * self.num_actions
        
        return policy


class RegretMatchingPlayer(Player):
    """Player using regret matching algorithm."""
    
    def __init__(self, name: str, num_actions: int, learning_rate: float = 1.0):
        super().__init__(name, num_actions)
        self.learning_rate = learning_rate
        self.regrets = [0.0] * num_actions
        self.strategy_sum = [0.0] * num_actions
    
    def handle_message(self, message: Message, state: GameState) -> Message:
        """Implement regret matching strategy."""
        # Calculate current strategy based on regrets
        strategy = self._get_strategy()
        
        # Update strategy sum for average strategy calculation
        for i in range(self.num_actions):
            self.strategy_sum[i] += strategy[i]
        
        return Message(
            sender=self.name,
            receiver="moderator",
            topic=Topic("policy"),
            content={"policy": strategy, "player": self.name}
        )
    
    def _get_strategy(self) -> List[float]:
        """Get current strategy based on regrets."""
        # Calculate positive regrets
        positive_regrets = [max(0, r) for r in self.regrets]
        total_positive = sum(positive_regrets)
        
        if total_positive > 0:
            # Use regret matching
            strategy = [r / total_positive for r in positive_regrets]
        else:
            # Uniform random if no positive regrets
            strategy = [1.0 / self.num_actions] * self.num_actions
        
        return strategy
    
    def update_regrets(self, action_taken: int, payoffs: List[float]):
        """Update regrets based on observed payoffs."""
        if len(payoffs) != self.num_actions:
            return
        
        # Calculate regret for each action
        for a in range(self.num_actions):
            regret = payoffs[a] - payoffs[action_taken]
            self.regrets[a] += regret * self.learning_rate
    
    def get_average_strategy(self) -> List[float]:
        """Get average strategy over all rounds."""
        total = sum(self.strategy_sum)
        if total > 0:
            return [s / total for s in self.strategy_sum]
        else:
            return [1.0 / self.num_actions] * self.num_actions

