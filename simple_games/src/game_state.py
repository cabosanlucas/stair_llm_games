"""
Centralized game state management for repeated general-sum games.
"""

from typing import List, Dict, Any, Optional


class GameState:
    """
    A centralized container that tracks the current state, history, and event log across rounds.
    """
    
    def __init__(self, num_rounds: int, player_names: List[str], sequential: bool = False):
        self.current_round = 0
        self.num_rounds = num_rounds
        self.players = player_names
        self.sequential = sequential
        self.round_history = []   # list of per-round dictionaries
        self.event_log = []       # list of structured events
        self.status = "initialized"  # ["initialized", "running", "finished"]
        
    def update(self, **kwargs):
        """Update arbitrary state variables (e.g., round counters, scores)."""
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def record_event(self, event_type: str, details: Dict[str, Any]):
        """Log structured game events for audit and analysis. Supports chain of thought logging."""
        event = {
            "round": self.current_round,
            "event": event_type,
            "details": details,
            "status": self.status,
        }
        # If chain_of_thought is present in details, also log it at top level for easier access
        if isinstance(details, dict) and "chain_of_thought" in details:
            event["chain_of_thought"] = details["chain_of_thought"]
        self.event_log.append(event)
    
    def get_round_history(self, round_num: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get history for a specific round or all rounds."""
        if round_num is not None:
            return [h for h in self.round_history if h.get("round") == round_num]
        return self.round_history
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get all events of a specific type."""
        return [e for e in self.event_log if e.get("event") == event_type]
    
    def is_finished(self) -> bool:
        """Check if the game has finished all rounds."""
        return self.current_round >= self.num_rounds
    
    def __repr__(self) -> str:
        return f"GameState(round={self.current_round}/{self.num_rounds}, status={self.status}, players={self.players})"

