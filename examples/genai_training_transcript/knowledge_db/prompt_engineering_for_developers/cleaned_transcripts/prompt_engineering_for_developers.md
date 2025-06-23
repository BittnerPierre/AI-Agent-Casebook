# Prompt Engineering for Developers - Smoke Test

## Introduction to Prompt Engineering

Welcome to prompt engineering for developers. This module explores fundamental techniques for designing and optimizing text inputs to elicit desired responses from language models.

Prompt engineering is essential for building production-ready AI systems that behave predictably and effectively.

## System vs User Prompts

### System Prompts

System prompts establish context and behavioral guidelines for AI assistants.

**Example System Prompt:**
```
You are a helpful coding assistant specialized in Python development. You provide clear, well-commented code examples and explain complex concepts in simple terms.
```

System prompts are powerful because they:
- Set overall tone and personality
- Define expertise areas and limitations
- Establish response format preferences

### User Prompts

User prompts contain the actual task or question. They should be clear, specific, and provide necessary context.

**Example User Prompt:**
```
Write a Python function that calculates the moving average of a list of numbers with a configurable window size. Include error handling for edge cases.
```

## Zero-Shot and Few-Shot Techniques

### Zero-Shot Prompting

Zero-shot prompting relies on the model's pre-trained knowledge without providing examples.

**Example Zero-Shot Prompt:**
```
Classify the sentiment of this customer review as positive, negative, or neutral:
"The product arrived quickly but the quality was disappointing."
```

### Few-Shot Prompting

Few-shot prompting provides examples to guide the model's understanding.

**Example Few-Shot Prompt:**
```
Classify sentiment (positive/negative/neutral):

Review: "Great product, fast shipping!" → positive
Review: "Poor quality, wouldn't recommend." → negative
Review: "It's okay, nothing special." → neutral
Review: "Excellent value for money!" → ?
```

## Chain-of-Thought Prompting

**Basic Chain-of-Thought:**
```
Problem: If a train travels 120 miles in 2 hours, what's its average speed?

Let me think step by step:
1. Speed = Distance ÷ Time
2. Distance = 120 miles
3. Time = 2 hours
4. Speed = 120 ÷ 2 = 60 mph
```

## Implementation Example

```python
import openai

def classify_sentiment(text, examples=None):
    if examples:
        prompt = f"Examples:\n{examples}\n\nClassify: {text}"  
    else:
        prompt = f"Classify sentiment (positive/negative/neutral): {text}"
    return prompt
```

## Best Practices

1. **Be Specific**: Vague prompts lead to unpredictable outputs
2. **Provide Context**: Include relevant background information
3. **Set Expectations**: Specify desired format, length, or style
4. **Use Examples**: Show the model what good output looks like

This smoke test covers fundamental prompt engineering patterns for development.