import asyncio
from autogen_agentchat.teams import GraphFlow
from autogen_agentchat.conditions import MaxMessageTermination, FunctionalTermination
from graphflow_blackjack import BlackjackGameFlow

async def run_game(game: BlackjackGameFlow):
    """Run the complete blackjack game using GraphFlow"""
    print("Welcome to Blackjack!")
    print("="*50)
    
    # Create game components
    player_agents, dealer_agent = game.create_game_components()
    
    # Deal initial cards
    game.game_state.start_game()
    
    # Build the game graph
    graph = game.build_game_graph(player_agents, dealer_agent)
    
    # Create termination conditions
    dealer_turn_termination = FunctionalTermination(
        func=lambda messages: game.game_state.game_state == "finished"
    )
    max_messages_termination = MaxMessageTermination(50)  # Safety limit
    
    # Create the flow with termination conditions
    flow = GraphFlow(
        player_agents + [dealer_agent], 
        graph=graph,
        termination_condition=dealer_turn_termination | max_messages_termination
    )
    
    print("\n" + "="*50)
    print("STARTING BLACKJACK GAME")
    print("="*50)
    print("Game flow: Players take turns, then dealer plays")
    print(f"Players: {[p.name for p in player_agents]}")
    print("="*50)
    
    # Run the flow
    stream = flow.run_stream(task="Play a game of blackjack. Each player should view their hand and dealer's upcard, then decide to hit or stand. The dealer will play after all players finish.")
    
    # Process the stream
    async for event in stream:
        if hasattr(event, 'content'):
            print(f"\n[EVENT] {event.content}")
        elif hasattr(event, 'stop_reason'):
            print(f"\n[FLOW COMPLETED] Reason: {event.stop_reason}")
            break
    
    # Ensure dealer plays and winners are determined
    if game.game_state.game_state != "finished":
        print("\n" + "="*50)
        print("DEALER TURN")
        print("="*50)
        game.game_state.start_dealer_turn()
    
    print("\nGame over! Thanks for playing!")
    
async def main():
    """Main function to run the blackjack game using GraphFlow"""
    # Number of players (can be configured)
    n_players = 2
    
    print("Starting Blackjack Game...")
    print("=" * 50)
    
    # Create and run the game
    game = BlackjackGameFlow(n_players)
    await run_game(game)


if __name__ == "__main__":
    asyncio.run(main())
