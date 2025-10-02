from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


class Player(AssistantAgent):
    """Base player class for blackjack game logic"""
    
    def __init__(self, name: str, tools=None, system_message=None, model_client=None):
        # Initialize AssistantAgent
        model_client = model_client or OpenAIChatCompletionClient(model="gpt-4o")
        
        # Default system message if none provided
        if system_message is None:
            system_message = f"""You are {name} in a blackjack game. 
            
Your goal is to get as close to 21 as possible without going over. You can:
- Use the hit tool to take another card
- Use the stand tool to keep your current hand
- Use view_hand to see your cards and score
- Use view_dealer_upcard to see the dealer's visible card

When calling tools, always use your exact name: "{name}"

Make strategic decisions based on your hand and the dealer's upcard. 
Remember: Face cards are worth 10, Aces can be 1 or 11, and you bust if you go over 21."""
        
        super().__init__(
            name=name,
            model_client=model_client,
            system_message=system_message,
            tools=tools or []
        )
        
        # Player-specific game state attributes
        self.hand = []
        self.score = 0
        self.busted = False
        self.standing = False
    
    #### Game Logic Methods ####
    def add_card(self, card):
        """Add a card to the player's hand"""
        self.hand.append(card)
        self.score = self.calculate_hand_value()
        
        # Check for bust
        if self.score > 21:
            self.busted = True
    
    def calculate_hand_value(self):
        """Calculate the value of a hand, handling aces properly"""
        value = 0
        aces = 0
        
        for rank, suit in self.hand:
            if rank in ['Jack', 'Queen', 'King']:
                value += 10
            elif rank == 'Ace':
                aces += 1
                value += 11
            else:
                value += int(rank)
        
        # Adjust for aces
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
            
        return value
    
    def stand(self):
        """Player decides to stand"""
        self.standing = True
    
    def reset(self):
        """Reset player for new game"""
        self.hand = []
        self.score = 0
        self.busted = False
        self.standing = False
    
    #### Utility Methods ####
    def get_hand_display(self):
        """Get formatted hand display"""
        return f"{self.name}: {self.hand} (Score: {self.score})"
    
    def is_active(self):
        """Check if player is still active (not busted and not standing)"""
        return not self.busted and not self.standing

