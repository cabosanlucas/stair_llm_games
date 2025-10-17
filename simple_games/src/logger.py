"""
Event logging system for game experiments.
"""

import json
import csv
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from .game_state import GameState


class EventLogger:
    """Persists structured event logs for later analysis."""
    
    def __init__(self, filepath: Optional[str] = None, format: str = "json"):
        """
        Initialize logger.
        
        Args:
            filepath: Path to save logs (if None, prints to stdout)
            format: Output format ("json", "csv", or "txt")
        """
        self.filepath = filepath
        self.format = format.lower()
        
        if self.format not in ["json", "csv", "txt"]:
            raise ValueError(f"Unsupported format: {format}")
    
    def dump(self, state: GameState):
        """Export the complete event log."""
        if self.filepath:
            self._save_to_file(state)
        else:
            self._print_to_stdout(state)
    
    def _save_to_file(self, state: GameState):
        """Save logs to file in specified format."""
        if self.format == "json":
            self._save_json(state)
        elif self.format == "csv":
            self._save_csv(state)
        elif self.format == "txt":
            self._save_txt(state)
    
    def _save_json(self, state: GameState):
        """Save logs as JSON file."""
        log_data = {
            "experiment_info": {
                "num_rounds": state.num_rounds,
                "players": state.players,
                "sequential": state.sequential,
                "timestamp": datetime.now().isoformat()
            },
            "event_log": state.event_log,
            "round_history": state.round_history
        }
        
        with open(self.filepath, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
    
    def _save_csv(self, state: GameState):
        """Save logs as CSV file."""
        with open(self.filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(["round", "event", "details", "status"])
            
            # Write events
            for event in state.event_log:
                writer.writerow([
                    event.get("round", ""),
                    event.get("event", ""),
                    json.dumps(event.get("details", {})),
                    event.get("status", "")
                ])
    
    def _save_txt(self, state: GameState):
        """Save logs as human-readable text file."""
        with open(self.filepath, 'w') as f:
            f.write("Game Experiment Log\n")
            f.write("==================\n\n")
            
            f.write(f"Experiment Info:\n")
            f.write(f"  Rounds: {state.num_rounds}\n")
            f.write(f"  Players: {', '.join(state.players)}\n")
            f.write(f"  Sequential: {state.sequential}\n")
            f.write(f"  Status: {state.status}\n\n")
            
            f.write("Event Log:\n")
            f.write("----------\n")
            for event in state.event_log:
                f.write(f"Round {event.get('round', '?')} - {event.get('event', 'unknown')}\n")
                details = event.get('details', {})
                if details:
                    f.write(f"  Details: {json.dumps(details, indent=2)}\n")
                f.write("\n")
            
            f.write("Round History:\n")
            f.write("-------------\n")
            for round_data in state.round_history:
                f.write(f"Round {round_data.get('round', '?')}:\n")
                f.write(f"  Actions: {round_data.get('actions', {})}\n")
                f.write(f"  Rewards: {round_data.get('rewards', {})}\n")
                f.write("\n")
    
    def _print_to_stdout(self, state: GameState):
        """Print logs to stdout."""
        if self.format == "json":
            log_data = {
                "experiment_info": {
                    "num_rounds": state.num_rounds,
                    "players": state.players,
                    "sequential": state.sequential,
                    "timestamp": datetime.now().isoformat()
                },
                "event_log": state.event_log,
                "round_history": state.round_history
            }
            print(json.dumps(log_data, indent=2, default=str))
        else:
            # For CSV and TXT, just print a summary
            print(f"Event Log Summary:")
            print(f"  Total events: {len(state.event_log)}")
            print(f"  Total rounds: {len(state.round_history)}")
            print(f"  Players: {', '.join(state.players)}")
            print(f"  Status: {state.status}")


class AnalysisLogger:
    """Specialized logger for post-experiment analysis."""
    
    def __init__(self, output_dir: str = "analysis_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def log_player_strategies(self, state: GameState, moderator):
        """Log detailed strategy information for each player."""
        strategies_file = self.output_dir / "player_strategies.json"
        
        strategies_data = {}
        for player_name, player in moderator.players.items():
            strategies_data[player_name] = {
                "class": player.__class__.__name__,
                "history": player.history,
                "total_reward": player.total_reward,
                "average_reward": player.get_average_reward(),
                "num_rounds": len(player.history)
            }
            
            # Add strategy-specific data
            if hasattr(player, 'get_average_strategy'):
                strategies_data[player_name]["average_strategy"] = player.get_average_strategy()
            if hasattr(player, 'regrets'):
                strategies_data[player_name]["regrets"] = player.regrets
            if hasattr(player, 'opponent_history'):
                strategies_data[player_name]["opponent_history"] = player.opponent_history
        
        with open(strategies_file, 'w') as f:
            json.dump(strategies_data, f, indent=2, default=str)
    
    def log_payoff_analysis(self, state: GameState, game):
        """Log payoff analysis and game-theoretic insights."""
        analysis_file = self.output_dir / "payoff_analysis.json"
        
        # Calculate cumulative payoffs
        cumulative_payoffs = {player: 0.0 for player in state.players}
        round_payoffs = {player: [] for player in state.players}
        
        for round_data in state.round_history:
            rewards = round_data.get("rewards", {})
            for player, reward in rewards.items():
                cumulative_payoffs[player] += reward
                round_payoffs[player].append(reward)
        
        analysis_data = {
            "cumulative_payoffs": cumulative_payoffs,
            "round_payoffs": round_payoffs,
            "game_info": {
                "type": game.__class__.__name__,
                "num_actions": game.get_num_actions(),
                "num_players": game.get_num_players()
            }
        }
        
        # Add game-specific analysis
        if hasattr(game, 'get_payoff_matrix'):
            analysis_data["payoff_matrices"] = {
                f"player_{i}": game.get_payoff_matrix(i) 
                for i in range(game.get_num_players())
            }
        
        with open(analysis_file, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
    
    def log_convergence_analysis(self, state: GameState, moderator):
        """Log convergence analysis for learning algorithms."""
        convergence_file = self.output_dir / "convergence_analysis.json"
        
        convergence_data = {}
        
        for player_name, player in moderator.players.items():
            if hasattr(player, 'regrets') and player.regrets:
                # Analyze regret convergence
                convergence_data[player_name] = {
                    "regrets": player.regrets,
                    "regret_magnitude": [abs(r) for r in player.regrets],
                    "max_regret": max(abs(r) for r in player.regrets) if player.regrets else 0
                }
            
            if hasattr(player, 'get_average_strategy'):
                # Analyze strategy convergence
                avg_strategy = player.get_average_strategy()
                convergence_data[player_name] = convergence_data.get(player_name, {})
                convergence_data[player_name]["average_strategy"] = avg_strategy
                convergence_data[player_name]["strategy_entropy"] = self._calculate_entropy(avg_strategy)
        
        with open(convergence_file, 'w') as f:
            json.dump(convergence_data, f, indent=2, default=str)
    
    def _calculate_entropy(self, strategy: List[float]) -> float:
        """Calculate entropy of a strategy distribution."""
        import math
        entropy = 0.0
        for p in strategy:
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy

