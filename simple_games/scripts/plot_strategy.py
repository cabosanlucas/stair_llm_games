#!/usr/bin/env python3
"""
Script to plot player strategies over rounds from game logs.
Supports games with any number of actions.
"""

import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for saving files
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_log_data(log_file_path):
    """Load and parse the game log file."""
    with open(log_file_path, 'r') as f:
        data = json.load(f)
    return data

def extract_policy_data(data):
    """Extract policy data for each player across all rounds.
    
    Returns a dictionary with:
    - 'rounds': list of round numbers
    - 'players': list of player names
    - 'num_actions': number of actions in the game
    - 'policies': dict mapping player names to list of policies (one per round)
    """
    round_history = data['round_history']
    
    if not round_history:
        raise ValueError("No round history found in data")
    
    # Get player names and number of actions from first round
    first_round = round_history[0]
    players = list(first_round['policies'].keys())
    num_actions = len(first_round['policies'][players[0]])
    
    # Initialize data structure
    rounds = []
    policies = {player: [[] for _ in range(num_actions)] for player in players}
    
    # Extract policy data for each round
    for round_data in round_history:
        round_num = round_data['round']
        round_policies = round_data['policies']
        
        rounds.append(round_num)
        
        # Store each action's probability for each player
        for player in players:
            player_policy = round_policies[player]
            for action_idx, prob in enumerate(player_policy):
                policies[player][action_idx].append(prob)
    
    return {
        'rounds': rounds,
        'players': players,
        'num_actions': num_actions,
        'policies': policies
    }

def extract_reward_data(data):
    """Extract cumulative reward data for each player across all rounds.
    
    Returns a dictionary with:
    - 'rounds': list of round numbers
    - 'players': list of player names
    - 'cumulative_rewards': dict mapping player names to list of cumulative rewards
    - 'round_rewards': dict mapping player names to list of per-round rewards
    """
    round_history = data['round_history']
    
    if not round_history:
        raise ValueError("No round history found in data")
    
    # Get player names from first round
    first_round = round_history[0]
    players = list(first_round['rewards'].keys())
    
    # Initialize data structure
    rounds = []
    cumulative_rewards = {player: [] for player in players}
    round_rewards = {player: [] for player in players}
    
    # Track cumulative rewards
    running_totals = {player: 0 for player in players}
    
    # Extract reward data for each round
    for round_data in round_history:
        round_num = round_data['round']
        round_reward_data = round_data['rewards']
        
        rounds.append(round_num)
        
        # Store per-round rewards and update cumulative totals
        for player in players:
            round_reward = round_reward_data[player]
            round_rewards[player].append(round_reward)
            running_totals[player] += round_reward
            cumulative_rewards[player].append(running_totals[player])
    
    return {
        'rounds': rounds,
        'players': players,
        'cumulative_rewards': cumulative_rewards,
        'round_rewards': round_rewards
    }

