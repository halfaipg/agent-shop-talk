#!/usr/bin/env python3
"""
Work Log module for Agent Shop Talk.
Tracks tool actions and completed tasks from the bulletin board.
"""

import time
import uuid
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum


class LogEntryType(Enum):
    """Types of log entries."""
    TOOL_EXECUTION = "tool_execution"
    TASK_COMPLETION = "task_completion"
    SYSTEM_EVENT = "system_event"
    AGENT_COMMUNICATION = "agent_communication"


@dataclass
class LogEntry:
    """Represents a single log entry in the work log."""
    entry_type: LogEntryType
    agent_id: str
    agent_name: str
    action: str
    details: Dict[str, Any]
    status: str = "success"  # success, failure, pending
    error_message: Optional[str] = None
    related_message_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the log entry to a dictionary format."""
        result = asdict(self)
        result["entry_type"] = self.entry_type.value
        result["timestamp_iso"] = datetime.fromtimestamp(result["timestamp"]).isoformat()
        return result


class WorkLog:
    """Work log for tracking agent activities and tool executions."""
    
    def __init__(self):
        """Initialize an empty work log."""
        self._entries: Dict[str, LogEntry] = {}  # Entry ID -> LogEntry
    
    def log_tool_execution(self, 
                          agent_id: str,
                          agent_name: str,
                          tool_name: str,
                          parameters: Dict[str, Any],
                          result: Any,
                          status: str = "success",
                          error_message: Optional[str] = None,
                          related_message_id: Optional[str] = None) -> str:
        """Log a tool execution.
        
        Args:
            agent_id: ID of the agent that executed the tool
            agent_name: Name of the agent that executed the tool
            tool_name: Name of the tool that was executed
            parameters: Parameters passed to the tool
            result: Result returned by the tool
            status: Execution status (success, failure, pending)
            error_message: Error message if the execution failed
            related_message_id: ID of a related message in the bulletin board
            
        Returns:
            The ID of the created log entry
        """
        entry = LogEntry(
            entry_type=LogEntryType.TOOL_EXECUTION,
            agent_id=agent_id,
            agent_name=agent_name,
            action=f"Execute tool: {tool_name}",
            details={
                "tool_name": tool_name,
                "parameters": parameters,
                "result": result
            },
            status=status,
            error_message=error_message,
            related_message_id=related_message_id
        )
        
        self._entries[entry.id] = entry
        return entry.id
    
    def log_task_completion(self,
                           agent_id: str,
                           agent_name: str,
                           task_name: str,
                           task_details: Dict[str, Any],
                           message_id: str,
                           status: str = "success",
                           error_message: Optional[str] = None) -> str:
        """Log a task completion.
        
        Args:
            agent_id: ID of the agent that completed the task
            agent_name: Name of the agent that completed the task
            task_name: Name of the task that was completed
            task_details: Details about the task completion
            message_id: ID of the related task message in the bulletin board
            status: Completion status (success, failure, pending)
            error_message: Error message if the task failed
            
        Returns:
            The ID of the created log entry
        """
        entry = LogEntry(
            entry_type=LogEntryType.TASK_COMPLETION,
            agent_id=agent_id,
            agent_name=agent_name,
            action=f"Complete task: {task_name}",
            details=task_details,
            status=status,
            error_message=error_message,
            related_message_id=message_id
        )
        
        self._entries[entry.id] = entry
        return entry.id
    
    def log_system_event(self,
                        event_name: str,
                        details: Dict[str, Any],
                        agent_id: Optional[str] = None,
                        agent_name: Optional[str] = None,
                        status: str = "success",
                        error_message: Optional[str] = None) -> str:
        """Log a system event.
        
        Args:
            event_name: Name of the event
            details: Details about the event
            agent_id: Optional ID of the agent related to the event
            agent_name: Optional name of the agent related to the event
            status: Event status (success, failure, pending)
            error_message: Error message if the event failed
            
        Returns:
            The ID of the created log entry
        """
        entry = LogEntry(
            entry_type=LogEntryType.SYSTEM_EVENT,
            agent_id=agent_id or "system",
            agent_name=agent_name or "System",
            action=f"System event: {event_name}",
            details=details,
            status=status,
            error_message=error_message
        )
        
        self._entries[entry.id] = entry
        return entry.id
    
    def log_agent_communication(self,
                              sender_id: str,
                              sender_name: str,
                              recipient_id: Optional[str],
                              recipient_name: Optional[str],
                              message_type: str,
                              message_content: Union[str, Dict[str, Any]],
                              message_id: str) -> str:
        """Log an agent communication event.
        
        Args:
            sender_id: ID of the sender agent
            sender_name: Name of the sender agent
            recipient_id: ID of the recipient agent (None for broadcast)
            recipient_name: Name of the recipient agent (None for broadcast)
            message_type: Type of message (e.g., "request", "response", "notification")
            message_content: Content of the message
            message_id: ID of the message in the bulletin board
            
        Returns:
            The ID of the created log entry
        """
        recipient_desc = f" to {recipient_name}" if recipient_name else " (broadcast)"
        
        entry = LogEntry(
            entry_type=LogEntryType.AGENT_COMMUNICATION,
            agent_id=sender_id,
            agent_name=sender_name,
            action=f"Send {message_type}{recipient_desc}",
            details={
                "sender": {
                    "id": sender_id,
                    "name": sender_name
                },
                "recipient": {
                    "id": recipient_id,
                    "name": recipient_name
                } if recipient_id else None,
                "message_type": message_type,
                "content": message_content
            },
            status="success",
            related_message_id=message_id
        )
        
        self._entries[entry.id] = entry
        return entry.id
    
    def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific log entry by ID.
        
        Args:
            entry_id: The ID of the log entry to retrieve
            
        Returns:
            The log entry as a dictionary, or None if not found
        """
        entry = self._entries.get(entry_id)
        return entry.to_dict() if entry else None
    
    def get_entries(self,
                   limit: int = 100,
                   entry_type: Optional[LogEntryType] = None,
                   agent_id: Optional[str] = None,
                   status: Optional[str] = None,
                   related_message_id: Optional[str] = None,
                   since_timestamp: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get log entries with optional filtering.
        
        Args:
            limit: Maximum number of entries to return
            entry_type: Filter by entry type
            agent_id: Filter by agent ID
            status: Filter by status
            related_message_id: Filter by related message ID
            since_timestamp: Filter entries newer than this timestamp
            
        Returns:
            List of log entries as dictionaries, sorted by timestamp (newest first)
        """
        entries = list(self._entries.values())
        
        # Apply filters
        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]
        
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]
        
        if status:
            entries = [e for e in entries if e.status == status]
        
        if related_message_id:
            entries = [e for e in entries if e.related_message_id == related_message_id]
        
        if since_timestamp:
            entries = [e for e in entries if e.timestamp > since_timestamp]
        
        # Sort by timestamp (newest first)
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Limit results and convert to dictionaries
        return [e.to_dict() for e in entries[:limit]]
    
    def get_tool_executions(self,
                           tool_name: Optional[str] = None,
                           agent_id: Optional[str] = None,
                           status: Optional[str] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Get tool execution log entries with optional filtering.
        
        Args:
            tool_name: Filter by tool name
            agent_id: Filter by agent ID
            status: Filter by status
            limit: Maximum number of entries to return
            
        Returns:
            List of tool execution log entries as dictionaries
        """
        entries = self.get_entries(
            limit=limit,
            entry_type=LogEntryType.TOOL_EXECUTION,
            agent_id=agent_id,
            status=status
        )
        
        if tool_name:
            entries = [e for e in entries if e["details"]["tool_name"] == tool_name]
        
        return entries
    
    def get_task_completions(self,
                            task_name: Optional[str] = None,
                            agent_id: Optional[str] = None,
                            status: Optional[str] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get task completion log entries with optional filtering.
        
        Args:
            task_name: Filter by task name
            agent_id: Filter by agent ID
            status: Filter by status
            limit: Maximum number of entries to return
            
        Returns:
            List of task completion log entries as dictionaries
        """
        entries = self.get_entries(
            limit=limit,
            entry_type=LogEntryType.TASK_COMPLETION,
            agent_id=agent_id,
            status=status
        )
        
        if task_name:
            entries = [e for e in entries if task_name in e["action"]]
        
        return entries
    
    def export_log(self, 
                  format_type: str = "json", 
                  file_path: Optional[str] = None) -> Optional[str]:
        """Export the work log in various formats.
        
        Args:
            format_type: Export format ("json", "csv", "txt")
            file_path: Path to save the export to
            
        Returns:
            The exported data as a string if file_path is None, otherwise None
        """
        entries = [e.to_dict() for e in self._entries.values()]
        entries.sort(key=lambda e: e["timestamp"])
        
        if format_type == "json":
            output = json.dumps(entries, indent=2)
        elif format_type == "csv":
            # Simple CSV format
            header = "ID,Type,Agent,Action,Status,Timestamp,Related Message\n"
            rows = []
            for entry in entries:
                row = (
                    f"{entry['id']},{entry['entry_type']},{entry['agent_name']},"
                    f"\"{entry['action']}\",{entry['status']},{entry['timestamp_iso']},"
                    f"{entry['related_message_id'] or ''}"
                )
                rows.append(row)
            output = header + "\n".join(rows)
        elif format_type == "txt":
            # Human-readable text format
            lines = []
            for entry in entries:
                time_str = entry["timestamp_iso"]
                lines.append(f"[{time_str}] {entry['agent_name']}: {entry['action']} - {entry['status']}")
                if entry["error_message"]:
                    lines.append(f"  Error: {entry['error_message']}")
                if entry["details"]:
                    details_str = json.dumps(entry["details"], indent=2)
                    indented_details = "\n".join(f"  {line}" for line in details_str.split("\n"))
                    lines.append(f"  Details:\n{indented_details}")
                lines.append("")  # Empty line between entries
            output = "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
        
        if file_path:
            with open(file_path, "w") as file:
                file.write(output)
            return None
        else:
            return output
    
    def clear(self) -> None:
        """Clear all entries from the work log."""
        self._entries.clear()


# Create a global work log instance
work_log = WorkLog() 