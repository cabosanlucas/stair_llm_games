from typing import List, Dict, Any
from player import Player
from dealer import Dealer


class GameState:
    """GameState class to log and monitor groupchat events, track hands, and determine winners"""
    
    def __init__(self, players: List[Player], dealer: Dealer):
        self.players = players
        self.dealer = dealer
        self.game_state = "betting"  # betting, playing, dealer_turn, finished
        self.turn_order = []
        self.current_turn = 0
        self.game_log = []
        self.completed_turns = set()  # Track which players have completed their turns
        
        # Initialize turn order
        self.turn_order = [player.name for player in players]
        self.current_turn = 0
    
    def log_event(self, event: str, details: Dict[str, Any] = None):
        """Log a game event"""
        log_entry = {
            "event": event,
            "details": details or {},
            "game_state": self.game_state
        }
        self.game_log.append(log_entry)
        print(f"[GAME LOG] {event}")
        if details:
            for key, value in details.items():
                print(f"  {key}: {value}")
    
    def start_game(self):
        """Start the game and deal initial cards"""
        self.game_state = "playing"
        self.log_event("Game started", {
            "players": [p.name for p in self.players],
            "dealer": self.dealer.name
        })
        
        # Deal initial cards
        self.dealer.deal_initial_cards(self.players)
        
        self.log_event("Initial cards dealt", {
            "player_hands": {p.name: p.hand for p in self.players},
            "dealer_upcard": self.dealer.hand[0] if len(self.dealer.hand) > 0 else None
        })
    
    def get_current_player(self) -> Player:
        """Get the current player whose turn it is"""
        if self.current_turn < len(self.turn_order):
            player_name = self.turn_order[self.current_turn]
            return next(p for p in self.players if p.name == player_name)
        return None
    
    def next_turn(self):
        """Move to the next player's turn"""
        self.current_turn += 1
        
        # Check if all players have finished
        if self.current_turn >= len(self.turn_order):
            self.start_dealer_turn()
        else:
            current_player = self.get_current_player()
            if current_player and current_player.is_active():
                self.log_event("Player turn started", {
                    "player": current_player.name,
                    "hand": current_player.hand,
                    "score": current_player.score
                })
            else:
                # Skip inactive players
                self.next_turn()
    
    def start_dealer_turn(self):
        """Start the dealer's turn"""
        self.game_state = "dealer_turn"
        self.log_event("Dealer turn started", {
            "dealer_hand": self.dealer.hand,
            "dealer_score": self.dealer.score
        })
        
        # Dealer plays
        dealer_busted = self.dealer.play_dealer_hand()
        
        self.log_event("Dealer turn completed", {
            "dealer_busted": dealer_busted,
            "final_dealer_score": self.dealer.score
        })
        
        # Determine winners
        self.determine_winners()
    
    def determine_winners(self):
        """Determine the winners of the game"""
        self.game_state = "finished"
        
        print("\n" + "="*50)
        print("FINAL RESULTS")
        print("="*50)
        
        dealer_busted = self.dealer.busted
        results = {}
        
        for player in self.players:
            player_busted = player.busted
            
            if player_busted:
                result = "BUST - Loses"
                print(f"{player.name}: BUST ({player.score}) - Loses")
            elif dealer_busted:
                result = "Wins (Dealer busted)"
                print(f"{player.name}: {player.score} - Wins (Dealer busted)")
            elif player.score > self.dealer.score:
                result = f"Wins (Beats dealer's {self.dealer.score})"
                print(f"{player.name}: {player.score} - Wins (Beats dealer's {self.dealer.score})")
            elif player.score == self.dealer.score:
                result = f"Push (Ties dealer's {self.dealer.score})"
                print(f"{player.name}: {player.score} - Push (Ties dealer's {self.dealer.score})")
            else:
                result = f"Loses (Dealer's {self.dealer.score} wins)"
                print(f"{player.name}: {player.score} - Loses (Dealer's {self.dealer.score} wins)")
            
            results[player.name] = {
                "score": player.score,
                "result": result,
                "busted": player_busted
            }
        
        print(f"Dealer: {self.dealer.score}")
        if dealer_busted:
            print("Dealer: BUST")
        
        self.log_event("Game completed", {
            "final_results": results,
            "dealer_score": self.dealer.score,
            "dealer_busted": dealer_busted
        })
        
        return results
    
    def display_game_state(self):
        """Display the current state of the game"""
        print("\n" + "-"*40)
        print("CURRENT GAME STATE")
        print("-"*40)
        
        # Show all player hands
        for player in self.players:
            status = "BUST" if player.busted else f"Score: {player.score}"
            if player.standing:
                status += " (STANDING)"
            print(f"{player.name}: {player.hand} ({status})")
        
        # Show dealer hand
        if len(self.dealer.hand) >= 2:
            print(f"Dealer: {self.dealer.hand[0]} + [Hidden]")
        else:
            print(f"Dealer: {self.dealer.hand}")
        
        # Show current turn info
        if self.game_state == "playing":
            current_player = self.get_current_player()
            if current_player:
                print(f"Current turn: {current_player.name}")
        
        print("-"*40)
    
    def get_active_players(self) -> List[Player]:
        """Get list of players who are still active (not busted and not standing)"""
        return [player for player in self.players if player.is_active()]
    
    def all_players_finished(self) -> bool:
        """Check if all players have finished their turns (busted or standing)"""
        return len(self.get_active_players()) == 0
    
    def complete_player_turn(self, player_name: str):
        """Mark a player's turn as complete"""
        self.completed_turns.add(player_name)
        self.log_event(f"Player {player_name} completed their turn")
    
    def is_player_turn_complete(self, player_name: str) -> bool:
        """Check if a player has completed their turn"""
        return player_name in self.completed_turns
    
    def all_players_completed_turns(self) -> bool:
        """Check if all players have completed their turns"""
        return len(self.completed_turns) == len(self.players)
    
    def reset_game(self):
        """Reset the game for a new round"""
        self.game_state = "betting"
        self.current_turn = 0
        self.game_log = []
        self.completed_turns = set()  # Reset completed turns
        
        # Reset all players
        for player in self.players:
            player.reset()
        
        # Reset dealer
        self.dealer.reset()
        
        self.log_event("Game reset for new round")
    
    def get_game_summary(self) -> Dict[str, Any]:
        """Get a summary of the current game state"""
        return {
            "game_state": self.game_state,
            "current_turn": self.current_turn,
            "current_player": self.get_current_player().name if self.get_current_player() else None,
            "active_players": [p.name for p in self.get_active_players()],
            "player_scores": {p.name: p.score for p in self.players},
            "dealer_score": self.dealer.score,
            "dealer_busted": self.dealer.busted,
            "total_events": len(self.game_log)
        }
