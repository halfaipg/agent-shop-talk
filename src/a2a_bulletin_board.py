#!/usr/bin/env python3
"""
Agent-to-Agent (A2A) Bulletin Board implementation for Agent Shop Talk.
Provides a central message board for agents to communicate asynchronously.
"""

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Set, Union


@dataclass
class Message:
    """Represents a message that can be posted to the bulletin board."""
    content: Union[str, dict]
    sender_id: str
    sender_name: str
    recipient_id: Optional[str] = None
    recipient_name: Optional[str] = None
    topic: str = "general"
    priority: str = "normal"
    tags: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary format."""
        result = asdict(self)
        
        # Restructure for cleaner API
        return {
            "id": result["id"],
            "content": result["content"],
            "sender": {
                "id": result["sender_id"],
                "name": result["sender_name"]
            },
            "recipient": {
                "id": result["recipient_id"],
                "name": result["recipient_name"]
            } if result["recipient_id"] else None,
            "topic": result["topic"],
            "metadata": {
                "priority": result["priority"],
                "tags": result["tags"],
                "timestamp": result["timestamp"]
            }
        }


class BulletinBoard:
    """The bulletin board where agents can post and retrieve messages."""
    
    def __init__(self):
        """Initialize an empty bulletin board."""
        self._messages: Dict[str, Message] = {}  # Message ID -> Message
        self._topic_subscriptions: Dict[str, Set[str]] = {}  # Topic -> Set of agent IDs
        
    def post_message(self, message: Message) -> str:
        """Post a message to the bulletin board.
        
        Args:
            message: The message to post
            
        Returns:
            The ID of the posted message
        """
        self._messages[message.id] = message
        return message.id
    
    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific message by ID.
        
        Args:
            message_id: The ID of the message to retrieve
            
        Returns:
            The message as a dictionary, or None if not found
        """
        message = self._messages.get(message_id)
        return message.to_dict() if message else None
    
    def get_messages(self, 
                     limit: int = 100, 
                     sender_id: Optional[str] = None,
                     recipient_id: Optional[str] = None,
                     topic: Optional[str] = None,
                     tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get messages from the bulletin board with optional filtering.
        
        Args:
            limit: Maximum number of messages to return
            sender_id: Filter by sender ID
            recipient_id: Filter by recipient ID
            topic: Filter by topic
            tags: Filter by tags (messages must have at least one of these tags)
            
        Returns:
            List of messages as dictionaries, sorted by timestamp (newest first)
        """
        messages = list(self._messages.values())
        
        # Apply filters
        if sender_id:
            messages = [msg for msg in messages if msg.sender_id == sender_id]
        
        if recipient_id:
            messages = [msg for msg in messages if msg.recipient_id == recipient_id]
        
        if topic:
            messages = [msg for msg in messages if msg.topic == topic]
        
        if tags:
            messages = [msg for msg in messages if any(tag in msg.tags for tag in tags)]
        
        # Sort by timestamp (newest first)
        messages.sort(key=lambda msg: msg.timestamp, reverse=True)
        
        # Limit results and convert to dictionaries
        return [msg.to_dict() for msg in messages[:limit]]
    
    def delete_message(self, message_id: str) -> bool:
        """Delete a message from the bulletin board.
        
        Args:
            message_id: The ID of the message to delete
            
        Returns:
            True if the message was deleted, False if it wasn't found
        """
        if message_id in self._messages:
            del self._messages[message_id]
            return True
        return False
    
    def subscribe(self, agent_id: str, topics: List[str]) -> None:
        """Subscribe an agent to receive messages for specific topics.
        
        Args:
            agent_id: The ID of the agent subscribing
            topics: List of topics to subscribe to
        """
        for topic in topics:
            if topic not in self._topic_subscriptions:
                self._topic_subscriptions[topic] = set()
            self._topic_subscriptions[topic].add(agent_id)
    
    def unsubscribe(self, agent_id: str, topics: Optional[List[str]] = None) -> None:
        """Unsubscribe an agent from specific topics or all topics.
        
        Args:
            agent_id: The ID of the agent unsubscribing
            topics: List of topics to unsubscribe from, or None to unsubscribe from all
        """
        if topics is None:
            # Unsubscribe from all topics
            for subscribers in self._topic_subscriptions.values():
                if agent_id in subscribers:
                    subscribers.remove(agent_id)
        else:
            # Unsubscribe from specific topics
            for topic in topics:
                if topic in self._topic_subscriptions and agent_id in self._topic_subscriptions[topic]:
                    self._topic_subscriptions[topic].remove(agent_id)
    
    def get_subscribed_messages(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages for topics an agent is subscribed to.
        
        Args:
            agent_id: The ID of the agent
            limit: Maximum number of messages to return
            
        Returns:
            List of messages as dictionaries, sorted by timestamp (newest first)
        """
        # Get topics the agent is subscribed to
        subscribed_topics = [
            topic for topic, subscribers in self._topic_subscriptions.items()
            if agent_id in subscribers
        ]
        
        # Get messages for those topics or directly addressed to the agent
        messages = []
        for msg in self._messages.values():
            if (msg.topic in subscribed_topics) or (msg.recipient_id == agent_id):
                messages.append(msg)
        
        # Sort by timestamp (newest first)
        messages.sort(key=lambda msg: msg.timestamp, reverse=True)
        
        # Limit results and convert to dictionaries
        return [msg.to_dict() for msg in messages[:limit]]
    
    def clear(self) -> None:
        """Clear all messages from the bulletin board."""
        self._messages.clear()


# Create a global bulletin board instance
bulletin_board = BulletinBoard() 