#!/usr/bin/env python3
"""
Test script for Agent Shop Talk Work Log.
Demonstrates logging tool executions and task completions from the bulletin board.
"""

import sys
import json
import time
import uuid
import random
from typing import Dict, Any

from src.a2a_bulletin_board import bulletin_board, Message
from src.work_log import work_log, LogEntryType


class MockTool:
    """A mock tool for testing."""
    
    def __init__(self, name: str, failure_rate: float = 0.0):
        """Initialize a mock tool.
        
        Args:
            name: Name of the tool
            failure_rate: Probability of tool execution failure (0.0 to 1.0)
        """
        self.name = name
        self.failure_rate = failure_rate
    
    def execute(self, **parameters) -> Dict[str, Any]:
        """Execute the tool with the given parameters.
        
        Args:
            **parameters: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            Exception: If the tool execution fails (based on failure_rate)
        """
        # Simulate random failure
        if random.random() < self.failure_rate:
            raise Exception(f"Tool {self.name} execution failed")
        
        # Simulate successful execution
        result = {
            "tool_name": self.name,
            "parameters_received": parameters,
            "execution_id": str(uuid.uuid4()),
            "success": True
        }
        
        # Add tool-specific result data
        if self.name == "data_processor":
            result["processed_records"] = random.randint(10, 100)
            result["execution_time_ms"] = random.randint(50, 500)
        elif self.name == "file_uploader":
            result["uploaded_file"] = parameters.get("file_path", "unknown.txt")
            result["destination"] = parameters.get("destination", "default")
            result["bytes_transferred"] = random.randint(1024, 10240)
        elif self.name == "text_analyzer":
            result["sentiment"] = random.choice(["positive", "neutral", "negative"])
            result["entities"] = random.randint(0, 10)
            result["language"] = "en"
        
        return result


def run_tool_execution_test():
    """Test logging tool executions."""
    print("\n--- Tool Execution Logging Test ---")
    
    # Create some mock tools
    tools = {
        "data_processor": MockTool("data_processor", failure_rate=0.2),
        "file_uploader": MockTool("file_uploader", failure_rate=0.1),
        "text_analyzer": MockTool("text_analyzer", failure_rate=0.0)
    }
    
    # Create some test agents
    agents = [
        {"id": "agent1", "name": "Data Processing Agent"},
        {"id": "agent2", "name": "File Management Agent"},
        {"id": "agent3", "name": "Text Analysis Agent"}
    ]
    
    # Execute tools and log the executions
    num_executions = 5
    print(f"Executing {num_executions} random tool operations...")
    
    for i in range(num_executions):
        # Select random agent and tool
        agent = random.choice(agents)
        tool_name = random.choice(list(tools.keys()))
        tool = tools[tool_name]
        
        # Generate random parameters
        parameters = {}
        if tool_name == "data_processor":
            parameters = {
                "data_source": f"source_{random.randint(1, 5)}",
                "batch_size": random.randint(10, 50),
                "process_type": random.choice(["analyze", "transform", "aggregate"])
            }
        elif tool_name == "file_uploader":
            parameters = {
                "file_path": f"/path/to/file_{random.randint(1, 100)}.txt",
                "destination": random.choice(["s3", "gcs", "local"]),
                "compress": random.choice([True, False])
            }
        elif tool_name == "text_analyzer":
            parameters = {
                "text": f"Sample text {i} for analysis with varying length and content.",
                "analyze_sentiment": random.choice([True, False]),
                "extract_entities": random.choice([True, False])
            }
        
        print(f"  Agent {agent['name']} executing {tool_name}...")
        
        try:
            # Execute the tool
            result = tool.execute(**parameters)
            
            # Log successful execution
            log_id = work_log.log_tool_execution(
                agent_id=agent["id"],
                agent_name=agent["name"],
                tool_name=tool_name,
                parameters=parameters,
                result=result,
                status="success"
            )
            
            print(f"    Success - Log entry: {log_id}")
            
        except Exception as e:
            # Log failed execution
            log_id = work_log.log_tool_execution(
                agent_id=agent["id"],
                agent_name=agent["name"],
                tool_name=tool_name,
                parameters=parameters,
                result=None,
                status="failure",
                error_message=str(e)
            )
            
            print(f"    Failure - Log entry: {log_id}")
    
    # Retrieve and display the tool execution logs
    tool_logs = work_log.get_tool_executions(limit=10)
    print(f"\nRetrieved {len(tool_logs)} tool execution logs")
    
    # Display successful vs. failed executions
    successful = [log for log in tool_logs if log["status"] == "success"]
    failed = [log for log in tool_logs if log["status"] == "failure"]
    
    print(f"  Successful executions: {len(successful)}")
    print(f"  Failed executions: {len(failed)}")
    
    # Display most recent execution
    if tool_logs:
        most_recent = tool_logs[0]
        print("\nMost recent tool execution:")
        print(f"  Agent: {most_recent['agent_name']}")
        print(f"  Action: {most_recent['action']}")
        print(f"  Tool: {most_recent['details']['tool_name']}")
        print(f"  Status: {most_recent['status']}")
        if most_recent["error_message"]:
            print(f"  Error: {most_recent['error_message']}")
        print(f"  Time: {most_recent['timestamp_iso']}")


