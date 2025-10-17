"""
Topic and Message abstractions for structured communication.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Topic:
    """Represents a communication channel/topic."""
    name: str  # e.g., "private:player1", "public"
    
    def is_private(self) -> bool:
        """Check if this is a private topic."""
        return self.name.startswith("private:")
    
    def is_public(self) -> bool:
        """Check if this is a public topic."""
        return self.name == "public"
    
    def get_player_name(self) -> Optional[str]:
        """Extract player name from private topic, or None if not private."""
        if self.is_private():
            return self.name.split(":", 1)[1]
        return None


@dataclass
class Message:
    """Structured message for communication between moderator and players."""
    sender: str
    receiver: Optional[str]
    topic: Topic
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_private(self) -> bool:
        """Check if this is a private message."""
        return self.topic.is_private()
    
    def is_public(self) -> bool:
        """Check if this is a public message."""
        return self.topic.is_public()
    
    def __repr__(self) -> str:
        return f"Message({self.sender} -> {self.receiver}, topic={self.topic.name})"

