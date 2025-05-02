
# Text Analysis Tool
tool_info = {
    "name": "text_analyzer",
    "description": "A tool for analyzing text, including word count, character count, and sentiment",
    "version": "1.0.0",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to analyze"
            },
            "analyze_sentiment": {
                "type": "boolean",
                "description": "Whether to analyze sentiment",
                "default": False
            }
        },
        "required": ["text"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "word_count": {
                "type": "integer",
                "description": "The number of words in the text"
            },
            "character_count": {
                "type": "integer",
                "description": "The number of characters in the text"
            },
            "sentiment": {
                "type": "string",
                "description": "The sentiment of the text (positive, neutral, or negative)",
                "enum": ["positive", "neutral", "negative"]
            }
        }
    }
}

def tool_function(text, analyze_sentiment=False):
    """Analyze text.
    
    Args:
        text: The text to analyze
        analyze_sentiment: Whether to analyze sentiment
        
    Returns:
        Analysis results
    """
    # Basic analysis
    result = {
        "word_count": len(text.split()),
        "character_count": len(text)
    }
    
    # Sentiment analysis (very simplistic)
    if analyze_sentiment:
        positive_words = ["good", "great", "excellent", "happy", "positive", "wonderful", "best", "love"]
        negative_words = ["bad", "terrible", "awful", "sad", "negative", "worst", "hate"]
        
        positive_count = sum(1 for word in text.lower().split() if word in positive_words)
        negative_count = sum(1 for word in text.lower().split() if word in negative_words)
        
        if positive_count > negative_count:
            result["sentiment"] = "positive"
        elif negative_count > positive_count:
            result["sentiment"] = "negative"
        else:
            result["sentiment"] = "neutral"
    
    return result
