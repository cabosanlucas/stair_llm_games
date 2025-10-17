"""
Simple Games Framework - Event-Driven Repeated General-Sum Game Framework

A modular simulation framework for studying LLM and algorithmic behavior 
in repeated general-sum games (e.g., matrix games).

Key Components:
- GameState: Centralized state management
- Player: Abstract base for game agents (RandomPlayer, LLMPlayer, etc.)
- Game: Abstract base for game environments (MatrixGame, PrisonersDilemma, etc.)
- Moderator: Orchestrates game rounds
- Experiment: Runs repeated games and manages execution
- EventLogger: Structured event logging for analysis
"""

from .game_state import GameState
from .topics import Topic, Message
from .game import Game, MatrixGame, PrisonersDilemma, ChickenGame
from .player import Player, RandomPlayer, TitForTatPlayer, LLMPlayer, RegretMatchingPlayer
from .moderator import Moderator
from .experiment import Experiment
from .logger import EventLogger, AnalysisLogger

__version__ = "0.1.0"
__author__ = "Simple Games Framework"

__all__ = [
    # Core components
    "GameState",
    "Topic", 
    "Message",
    
    # Game environments
    "Game",
    "MatrixGame", 
    "PrisonersDilemma",
    "ChickenGame",
    
    # Players
    "Player",
    "RandomPlayer",
    "TitForTatPlayer", 
    "LLMPlayer",
    "RegretMatchingPlayer",
    
    # Orchestration
    "Moderator",
    "Experiment",
    
    # Logging
    "EventLogger",
    "AnalysisLogger"
]

