import random
from dataclasses import dataclass
from autogen_core import RoutedAgent, MessageContext, default_subscription, message_handler
from player import Player


@dataclass 
class DealRequest:
    player_name: str
    num_decks: int = 1

@dataclass
class HitRequest:
    player_name: str


@default_subscription
class Dealer(Player, RoutedAgent):
    """Dealer class that handles card dealing and plays the game"""
    
    def __init__(self):
        # Initialize Player with dealer name
        Player.__init__(self, "Dealer")
        # Initialize RoutedAgent
        RoutedAgent.__init__(self, "A dealer agent that handles card dealing in blackjack")
        
        # Deck management
        self.suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
        self.deck = []
        self.shuffle_deck()
    
    def shuffle_deck(self, num_decks: int = 1):
        """Shuffle a new deck with specified number of decks"""
        self.deck = [(rank, suit) for _ in range(num_decks) 
                    for rank in self.ranks 
                    for suit in self.suits]
        random.shuffle(self.deck)
        print(f"Dealer shuffled {num_decks} deck(s) - {len(self.deck)} cards")
    
    @message_handler
    async def handle_deal_request(self, message: DealRequest, ctx: MessageContext) -> None:
        """Handle requests to deal cards"""
        if len(self.deck) < 1:
            self.shuffle_deck(message.num_decks)
        
        card = self.deck.pop()
        await self.publish_message(
            f"Dealt {card[0]} of {card[1]} to {message.player_name}",
            ctx.reply_topic
        )
    
    @message_handler
    async def handle_hit_request(self, message: HitRequest, ctx: MessageContext) -> None:
        """Handle requests to hit (deal one card to a player)"""
        if len(self.deck) < 1:
            self.shuffle_deck()
        
        card = self.deck.pop()
        await self.publish_message(
            f"Dealt {card[0]} of {card[1]} to {message.player_name}",
            ctx.reply_topic
        )
    
    def deal_card(self):
        """Deal a single card from the deck"""
        if len(self.deck) < 1:
            self.shuffle_deck()
        
        card = self.deck.pop()
        return card
    
    def deal_initial_cards(self, players):
        """Deal initial 2 cards to each player and dealer"""
        print("Dealing initial cards...")
        
        # Deal to players
        for player in players:
            for _ in range(2):
                card = self.deal_card()
                player.add_card(card)
                print(f"Dealt {card[0]} of {card[1]} to {player.name}")
        
        # Deal to dealer
        for _ in range(2):
            card = self.deal_card()
            self.add_card(card)
            print(f"Dealt {card[0]} of {card[1]} to {self.name}")
        
        print("Initial cards dealt!")
        self.display_initial_state(players)
    
    def display_initial_state(self, players):
        """Display the initial game state after dealing"""
        for player in players:
            print(f"{player.get_hand_display()}")
        
        # Show dealer's upcard
        if len(self.hand) >= 2:
            upcard = self.hand[0]
            upcard_value = self._get_card_value(upcard)
            print(f"Dealer: {upcard} + [Hidden] (Upcard value: {upcard_value})")
    
    def _get_card_value(self, card):
        """Get the value of a single card"""
        rank = card[0]
        if rank in ['Jack', 'Queen', 'King']:
            return 10
        elif rank == 'Ace':
            return 11
        else:
            return int(rank)
    
    def play_dealer_hand(self):
        """Dealer plays according to blackjack rules (hit until 17)"""
        print(f"\n{self.name} reveals hidden card: {self.hand[1]}")
        print(f"{self.get_hand_display()}")
        
        while self.score < 17:
            card = self.deal_card()
            self.add_card(card)
            print(f"{self.name} hits! New card: {card[0]} of {card[1]}")
            print(f"{self.get_hand_display()}")
        
        if self.busted:
            print(f"{self.name} busts!")
            return True  # Dealer busted
        else:
            print(f"{self.name} stands with {self.score}")
            return False
    
    def get_upcard_display(self):
        """Get display for dealer's upcard only"""
        if len(self.hand) >= 1:
            return f"Dealer's upcard: {self.hand[0]}"
        return "No dealer card visible yet"
    
    def reset(self):
        """Reset dealer for new game"""
        super().reset()
        self.shuffle_deck()


def build_dealer():
    """Build and return a dealer instance"""
    return Dealer()
