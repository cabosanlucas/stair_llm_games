"""
Experiment class for running repeated games and managing execution.
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime

from .moderator import Moderator
from .game_state import GameState
from .logger import EventLogger


class Experiment:
    """Wraps repeated execution and final export of logs."""
    
    def __init__(self, moderator: Moderator, state: GameState, logger: Optional[EventLogger] = None):
        self.moderator = moderator
        self.state = state
        self.logger = logger
        self.start_time = None
        self.end_time = None
        self.metadata = {}
    
    def run(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Run the complete experiment.
        
        Args:
            verbose: If True, print progress information
            
        Returns:
            Dictionary with experiment results and statistics
        """
        self.start_time = time.time()
        self.state.record_event("experiment_start", {
            "timestamp": datetime.now().isoformat(),
            "num_rounds": self.state.num_rounds,
            "players": self.state.players,
            "sequential": self.state.sequential
        })
        
        if verbose:
            print(f"Starting experiment with {len(self.state.players)} players for {self.state.num_rounds} rounds")
            print(f"Players: {', '.join(self.state.players)}")
            print(f"Sequential play: {self.state.sequential}")
            print("-" * 50)
        
        # Run all rounds
        for round_num in range(1, self.state.num_rounds + 1):
            if verbose:
                print(f"Round {round_num}/{self.state.num_rounds}")
            
            self.moderator.play_round()
            
            if verbose and round_num % 10 == 0:
                # Print periodic stats
                stats = self.moderator.get_player_stats()
                print(f"  Round {round_num} stats:")
                for player_name, player_stats in stats.items():
                    print(f"    {player_name}: avg_reward={player_stats['average_reward']:.3f}")
        
        # Mark experiment as finished
        self.end_time = time.time()
        self.state.status = "finished"
        self.state.record_event("experiment_complete", {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": self.end_time - self.start_time,
            "total_rounds": self.state.current_round
        })
        
        # Export logs if logger is provided
        if self.logger:
            self.logger.dump(self.state)
        
        if verbose:
            print("-" * 50)
            print("Experiment completed!")
            print(f"Duration: {self.end_time - self.start_time:.2f} seconds")
            
            # Print final statistics
            final_stats = self.moderator.get_player_stats()
            print("\nFinal Statistics:")
            for player_name, stats in final_stats.items():
                print(f"  {player_name}:")
                print(f"    Total reward: {stats['total_reward']:.3f}")
                print(f"    Average reward: {stats['average_reward']:.3f}")
                print(f"    Rounds played: {stats['num_rounds']}")
        
        return self._get_results()
    
    def _get_results(self) -> Dict[str, Any]:
        """Get comprehensive results from the experiment."""
        duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        results = {
            "experiment_metadata": {
                "duration_seconds": duration,
                "num_rounds": self.state.num_rounds,
                "players": self.state.players,
                "sequential": self.state.sequential,
                "start_time": self.start_time,
                "end_time": self.end_time
            },
            "game_state": {
                "current_round": self.state.current_round,
                "status": self.state.status,
                "num_events": len(self.state.event_log)
            },
            "player_statistics": self.moderator.get_player_stats(),
            "round_history": self.state.round_history,
            "event_log": self.state.event_log
        }
        
        return results
    
    def get_summary(self) -> str:
        """Get a text summary of the experiment results."""
        if not self.state.is_finished():
            return "Experiment not yet completed."
        
        stats = self.moderator.get_player_stats()
        duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        summary_lines = [
            f"Experiment Summary",
            f"==================",
            f"Duration: {duration:.2f} seconds",
            f"Rounds: {self.state.current_round}/{self.state.num_rounds}",
            f"Players: {', '.join(self.state.players)}",
            f"Sequential: {self.state.sequential}",
            "",
            "Final Results:"
        ]
        
        for player_name, player_stats in stats.items():
            summary_lines.append(f"  {player_name}:")
            summary_lines.append(f"    Total Reward: {player_stats['total_reward']:.3f}")
            summary_lines.append(f"    Average Reward: {player_stats['average_reward']:.3f}")
            summary_lines.append(f"    Rounds: {player_stats['num_rounds']}")
        
        return "\n".join(summary_lines)
    
    def save_results(self, filepath: str, format: str = "json"):
        """Save experiment results to a file."""
        import json
        
        results = self._get_results()
        
        if format.lower() == "json":
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        elif format.lower() == "txt":
            with open(filepath, 'w') as f:
                f.write(self.get_summary())
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def __repr__(self) -> str:
        return f"Experiment(moderator={self.moderator}, state={self.state}, logger={self.logger})"

