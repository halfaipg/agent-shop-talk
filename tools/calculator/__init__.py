"""
Calculator tool initialization.

This module registers the calculator tool with the LLM Shop Talk system.
"""

import json
import os
from typing import Dict, Any

# Read tool metadata
with open(os.path.join(os.path.dirname(__file__), 'metadata.json'), 'r') as f:
    METADATA = json.load(f)

def get_metadata() -> Dict[str, Any]:
    """Get the tool metadata.
    
    Returns:
        The tool metadata as a dictionary
    """
    return METADATA

# Tool will be auto-discovered and registered by the tool registry system
print(f"Initializing {METADATA['name']} tool...") 