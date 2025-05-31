"""
Intent Detection Module for Multi-Agent AI System
Provides utilities for detecting document intent based on content.
"""

import re
from typing import Dict, List, Tuple, Optional, Any

# Define intent keywords for rule-based classification
INTENT_KEYWORDS = {
    "invoice": ["invoice", "payment", "bill", "amount due", "total", "tax", "paid", "payment terms"],
    "rfq": ["rfq", "request for quote", "quotation", "pricing", "quote", "proposal", "bid"],
    "complaint": ["complaint", "issue", "problem", "dissatisfied", "unhappy", "refund", "compensation"],
    "compliance": ["compliance", "regulation", "legal", "requirement", "policy", "standard", "certification"],
    "update": ["update", "status", "progress", "notification", "inform", "announcement"],
    "internal": ["internal", "team", "staff", "employee", "department", "confidential"]
}

def detect_intent_from_text(text: str) -> Tuple[str, float]:
    """
    Detect document intent from text using keyword matching
    
    Args:
        text: The document text content
        
    Returns:
        tuple: (intent_name, confidence_score)
    """
    text = text.lower()
    
    # Count keyword matches for each intent
    scores = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        count = 0
        for keyword in keywords:
            count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
        
        # Calculate a simple confidence score based on keyword density
        scores[intent] = count / (len(text.split()) + 0.001)  # Avoid division by zero
    
    # Find the intent with the highest score
    if not scores:
        return "unknown", 0.0
        
    best_intent = max(scores, key=scores.get)
    confidence = scores[best_intent]
    
    # If confidence is too low, return unknown
    if confidence < 0.01:
        return "unknown", confidence
        
    return best_intent, confidence

def detect_intent_from_json(json_data: Dict[str, Any]) -> Tuple[str, float]:
    """
    Detect document intent from JSON structure and content
    
    Args:
        json_data: The parsed JSON data
        
    Returns:
        tuple: (intent_name, confidence_score)
    """
    # Check for explicit type field
    if "type" in json_data and isinstance(json_data["type"], str):
        intent_type = json_data["type"].lower()
        for intent in INTENT_KEYWORDS:
            if intent in intent_type:
                return intent, 1.0
    
    # Convert JSON to text for keyword analysis
    text = ""
    for key, value in json_data.items():
        if isinstance(value, str):
            text += f"{key}: {value} "
        elif isinstance(value, (int, float)):
            text += f"{key}: {str(value)} "
    
    # Use text-based detection as fallback
    return detect_intent_from_text(text)

def detect_intent_from_email(subject: str, body: str) -> Tuple[str, float]:
    """
    Detect document intent from email subject and body
    
    Args:
        subject: Email subject line
        body: Email body text
        
    Returns:
        tuple: (intent_name, confidence_score)
    """
    # Subject line is weighted more heavily
    combined_text = subject + " " + subject + " " + body
    return detect_intent_from_text(combined_text)

# Optional: LLM-based intent detection (requires OpenAI API key)
"""
import os
import openai

def detect_intent_with_llm(text: str) -> Tuple[str, float]:
    '''
    Use OpenAI's API to detect document intent
    
    Args:
        text: The document text content
        
    Returns:
        tuple: (intent_name, confidence_score)
    '''
    try:
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI that categorizes document intent. "
                                             "Categorize the following text into one of these categories: "
                                             "invoice, rfq, complaint, compliance, update, internal, or unknown. "
                                             "Respond with only the category name and a confidence score from 0 to 1."},
                {"role": "user", "content": text[:1000]}  # Limit text length
            ],
            temperature=0.3,
            max_tokens=20
        )
        
        result = response.choices[0].message.content.strip().lower()
        
        # Parse the response
        parts = result.split()
        if len(parts) >= 1:
            intent = parts[0].strip()
            confidence = 0.8  # Default confidence
            
            # Try to extract confidence if provided
            if len(parts) >= 2:
                try:
                    confidence = float(parts[1])
                except ValueError:
                    pass
                    
            return intent, confidence
            
    except Exception as e:
        print(f"Error using LLM for intent detection: {e}")
    
    # Fallback to keyword-based detection
    return detect_intent_from_text(text)
"""