def run_bulletin_board_task_test():
    """Test logging task completions from the bulletin board."""
    print("\n--- Bulletin Board Task Completion Logging Test ---")
    
    # Clear the bulletin board to start fresh
    bulletin_board.clear()
    
    # Create some test agents
    agents = [
        {"id": "agent1", "name": "Task Manager Agent"},
        {"id": "agent2", "name": "Worker Agent"},
        {"id": "agent3", "name": "Supervisor Agent"}
    ]
    
    # Post some task messages to the bulletin board
    print("Posting task messages to the bulletin board...")
    
    task_ids = []
    for i in range(3):
        task_name = f"Task-{i+1}"
        
        # Post task request
        msg = Message(
            content=f"Please complete {task_name} with priority {random.choice(['high', 'medium', 'low'])}",
            sender_id=agents[0]["id"],
            sender_name=agents[0]["name"],
            recipient_id=agents[1]["id"],
            recipient_name=agents[1]["name"],
            topic="tasks",
            priority=random.choice(["high", "normal", "low"]),
            tags=["task", f"task-{i+1}", random.choice(["analysis", "processing", "reporting"])]
        )
        
        message_id = bulletin_board.post_message(msg)
        task_ids.append((message_id, task_name))
        
        # Log the communication
        work_log.log_agent_communication(
            sender_id=agents[0]["id"],
            sender_name=agents[0]["name"],
            recipient_id=agents[1]["id"],
            recipient_name=agents[1]["name"],
            message_type="task_request",
            message_content=msg.content,
            message_id=message_id
        )
        
        print(f"  Posted {task_name} - Message ID: {message_id}")
    
    # Complete the tasks and log the completions
    print("\nCompleting tasks and logging completions...")
    
    for message_id, task_name in task_ids:
        # Simulate task completion (some succeed, some fail)
        success = random.random() > 0.3
        status = "success" if success else "failure"
        error_message = None if success else f"Failed to complete {task_name} due to resource constraints."
        
        # Create completion details
        completion_details = {
            "task_name": task_name,
            "completion_time": random.randint(5, 30),
            "resources_used": random.randint(1, 5),
            "outputs": {
                "files_created": random.randint(0, 3),
                "records_processed": random.randint(10, 100)
            }
        }
        
        if not success:
            completion_details["error"] = error_message
        
        # Create a completion message
        completion_msg = Message(
            content=completion_details,
            sender_id=agents[1]["id"],
            sender_name=agents[1]["name"],
            recipient_id=agents[0]["id"],
            recipient_name=agents[0]["name"],
            topic="task_completions",
            priority="normal",
            tags=["task", task_name, "completed" if success else "failed"]
        )
        
        # Post the completion message
        completion_id = bulletin_board.post_message(completion_msg)
        
        # Log the task completion
        log_id = work_log.log_task_completion(
            agent_id=agents[1]["id"],
            agent_name=agents[1]["name"],
            task_name=task_name,
            task_details=completion_details,
            message_id=completion_id,
            status=status,
            error_message=error_message
        )
        
        # Log the communication
        work_log.log_agent_communication(
            sender_id=agents[1]["id"],
            sender_name=agents[1]["name"],
            recipient_id=agents[0]["id"],
            recipient_name=agents[0]["name"],
            message_type="task_completion",
            message_content=completion_details,
            message_id=completion_id
        )
        
        print(f"  Completed {task_name} - Status: {status} - Log ID: {log_id}")
    
    # Retrieve and display task completion logs
    task_logs = work_log.get_task_completions(limit=10)
    print(f"\nRetrieved {len(task_logs)} task completion logs")
    
    # Display successful vs. failed completions
    successful = [log for log in task_logs if log["status"] == "success"]
    failed = [log for log in task_logs if log["status"] == "failure"]
    
    print(f"  Successful completions: {len(successful)}")
    print(f"  Failed completions: {len(failed)}")
    
    # Display most recent completion
    if task_logs:
        most_recent = task_logs[0]
        print("\nMost recent task completion:")
        print(f"  Agent: {most_recent['agent_name']}")
        print(f"  Action: {most_recent['action']}")
        print(f"  Status: {most_recent['status']}")
        if most_recent["error_message"]:
            print(f"  Error: {most_recent['error_message']}")
        print(f"  Time: {most_recent['timestamp_iso']}")
        print(f"  Related message: {most_recent['related_message_id']}")


def run_work_log_export_test():
    """Test exporting the work log."""
    print("\n--- Work Log Export Test ---")
    
    # Export to different formats
    formats = ["json", "csv", "txt"]
    
    for format_type in formats:
        print(f"Exporting work log to {format_type} format...")
        output = work_log.export_log(format_type=format_type)
        
        # Print a sample of the output
        if output:
            sample_length = min(200, len(output))
            print(f"  Sample of {format_type} output:")
            print(f"  {output[:sample_length]}...")
            print(f"  Total output size: {len(output)} bytes")
        
        # Save to file (optional)
        # work_log.export_log(format_type=format_type, file_path=f"work_log.{format_type}")


def run_work_log_test():
    """Run the work log test."""
    print("Agent Shop Talk - Work Log Test")
    print("=" * 60)
    
    # Clear work log
    work_log.clear()
    
    # Run tests
    run_tool_execution_test()
    run_bulletin_board_task_test()
    run_work_log_export_test()
    
    # Summary
    all_entries = work_log.get_entries()
    entry_types = {}
    
    for entry in all_entries:
        entry_type = entry["entry_type"]
        if entry_type not in entry_types:
            entry_types[entry_type] = 0
        entry_types[entry_type] += 1
    
    print("\n--- Work Log Summary ---")
    print(f"Total entries: {len(all_entries)}")
    print("Entry types:")
    for entry_type, count in entry_types.items():
        print(f"  {entry_type}: {count}")
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    try:
        run_work_log_test()
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {e}")
        sys.exit(1) 