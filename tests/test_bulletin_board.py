#!/usr/bin/env python3
"""
Test script for Agent Shop Talk A2A Bulletin Board implementation.
Demonstrates inter-agent communication through the bulletin board.
"""

import time
from datetime import datetime, timedelta
from src.a2a_bulletin_board import bulletin_board, Message


def test_bulletin_board():
    """Test A2A bulletin board functionality."""
    print("Agent Shop Talk - A2A Bulletin Board Test")
    print("-" * 50)
    
    # Define some test agents
    agents = [
        {"id": "agent1", "name": "Data Processing Agent"},
        {"id": "agent2", "name": "Analysis Agent"},
        {"id": "agent3", "name": "Reporting Agent"}
    ]
    
    # 1. Post messages from different agents
    print("\nPosting messages to the bulletin board:")
    
    # Message with short TTL (1 second)
    temp_msg_id = bulletin_board.post_message(
        Message(
            content="This is a temporary message that will expire",
            sender_id=agents[0]["id"],
            sender_name=agents[0]["name"],
            topic="system",
            ttl=1,  # 1 second TTL
            priority="low"
        )
    )
    print(f"  Posted temporary message (ID: {temp_msg_id})")
    
    # Broadcast message (no specific recipient)
    broadcast_msg_id = bulletin_board.post_message(
        Message(
            content="Attention all agents: System maintenance scheduled for tonight",
            sender_id=agents[0]["id"],
            sender_name=agents[0]["name"],
            topic="announcements",
            tags=["maintenance", "system"]
        )
    )
    print(f"  Posted broadcast message (ID: {broadcast_msg_id})")
    
    # Direct message to a specific agent
    direct_msg_id = bulletin_board.post_message(
        Message(
            content="Please analyze dataset XYZ",
            sender_id=agents[0]["id"],
            sender_name=agents[0]["name"],
            recipient_id=agents[1]["id"],
            recipient_name=agents[1]["name"],
            topic="tasks",
            priority="high",
            tags=["dataset", "analysis"]
        )
    )
    print(f"  Posted direct message (ID: {direct_msg_id})")
    
    # Response message
    response_msg_id = bulletin_board.post_message(
        Message(
            content="Analysis of dataset XYZ completed, findings attached",
            sender_id=agents[1]["id"],
            sender_name=agents[1]["name"],
            recipient_id=agents[0]["id"],
            recipient_name=agents[0]["name"],
            topic="tasks",
            tags=["dataset", "analysis", "completed"]
        )
    )
    print(f"  Posted response message (ID: {response_msg_id})")
    
    # 2. Subscribe agents to topics
    print("\nSetting up topic subscriptions:")
    bulletin_board.subscribe(agents[1]["id"], ["announcements", "tasks"])
    print(f"  {agents[1]['name']} subscribed to: announcements, tasks")
    
    bulletin_board.subscribe(agents[2]["id"], ["announcements", "reports"])
    print(f"  {agents[2]['name']} subscribed to: announcements, reports")
    
    # 3. Wait for temporary message to expire
    print("\nWaiting for temporary message to expire...")
    time.sleep(1.5)  # Wait longer than the TTL
    
    # 4. Retrieve messages using different filters
    print("\nRetrieving messages (after TTL expiration):")
    
    # All messages
    all_messages = bulletin_board.get_messages()
    print(f"  Total messages in bulletin board: {len(all_messages)}")
    
    # Messages for a specific agent
    agent2_messages = bulletin_board.get_messages(agent_id=agents[1]["id"])
    print(f"  Messages for {agents[1]['name']}: {len(agent2_messages)}")
    
    # Messages for a specific topic
    task_messages = bulletin_board.get_messages(topics=["tasks"])
    print(f"  Messages with topic 'tasks': {len(task_messages)}")
    
    # Messages with specific tags
    completed_messages = bulletin_board.get_messages(tags=["completed"])
    print(f"  Messages tagged 'completed': {len(completed_messages)}")
    
    # Messages based on subscription
    agent2_subscribed = bulletin_board.get_subscribed_messages(agent_id=agents[1]["id"])
    print(f"  Subscribed messages for {agents[1]['name']}: {len(agent2_subscribed)}")
    
    # 5. Display some message details
    if completed_messages:
        msg = completed_messages[0]
        print("\nExample message content:")
        print(f"  From: {msg['sender']['name']} ({msg['sender']['id']})")
        if msg['recipient']:
            print(f"  To: {msg['recipient']['name']} ({msg['recipient']['id']})")
        else:
            print("  To: Broadcast (all agents)")
        print(f"  Topic: {msg['topic']}")
        print(f"  Tags: {', '.join(msg['metadata']['tags'])}")
        print(f"  Content: {msg['content']}")
    
    # 6. Unsubscribe agent
    print("\nUnsubscribing agent:")
    bulletin_board.unsubscribe(agents[1]["id"], ["announcements"])
    print(f"  {agents[1]['name']} unsubscribed from: announcements")
    
    # Verify subscription change
    agent2_subscribed_after = bulletin_board.get_subscribed_messages(agent_id=agents[1]["id"])
    print(f"  Subscribed messages for {agents[1]['name']} after unsubscribe: {len(agent2_subscribed_after)}")
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    try:
        test_bulletin_board()
    except Exception as e:
        print(f"\nError during test: {e}") 