
# Weather Tool
tool_info = {
    "name": "weather",
    "description": "A tool for getting weather information for a location",
    "version": "1.0.0",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location to get weather for (city, state, country)"
            },
            "units": {
                "type": "string",
                "enum": ["metric", "imperial"],
                "description": "The units to use for temperature (metric or imperial)",
                "default": "metric"
            }
        },
        "required": ["location"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location the weather is for"
            },
            "temperature": {
                "type": "number",
                "description": "The current temperature"
            },
            "conditions": {
                "type": "string",
                "description": "The current weather conditions"
            },
            "units": {
                "type": "string",
                "description": "The units used for temperature (C or F)"
            }
        }
    }
}

def tool_function(location, units="metric"):
    """Get weather information.
    
    Args:
        location: The location to get weather for
        units: The units to use for temperature
        
    Returns:
        Weather information
    """
    # This is a mock implementation - in a real tool, you would call a weather API
    import random
    
    # Random temperature based on units
    if units == "metric":
        temperature = round(random.uniform(0, 30), 1)
        units_label = "C"
    else:
        temperature = round(random.uniform(32, 90), 1)
        units_label = "F"
    
    # Random conditions
    conditions = random.choice([
        "Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Stormy", "Snowy", "Foggy", "Windy"
    ])
    
    return {
        "location": location,
        "temperature": temperature,
        "conditions": conditions,
        "units": units_label
    }
