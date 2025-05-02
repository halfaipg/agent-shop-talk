#!/usr/bin/env python3
"""
Test script for Agent Shop Talk A2A Bulletin Board with Ollama integration.
Demonstrates posting messages to the bulletin board and having an LLM process them.
"""

import asyncio
import json
import sys
import time
import requests
from typing import Dict, Any, List
import re

from src.a2a_bulletin_board import bulletin_board, Message


# Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"  # Using model available on the system
MAX_TOKENS = 1000


def call_ollama(prompt: str, system_prompt: str = None, model_name: str = MODEL_NAME) -> str:
    """Call Ollama API with the given prompt.
    
    Args:
        prompt: The user prompt to send to the model
        system_prompt: Optional system prompt for context
        model_name: The name of the model to use (defaults to MODEL_NAME)
        
    Returns:
        The model's response text
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "max_tokens": MAX_TOKENS
    }
    
    if system_prompt:
        payload["system"] = system_prompt
    
    try:
        print(f"Sending request to Ollama API: {OLLAMA_API_URL}")
        response = requests.post(OLLAMA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama: {e}")
        sys.exit(1)


def post_test_messages():
    """Post some test messages to the bulletin board.
    
    Returns:
        A list of message IDs
    """
    message_ids = []
    
    # Define some test agents
    agents = [
        {"id": "agent1", "name": "Data Collection Agent"},
        {"id": "agent2", "name": "Analysis Agent"},
        {"id": "agent3", "name": "Report Generation Agent"}
    ]
    
    # Post a status update message
    status_msg_id = bulletin_board.post_message(
        Message(
            content="Dataset XYZ has been collected and is ready for analysis. Location: /data/xyz/",
            sender_id=agents[0]["id"],
            sender_name=agents[0]["name"],
            topic="status_updates",
            tags=["dataset", "collection", "completed"]
        )
    )
    message_ids.append(status_msg_id)
    
    # Post a task message to a specific agent
    task_msg_id = bulletin_board.post_message(
        Message(
            content="Please analyze dataset XYZ for anomalies using regression model A.",
            sender_id=agents[0]["id"],
            sender_name=agents[0]["name"],
            recipient_id=agents[1]["id"],
            recipient_name=agents[1]["name"],
            topic="tasks",
            priority="high",
            tags=["dataset", "analysis", "request"]
        )
    )
    message_ids.append(task_msg_id)
    
    # Post a task completion message
    completion_msg_id = bulletin_board.post_message(
        Message(
            content={
                "status": "completed",
                "task": "analysis",
                "dataset": "XYZ",
                "findings": {
                    "anomalies_detected": 3,
                    "confidence_score": 0.92,
                    "recommendations": [
                        "Further investigate time periods 3-5",
                        "Clean outliers in section B",
                        "Consider model recalibration"
                    ]
                }
            },
            sender_id=agents[1]["id"],
            sender_name=agents[1]["name"],
            recipient_id=agents[0]["id"],
            recipient_name=agents[0]["name"],
            topic="task_completions",
            tags=["dataset", "analysis", "completed"]
        )
    )
    message_ids.append(completion_msg_id)
    
    return message_ids, agents


def create_message_description(messages: List[Dict[str, Any]]) -> str:
    """Create a description of the messages for the model.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        Formatted string describing the messages
    """
    description = "You are an agent monitoring the bulletin board and have received the following messages:\n\n"
    
    for i, msg in enumerate(messages):
        description += f"--- MESSAGE {i+1} ---\n"
        
        # Sender info
        description += f"From: {msg['sender']['name']} ({msg['sender']['id']})\n"
        
        # Recipient info
        if msg['recipient']:
            description += f"To: {msg['recipient']['name']} ({msg['recipient']['id']})\n"
        else:
            description += "To: BROADCAST (All Agents)\n"
        
        # Message details
        description += f"Topic: {msg['topic']}\n"
        description += f"Priority: {msg['metadata']['priority']}\n"
        description += f"Tags: {', '.join(msg['metadata']['tags'])}\n"
        description += f"Timestamp: {msg['metadata']['timestamp']}\n"
        
        # Content
        description += "Content:\n"
        if isinstance(msg['content'], dict):
            description += json.dumps(msg['content'], indent=2) + "\n"
        else:
            description += str(msg['content']) + "\n"
        
        description += "\n"
    
    return description


def extract_json_from_response(response: str) -> Dict[str, Any]:
    """Extract a JSON object from the LLM's response.
    
    Args:
        response: The model's response text
        
    Returns:
        Extracted JSON object or error message
    """
    # Look for JSON blocks in the markdown
    json_pattern = r"```(?:json)?\n([\s\S]*?)\n```"
    matches = re.findall(json_pattern, response)
    
    if matches:
        try:
            return json.loads(matches[0].strip())
        except json.JSONDecodeError:
            pass
    
    # Try to extract JSON directly
    try:
        json_pattern = r"({[\s\S]*?})"
        matches = re.findall(json_pattern, response)
        
        if matches:
            return json.loads(matches[0])
    except Exception:
        pass
    
    return {"error": "Could not extract JSON from response"}


def run_ollama_bulletin_board_test():
    """Run the Ollama A2A Bulletin Board integration test."""
    print("Agent Shop Talk - Ollama A2A Bulletin Board Test")
    print("-" * 60)
    
    # Check if Ollama is available
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if not response.ok:
            print("Error: Ollama API is not responding. Is Ollama running?")
            return
        
        available_models = [model.get("name") for model in response.json().get("models", [])]
        if not available_models:
            print("Error: No models found in Ollama. Please pull a model first.")
            return
        
        print(f"Available Ollama models: {', '.join(available_models)}")
        
        # Use the declared model or switch to available one if needed
        model_to_use = MODEL_NAME
        if MODEL_NAME not in available_models:
            print(f"Warning: Model {MODEL_NAME} not found in available models. Using {available_models[0]} instead.")
            model_to_use = available_models[0]
        else:
            print(f"Using model: {MODEL_NAME}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Ollama API. Is Ollama running on localhost:11434?")
        return
    
    # Post test messages to the bulletin board
    print("\nPosting test messages to the bulletin board...")
    message_ids, agents = post_test_messages()
    print(f"Posted {len(message_ids)} messages")
    
    # Setup subscriptions
    bulletin_board.subscribe(agents[2]["id"], ["status_updates", "task_completions"])
    print(f"Subscribed {agents[2]['name']} to: status_updates, task_completions")
    
    # Retrieve messages (including subscribed ones) for the report generation agent
    all_messages = bulletin_board.get_messages()
    subscribed_messages = bulletin_board.get_subscribed_messages(agents[2]["id"])
    
    print(f"Total messages in bulletin board: {len(all_messages)}")
    print(f"Messages for {agents[2]['name']} based on subscription: {len(subscribed_messages)}")
    
    # Scenario 1: Ask the model to process all messages
    message_description = create_message_description(all_messages)
    
    # System prompt
    system_prompt = (
        "You are an AI assistant working within a multi-agent system. "
        "You need to process messages from the bulletin board and summarize the current state of operations. "
        "Identify any tasks, their status, and provide a concise summary of the current situation."
    )
    
    # User prompt
    user_prompt = (
        "I need you to review these messages from our agent bulletin board and provide:\n"
        "1. A summary of the current situation\n"
        "2. Any pending tasks or actions needed\n"
        "3. Key findings or insights from the messages\n\n"
        "Please format your response as JSON with these three sections."
    )
    
    # Combine prompts
    full_prompt = f"{message_description}\n\n{user_prompt}"
    
    print("\nSending request to Ollama to process all messages...")
    print(f"Model: {model_to_use}")
    
    # Call Ollama
    model_response = call_ollama(full_prompt, system_prompt, model_to_use)
    print("\nModel response:")
    print("-" * 40)
    print(model_response)
    print("-" * 40)
    
    # Parse any JSON in the response
    extracted_json = extract_json_from_response(model_response)
    if "error" not in extracted_json:
        print("\nExtracted structured data:")
        print(json.dumps(extracted_json, indent=2))
    
    # Scenario 2: Have the model respond to a specific message
    if len(subscribed_messages) > 0:
        # Get the first message in the subscription
        specific_message = subscribed_messages[0]
        
        # Create a specific prompt
        specific_prompt = (
            f"As the {agents[2]['name']}, you received this message:\n\n"
            f"--- MESSAGE ---\n"
            f"From: {specific_message['sender']['name']} ({specific_message['sender']['id']})\n"
            f"Topic: {specific_message['topic']}\n"
            f"Tags: {', '.join(specific_message['metadata']['tags'])}\n"
            f"Content: {specific_message['content']}\n\n"
            f"Please draft a response to this message. If any action is required, specify what action you would take."
        )
        
        print("\nSending request to Ollama to respond to a specific message...")
        
        # Call Ollama for the second scenario
        response_msg = call_ollama(specific_prompt, system_prompt, model_to_use)
        print("\nModel's drafted response:")
        print("-" * 40)
        print(response_msg)
        print("-" * 40)
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    try:
        run_ollama_bulletin_board_test()
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {e}")
        sys.exit(1) 