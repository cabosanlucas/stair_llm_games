import os
import asyncio
from dotenv import load_dotenv
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Import our game classes
from player import Player
from dealer import Dealer, build_dealer
from game_state import GameState

# Load environment variables from .env file
load_dotenv()


class BlackjackGameFlow:
    """Blackjack game using GraphFlow for structured execution"""
    
    def __init__(self, num_players=2):
        self.num_players = num_players
        self.game_state = None
        self.dealer = None
        self.player_agents = []
        self.player_objects = []
        
    #### Blackjack Game Tools ####
    def bet(self, name: str, value: int) -> str:
        """Place a bet"""
        return f"{name} bets {value}"
    
    def hit(self, player_name: str) -> str:
        """Hit - take another card"""
        print(f"\n--- {player_name} decides to HIT! ---")
        if self.game_state:
            # Find the player in game state
            player = next((p for p in self.game_state.players if p.name == player_name), None)
            if player and player.is_active():
                # Deal a card from the dealer
                card = self.game_state.dealer.deal_card()
                player.add_card(card)
                
                print(f"{player_name} hits! New card: {card[0]} of {card[1]}")
                print(f"{player_name}'s hand: {player.hand} (Score: {player.score})")
                
                if player.busted:
                    print(f"{player_name} busts!")
                    # Player busted, turn is complete
                    self.game_state.complete_player_turn(player_name)
                    return f"{player_name} hits and busts with {player.score}!"
                return f"{player_name} hits! New score: {player.score}"
            return f"{player_name} cannot hit (not active)"
        return f"{player_name} hits!"
    
    def stand(self, player_name: str) -> str:
        """Stand - keep current hand"""
        print(f"\n--- {player_name} decides to STAND! ---")
        if self.game_state:
            player = next((p for p in self.game_state.players if p.name == player_name), None)
            if player:
                player.stand()
                print(f"{player_name} stands with {player.score}")
                # Mark turn as complete
                self.game_state.complete_player_turn(player_name)
                return f"{player_name} stands with {player.score}"
        return f"{player_name} stands!"
    
    def view_hand(self, player_name: str) -> str:
        """View your current hand and score"""
        print(f"\n--- {player_name} checks their hand ---")
        if self.game_state:
            player = next((p for p in self.game_state.players if p.name == player_name), None)
            if player:
                result = f"{player_name}'s hand: {player.hand} (Score: {player.score})"
                print(f"  {result}")
                return result
        return f"{player_name}'s hand not available"
    
    def view_dealer_upcard(self) -> str:
        """View dealer's visible card"""
        print(f"\n--- Checking dealer's upcard ---")
        if self.game_state and len(self.game_state.dealer.hand) > 0:
            result = f"Dealer's upcard: {self.game_state.dealer.hand[0]}"
            print(f"  {result}")
            return result
        result = "No dealer card visible yet"
        print(f"  {result}")
        return result
    
    def _create_blackjack_tools(self):
        """Create blackjack tools for the game flow"""
        
        # Create tools
        bet_tool = FunctionTool(self.bet, description="Place a bet")
        hit_tool = FunctionTool(self.hit, description="Hit - take another card")
        stand_tool = FunctionTool(self.stand, description="Stand - keep current hand")
        view_hand_tool = FunctionTool(self.view_hand, description="View your current hand and score")
        view_dealer_tool = FunctionTool(self.view_dealer_upcard, description="View dealer's visible card")
        
        return [bet_tool, hit_tool, stand_tool, view_hand_tool, view_dealer_tool]
        
    def create_game_components(self):
        """Create all game components"""
        # Create dealer
        self.dealer = Dealer()
        
        # Create player objects for game logic
        self.player_objects = [Player(f"Player_{i+1}") for i in range(self.num_players)]
        
        # Create game state
        self.game_state = GameState(self.player_objects, self.dealer)
        
        # Create player agents with tools from game flow
        self.player_agents = []
        blackjack_tools = self._create_blackjack_tools()
        
        for i in range(self.num_players):
            player_name = f"Player_{i+1}"
            agent = Player(
                name=player_name,
                tools=blackjack_tools
            )
            self.player_agents.append(agent)
        
        # Create dealer agent
        dealer_agent = build_dealer()
        
        return self.player_agents, dealer_agent
    
    def get_game_summary(self):
        """Get current game state summary"""
        if not self.game_state:
            return "Game not started"
        
        summary = {
            "players": [f"{p.name}: {p.score}" for p in self.player_objects],
            "dealer_upcard": self.dealer.hand[0] if len(self.dealer.hand) > 0 else "None",
            "active_players": [p.name for p in self.player_objects if p.is_active()]
        }
        return str(summary)
    
    def build_game_graph(self, player_agents, dealer_agent):
        """Build the DiGraph for the blackjack game flow with turn control"""
        graph = DiGraphBuilder()
        
        # Add all nodes
        for agent in player_agents:
            graph.add_node(agent)
        graph.add_node(dealer_agent)
        
        # Set the first player as the start node
        if player_agents:
            graph.set_entry_point(player_agents[0])
        
        # Create conditional edges based on turn completion
        for i, agent in enumerate(player_agents):
            # Each player has a self-loop until their turn is complete
            graph.add_edge(
                agent, 
                agent, 
                condition=lambda message, agent_name=agent.name: not self.game_state.is_player_turn_complete(agent_name)
            )
            
            # When turn is complete, move to next player or dealer
            if i < len(player_agents) - 1:
                # Move to next player when current player's turn is complete
                next_agent = player_agents[i + 1]
                graph.add_edge(
                    agent, 
                    next_agent, 
                    condition='stand'
                )
            else:
                # Last player goes to dealer when their turn is complete
                graph.add_edge(
                    agent, 
                    dealer_agent, 
                    condition='stand'
                )
        
        return graph.build()
    

