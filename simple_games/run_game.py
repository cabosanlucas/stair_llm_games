
import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
load_dotenv()

from src import (TitForTatPlayer, LLMPlayer, RegretMatchingPlayer, GameState, Moderator, Experiment, EventLogger)
from src.LLMPlayer import LangGraphLLMPlayer
from src.game import Custom4PGame, PrisonersDilemma
from scripts.plot_strategy import main as plot_strategies


def play_game(game, players, num_rounds, log_file, output_file):
    # Create game state
    player_names = [player.name for player in players]
    state = GameState(num_rounds=num_rounds, player_names=player_names, sequential=False)

    # Create moderator
    moderator = Moderator(game, players, state, seed=42)

    # Create logger
    logger = EventLogger(log_file)

    # Run experiment
    experiment = Experiment(moderator, state, logger)
    results = experiment.run(verbose=True)

    print("\n" + experiment.get_summary())

    # Save detailed results
    experiment.save_results(log_file)

    # Plot strategies
    # plot_strategies(log_file_path=log_file, output_file=output_file)

    return results


def single_game_test():
    """Run a single Prisoner's Dilemma experiment with different player types."""
    output_dir = "custom_game_logs/single_game"
    os.makedirs(output_dir, exist_ok=True)

    ## make game / players
    game = Custom4PGame()
    players = [
        LangGraphLLMPlayer("Alice - LangGraph", num_actions=game.get_num_actions(), model_name="gpt-4o-mini", max_correction_attempts=3), 
        LangGraphLLMPlayer("Bob - LangGraph", num_actions=game.get_num_actions(), model_name="gpt-4o-mini", max_correction_attempts=3)
    ]

    # Run game
    results = play_game(game, players, 50, f"{output_dir}/game_log.json", f"{output_dir}/game_strategy_evolution.png")
    print(results)



def main():
    """Run a Prisoner's Dilemma experiment with different player types."""
    parser = argparse.ArgumentParser(description="Run LLM games experiment.")
    parser.add_argument('--n_games', type=int, default=10, help='Number of games to run')
    parser.add_argument('--out_dir', type=str, default='custom_game_logs/4o_mini_v_o3_mini', help='Output directory for logs and plots')
    parser.add_argument('--model_name_1', type=str, default='gpt-4o-mini', help='Model name for player 1')
    parser.add_argument('--model_name_2', type=str, default='o3-mini', help='Model name for player 2')
    parser.add_argument('--use_cot', action='store_true', help='Whether to use chain-of-thought for LLM players')
    args = parser.parse_args()

    n_games = args.n_games
    output_dir = args.out_dir
    os.makedirs(output_dir, exist_ok=True)

    # make games / players
    games = [Custom4PGame() for _ in range(n_games)]
    players_list = []
    for game in games:
        players = [
            LangGraphLLMPlayer(f"Alice {args.model_name_1}", num_actions=game.get_num_actions(), model_name=args.model_name_1, use_cot=args.use_cot),
            LangGraphLLMPlayer(f"Bob {args.model_name_2}", num_actions=game.get_num_actions(), model_name=args.model_name_2, use_cot=args.use_cot)
        ]
        players_list.append(players)

    # Run games in parallel using ThreadPoolExecutor
    results = []
    with ThreadPoolExecutor(max_workers=n_games) as executor:
        # Submit all tasks
        future_to_game = {
            executor.submit(
                play_game,
                games[i],
                players_list[i],
                50,
                f"{output_dir}/game_log_{i}.json",
                f"{output_dir}/game_strategy_evolution_{i}.png"
            ): i for i in range(n_games)
        }

        # Collect results as they complete
        for future in as_completed(future_to_game):
            game_id = future_to_game[future]
            try:
                result = future.result()
                results.append((game_id, result))
                print(f"Game {game_id} completed!")
            except Exception as exc:
                print(f"Game {game_id} generated an exception: {exc}")

    # Sort results by game ID
    results.sort(key=lambda x: x[0])
    print(f"All {n_games} games completed!")
    os.system(f"uv run plot_strategy.py {output_dir}")
    print(results)

if __name__ == "__main__":
    main()