"""
Abstract base class and implementations for game environments.
"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Any


class Game(ABC):
    """Abstract base class defining the payoff logic for the environment."""
    
    @abstractmethod
    def get_payoffs(self, actions: List[int]) -> Tuple[float, ...]:
        """Return rewards for each player given their chosen actions."""
        raise NotImplementedError
    
    @abstractmethod
    def get_num_actions(self) -> int:
        """Return the number of actions available to each player."""
        raise NotImplementedError
    
    @abstractmethod
    def get_num_players(self) -> int:
        """Return the number of players in this game."""
        raise NotImplementedError


class MatrixGame(Game):
    """
    A 2-player matrix game with specified payoff matrices.
    """
    
    def __init__(self, payoff_matrix_p1: List[List[float]], payoff_matrix_p2: List[List[float]]):
        """
        Initialize with payoff matrices for both players.
        
        Args:
            payoff_matrix_p1: 2D list where [i][j] is player 1's payoff for actions (i,j)
            payoff_matrix_p2: 2D list where [i][j] is player 2's payoff for actions (i,j)
        """
        self.R1 = payoff_matrix_p1
        self.R2 = payoff_matrix_p2
        
        # Validate matrices
        if len(self.R1) != len(self.R2):
            raise ValueError("Payoff matrices must have same number of rows")
        if len(self.R1[0]) != len(self.R2[0]):
            raise ValueError("Payoff matrices must have same number of columns")
        
        self.num_actions = len(self.R1)
        self.num_players = 2
    
    def get_payoffs(self, actions: List[int]) -> Tuple[float, float]:
        """Return (reward_player1, reward_player2) given the chosen actions."""
        if len(actions) != 2:
            raise ValueError("MatrixGame requires exactly 2 actions")
        
        a1, a2 = actions[0], actions[1]
        
        if a1 >= len(self.R1) or a2 >= len(self.R1[0]):
            raise ValueError(f"Action indices out of bounds: ({a1}, {a2})")
        
        return self.R1[a1][a2], self.R2[a1][a2]
    
    def get_num_actions(self) -> int:
        """Return the number of actions available to each player."""
        return self.num_actions
    
    def get_num_players(self) -> int:
        """Return the number of players in this game."""
        return self.num_players
    
    def get_payoff_matrix(self, player: int) -> List[List[float]]:
        """Get the payoff matrix for a specific player."""
        if player == 0:
            return self.R1
        elif player == 1:
            return self.R2
        else:
            raise ValueError(f"Invalid player index: {player}")
    
    def __repr__(self) -> str:
        return f"MatrixGame({self.num_actions}x{self.num_actions})"


class PrisonersDilemma(MatrixGame):
    """Classic Prisoner's Dilemma game."""
    
    def __init__(self, T: float = 5.0, R: float = 3.0, P: float = 1.0, S: float = 0.0):
        """
        Initialize Prisoner's Dilemma with standard parameters.
        
        Args:
            T: Temptation (defect while other cooperates)
            R: Reward (both cooperate)
            P: Punishment (both defect)
            S: Sucker's payoff (cooperate while other defects)
        """
        # Actions: 0 = Cooperate, 1 = Defect
        payoff_matrix_p1 = [[R, S], [T, P]]
        payoff_matrix_p2 = [[R, T], [S, P]]
        super().__init__(payoff_matrix_p1, payoff_matrix_p2)
        self.T, self.R, self.P, self.S = T, R, P, S
    
    def __repr__(self) -> str:
        return f"PrisonersDilemma(T={self.T}, R={self.R}, P={self.P}, S={self.S})"


class ChickenGame(MatrixGame):
    """Chicken game (also known as Hawk-Dove)."""
    
    def __init__(self, V: float = 2.0, C: float = 1.0):
        """
        Initialize Chicken game.
        
        Args:
            V: Value of winning
            C: Cost of conflict
        """
        # Actions: 0 = Swerve, 1 = Straight
        payoff_matrix_p1 = [[V/2, V], [V-C, 0]]
        payoff_matrix_p2 = [[V/2, V-C], [V, 0]]
        super().__init__(payoff_matrix_p1, payoff_matrix_p2)
        self.V, self.C = V, C
    
    def __repr__(self) -> str:
        return f"ChickenGame(V={self.V}, C={self.C})"


class Custom4PGame(MatrixGame):
    """Custom game."""
    
    def __init__(self):
        payoff_matrix_p1 = [[5, 0, 1, 1],
                            [0, 5, 1, 1],
                            [1, 1, 2, 0],
                            [1, 1, 0, 2]]
        payoff_matrix_p2 = [[5, 0, 1, 1],
                            [0, 5, 1, 1],
                            [1, 1, 0, 2],
                            [1, 1, 2, 0]]
        super().__init__(payoff_matrix_p1, payoff_matrix_p2)
        self.num_actions = len(payoff_matrix_p1)
        self.num_players = 2
    
    def __repr__(self) -> str:
        return f"CustomGame({self.num_actions}x{self.num_actions})"