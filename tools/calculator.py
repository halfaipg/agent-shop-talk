
# Calculator Tool
tool_info = {
    "name": "calculator",
    "description": "A simple calculator that can perform basic arithmetic operations",
    "version": "1.0.0",
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
                "description": "The arithmetic operation to perform"
            },
            "a": {
                "type": "number",
                "description": "The first operand"
            },
            "b": {
                "type": "number",
                "description": "The second operand"
            }
        },
        "required": ["operation", "a", "b"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "result": {
                "type": "number",
                "description": "The result of the arithmetic operation"
            }
        }
    }
}

def tool_function(operation, a, b):
    """Perform an arithmetic operation.
    
    Args:
        operation: The arithmetic operation to perform
        a: The first operand
        b: The second operand
        
    Returns:
        The result of the operation
    """
    if operation == "add":
        return {"result": a + b}
    elif operation == "subtract":
        return {"result": a - b}
    elif operation == "multiply":
        return {"result": a * b}
    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return {"result": a / b}
    else:
        raise ValueError(f"Unknown operation: {operation}")