def plot_strategies(policy_data, output_file=None, action_labels=None):
    """Create plots showing strategy evolution for all players.
    
    Args:
        policy_data: Dictionary containing rounds, players, num_actions, and policies
        output_file: Optional path to save the plot
        action_labels: Optional list of labels for actions (e.g., ['Cooperate', 'Defect'])
    """
    rounds = policy_data['rounds']
    players = policy_data['players']
    num_actions = policy_data['num_actions']
    policies = policy_data['policies']
    
    # Default action labels if not provided
    if action_labels is None:
        action_labels = [f'Action {i}' for i in range(num_actions)]
    
    # Color palette and markers for different actions
    colors = plt.cm.tab10(np.linspace(0, 1, num_actions))
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    
    # Create figure with subplots (one per player)
    num_players = len(players)
    fig, axes = plt.subplots(num_players, 1, figsize=(12, 5 * num_players))
    
    # Handle single player case
    if num_players == 1:
        axes = [axes]
    
    # Plot each player's strategy
    for player_idx, player in enumerate(players):
        ax = axes[player_idx]
        
        # Plot each action's probability
        for action_idx in range(num_actions):
            action_probs = policies[player][action_idx]
            ax.plot(
                rounds, 
                action_probs, 
                color=colors[action_idx],
                label=action_labels[action_idx] if action_idx < len(action_labels) else f'Action {action_idx}',
                linewidth=2, 
                marker=markers[action_idx % len(markers)], 
                markersize=4,
                alpha=0.8
            )
        
        ax.set_title(f'{player}\'s Strategy Evolution', fontsize=14, fontweight='bold')
        ax.set_xlabel('Round')
        ax.set_ylabel('Probability')
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', framealpha=0.9)
        
        # Set x-axis ticks
        if len(rounds) > 0:
            tick_spacing = max(1, len(rounds) // 10)
            ax.set_xticks(range(0, max(rounds)+1, tick_spacing))
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {output_file}")
    
    #plt.show()

def plot_cumulative_rewards(reward_data, output_file=None):
    """Create plots showing cumulative reward evolution for all players.
    
    Args:
        reward_data: Dictionary containing rounds, players, and cumulative_rewards
        output_file: Optional path to save the plot
    """
    rounds = reward_data['rounds']
    players = reward_data['players']
    cumulative_rewards = reward_data['cumulative_rewards']
    
    # Color palette for different players
    colors = plt.cm.tab10(np.linspace(0, 1, len(players)))
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Plot each player's cumulative rewards
    for player_idx, player in enumerate(players):
        player_rewards = cumulative_rewards[player]
        ax.plot(
            rounds, 
            player_rewards, 
            color=colors[player_idx],
            label=player,
            linewidth=2, 
            marker=markers[player_idx % len(markers)], 
            markersize=4,
            alpha=0.8
        )
    
    ax.set_title('Cumulative Rewards Over Time', fontsize=16, fontweight='bold')
    ax.set_xlabel('Round', fontsize=12)
    ax.set_ylabel('Cumulative Reward', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', framealpha=0.9)
    
    # Set x-axis ticks
    if len(rounds) > 0:
        tick_spacing = max(1, len(rounds) // 10)
        ax.set_xticks(range(0, max(rounds)+1, tick_spacing))
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Cumulative rewards plot saved to: {output_file}")
    
    #plt.show()

def plot_combined_strategy_and_rewards(policy_data, reward_data, output_file=None, action_labels=None):
    """Create combined plots showing both strategy evolution and cumulative rewards.
    
    Args:
        policy_data: Dictionary containing policy data
        reward_data: Dictionary containing reward data
        output_file: Optional path to save the plot
        action_labels: Optional list of labels for actions
    """
    rounds = policy_data['rounds']
    players = policy_data['players']
    num_actions = policy_data['num_actions']
    policies = policy_data['policies']
    cumulative_rewards = reward_data['cumulative_rewards']
    
    # Default action labels if not provided
    if action_labels is None:
        action_labels = [f'Action {i}' for i in range(num_actions)]
    
    # Color palette and markers for different actions and players
    action_colors = plt.cm.tab10(np.linspace(0, 1, num_actions))
    player_colors = plt.cm.Set1(np.linspace(0, 1, len(players)))
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    
    # Create figure with subplots (strategy plots + reward plot)
    num_players = len(players)
    fig, axes = plt.subplots(num_players + 1, 1, figsize=(14, 6 * (num_players + 1)))
    
    # Handle single player case
    if num_players == 1:
        axes = [axes[0], axes[1]]
    
    # Plot each player's strategy
    for player_idx, player in enumerate(players):
        ax = axes[player_idx]
        
        # Plot each action's probability
        for action_idx in range(num_actions):
            action_probs = policies[player][action_idx]
            ax.plot(
                rounds, 
                action_probs, 
                color=action_colors[action_idx],
                label=action_labels[action_idx] if action_idx < len(action_labels) else f'Action {action_idx}',
                linewidth=2, 
                marker=markers[action_idx % len(markers)], 
                markersize=4,
                alpha=0.8
            )
        
        ax.set_title(f'{player}\'s Strategy Evolution', fontsize=14, fontweight='bold')
        ax.set_xlabel('Round')
        ax.set_ylabel('Probability')
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', framealpha=0.9)
        
        # Set x-axis ticks
        if len(rounds) > 0:
            tick_spacing = max(1, len(rounds) // 10)
            ax.set_xticks(range(0, max(rounds)+1, tick_spacing))
    
    # Plot cumulative rewards in the last subplot
    ax_rewards = axes[-1]
    for player_idx, player in enumerate(players):
        player_rewards = cumulative_rewards[player]
        ax_rewards.plot(
            rounds, 
            player_rewards, 
            color=player_colors[player_idx],
            label=player,
            linewidth=2, 
            marker=markers[player_idx % len(markers)], 
            markersize=4,
            alpha=0.8
        )
    
    ax_rewards.set_title('Cumulative Rewards Over Time', fontsize=14, fontweight='bold')
    ax_rewards.set_xlabel('Round')
    ax_rewards.set_ylabel('Cumulative Reward')
    ax_rewards.grid(True, alpha=0.3)
    ax_rewards.legend(loc='best', framealpha=0.9)
    
    # Set x-axis ticks
    if len(rounds) > 0:
        tick_spacing = max(1, len(rounds) // 10)
        ax_rewards.set_xticks(range(0, max(rounds)+1, tick_spacing))
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Combined plot saved to: {output_file}")
    
    #plt.show()

def analyze_convergence(policy_data, window_size=10, threshold=0.1):
    """Analyze when each player's strategy converges.
    
    Args:
        policy_data: Dictionary containing policy data
        window_size: Number of rounds to check for stability (default: 10)
        threshold: Standard deviation threshold for convergence (default: 0.1)
    """
    rounds = policy_data['rounds']
    players = policy_data['players']
    num_actions = policy_data['num_actions']
    policies = policy_data['policies']
    
    print("\n=== CONVERGENCE ANALYSIS ===")
    print(f"Window size: {window_size} rounds")
    print(f"Convergence threshold (std dev): {threshold}")
    
    for player in players:
        print(f"\n{player}'s Strategy:")
        
        # Print final policy
        print(f"  Final policy:")
        for action_idx in range(num_actions):
            action_probs = policies[player][action_idx]
            print(f"    Action {action_idx}: {action_probs[-1]:.3f}")
        
        # Check stability in last N rounds
        if len(rounds) >= window_size:
            print(f"\n  Standard deviation in last {window_size} rounds:")
            all_stable = True
            
            for action_idx in range(num_actions):
                action_probs = policies[player][action_idx]
                last_n_probs = action_probs[-window_size:]
                std_dev = np.std(last_n_probs)
                
                print(f"    Action {action_idx}: {std_dev:.4f}")
                
                if std_dev >= threshold:
                    all_stable = False
            
            if all_stable:
                print(f"  Status: ✓ CONVERGED (stable in last {window_size} rounds)")
            else:
                print(f"  Status: ✗ NOT CONVERGED (still changing)")
        else:
            print(f"  Status: INSUFFICIENT DATA (need at least {window_size} rounds)")
        
        # Overall stability check
        print(f"\n  Standard deviation across all rounds:")
        overall_stable = True
        
        for action_idx in range(num_actions):
            action_probs = policies[player][action_idx]
            std_dev = np.std(action_probs)
            print(f"    Action {action_idx}: {std_dev:.4f}")
            
            if std_dev >= 0.01:
                overall_stable = False
        
        if overall_stable:
            print(f"  Overall: Stable from start (very low variance)")
        else:
            print(f"  Overall: Strategy evolved over time")

def detect_game_type(num_actions):
    """Detect game type and return appropriate action labels."""
    if num_actions == 2:
        return ['Cooperate', 'Defect']
    elif num_actions == 4:
        # Common 4-action games might be extended prisoner's dilemma or other games
        return ['Action 0', 'Action 1', 'Action 2', 'Action 3']
    else:
        return [f'Action {i}' for i in range(num_actions)]

def main(log_file_path=None, action_labels=None, output_file=None, plot_type='combined'):
    """Main function to run the analysis.
    
    Args:
        log_file_path: Optional path to log file. If None, looks for prisoners_dilemma_log.json
        action_labels: Optional list of labels for actions
        output_file: Optional path to save the plot
        plot_type: Type of plot to generate ('strategy', 'rewards', 'combined')
    """

    log_file = Path(log_file_path)
    if not log_file.exists():
        print(f"Error: Log file not found at {log_file}")
        return

    print(f"Loading data from: {log_file}")
    
    # Load and process data
    data = load_log_data(log_file)
    policy_data = extract_policy_data(data)
    
    # Extract reward data if available
    reward_data = None
    try:
        reward_data = extract_reward_data(data)
        print("✓ Reward data found and extracted")
    except (KeyError, ValueError) as e:
        print(f"⚠ Warning: Could not extract reward data: {e}")
        if plot_type in ['rewards', 'combined']:
            print("Falling back to strategy-only plotting")
            plot_type = 'strategy'
    
    # Print experiment info
    if 'experiment_info' in data:
        exp_info = data['experiment_info']
        print(f"\nExperiment Info:")
        print(f"  Rounds: {exp_info.get('num_rounds', 'N/A')}")
        print(f"  Players: {exp_info.get('players', policy_data['players'])}")
        print(f"  Sequential: {exp_info.get('sequential', 'N/A')}")
    elif 'experiment_metadata' in data:
        exp_info = data['experiment_metadata']
        print(f"\nExperiment Info:")
        print(f"  Rounds: {exp_info.get('num_rounds', 'N/A')}")
        print(f"  Players: {exp_info.get('players', policy_data['players'])}")
        print(f"  Sequential: {exp_info.get('sequential', 'N/A')}")
        print(f"  Duration: {exp_info.get('duration_seconds', 'N/A'):.2f}s")
    
    print(f"  Number of actions: {policy_data['num_actions']}")
    
    # Print reward summary if available
    if reward_data:
        print(f"\nReward Summary:")
        for player in reward_data['players']:
            final_reward = reward_data['cumulative_rewards'][player][-1] if reward_data['cumulative_rewards'][player] else 0
            avg_reward = final_reward / len(reward_data['rounds']) if len(reward_data['rounds']) > 0 else 0
            print(f"  {player}: Total={final_reward:.1f}, Average={avg_reward:.2f}")
    
    # Detect action labels if not provided
    if action_labels is None:
        action_labels = detect_game_type(policy_data['num_actions'])
    
    # Analyze convergence
    analyze_convergence(policy_data)
    
    # Create plots based on plot_type
    if output_file:
        output_file = Path(output_file)
        base_name = output_file.stem
        output_dir = output_file.parent
    else:
        base_name = "game_analysis"
        output_dir = Path(".")
    
    if plot_type == 'strategy':
        strategy_output = output_dir / f"{base_name}_strategy.png"
        plot_strategies(policy_data, strategy_output, action_labels)
    elif plot_type == 'rewards' and reward_data:
        rewards_output = output_dir / f"{base_name}_rewards.png"
        plot_cumulative_rewards(reward_data, rewards_output)
    elif plot_type == 'combined' and reward_data:
        combined_output = output_dir / f"{base_name}_combined.png"
        plot_combined_strategy_and_rewards(policy_data, reward_data, combined_output, action_labels)
    else:
        # Default fallback
        strategy_output = output_dir / f"{base_name}_strategy.png"
        plot_strategies(policy_data, strategy_output, action_labels)

if __name__ == "__main__":
    import sys
    import os
    import argparse
    
    parser = argparse.ArgumentParser(description='Plot player strategies and rewards from game logs')
    parser.add_argument('log_file', nargs='?', help='Path to log file or directory containing log files')
    parser.add_argument('--output', '-o', help='Output file path (for single file) or directory (for batch)')
    parser.add_argument('--plot-type', '-t', choices=['strategy', 'rewards', 'combined'], 
                       default='combined', help='Type of plot to generate (default: combined)')
    parser.add_argument('--action-labels', nargs='+', help='Custom labels for actions')
    
    args = parser.parse_args()
    
    if args.log_file:
        if os.path.isdir(args.log_file):
            # Batch processing for directory
            files = os.listdir(args.log_file)
            files = [os.path.join(args.log_file, f) for f in files if f.endswith('.json')]
            
            print(f"Found {len(files)} log files to process")
            for file in files:
                print(f"\n{'='*50}")
                print(f"Processing: {file}")
                print('='*50)
                
                if args.output and os.path.isdir(args.output):
                    output_file = os.path.join(args.output, os.path.basename(file).replace('.json', '_plot.png'))
                else:
                    output_file = file.replace('.json', '_plot.png')
                
                main(file, args.action_labels, output_file, args.plot_type)
        else:
            # Single file processing
            if args.output:
                output_file = args.output
            else:
                output_file = args.log_file.replace('.json', '_plot.png')
            
            main(args.log_file, args.action_labels, output_file, args.plot_type)
    else:
        # Default behavior - look for common log file names
        common_names = ['prisoners_dilemma_log.json', 'game_log.json']
        found = False
        
        for name in common_names:
            if os.path.exists(name):
                print(f"Found default log file: {name}")
                main(name, args.action_labels, name.replace('.json', '_plot.png'), args.plot_type)
                found = True
                break
        
        if not found:
            print("No log file specified and no default files found.")
            print("Usage: python plot_strategy.py <log_file> [options]")
            print("       python plot_strategy.py <directory> [options]")
            parser.print_help()
