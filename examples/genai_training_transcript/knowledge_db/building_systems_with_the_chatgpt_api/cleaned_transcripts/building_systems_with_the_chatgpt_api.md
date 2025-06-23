# Building Systems with the ChatGPT API - Smoke Test

## Introduction to the ChatGPT API

Welcome to Building Systems with the ChatGPT API. This module covers API fundamentals and practical implementation patterns for building ChatGPT-powered systems.

Modern AI applications require seamless integration with language models through well-designed APIs. Understanding how to effectively use the ChatGPT API is essential for building scalable AI systems.

## ChatGPT API Fundamentals

### Authentication and Setup

**API Key Management:**
```python
import openai
import os

class OpenAIClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        
    def test_connection(self):
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
```

### Basic API Usage

**Simple Chat Completion:**
```python
def simple_chat_completion(prompt: str):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"
```

## Function Calling

**Basic Function Implementation:**
```python
def get_weather(location: str):
    return f"Weather in {location}: 22°C, sunny"

functions = [{
    "name": "get_weather",
    "description": "Get weather for a location",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string"}
        }
    }
}]
```

This smoke test covers core API patterns and function calling basics for integration testing.