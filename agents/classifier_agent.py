"""
Classifier Agent Module for Multi-Agent AI System
Responsible for detecting document format and intent, then routing to appropriate agent.
"""

import os
import sys
from typing import Dict, Any, Tuple, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.parser_utils import detect_file_format, extract_text_from_pdf, parse_json_file, parse_email
from utils.intent_detection import detect_intent_from_text, detect_intent_from_json, detect_intent_from_email
from memory.shared_memory import SharedMemory

class ClassifierAgent:
    """
    Agent responsible for classifying document format and intent,
    then routing to appropriate specialized agent.
    """
    
    def __init__(self, memory: SharedMemory):
        """
        Initialize the classifier agent
        
        Args:
            memory: Shared memory instance for logging and context
        """
        self.memory = memory
        self.supported_formats = ['pdf', 'json', 'email']
    
    def process(self, file_path: str) -> Dict[str, Any]:
        """
        Process an input file and route to appropriate agent
        
        Args:
            file_path: Path to the input file
            
        Returns:
            dict: Processing result with format, intent, and routing info
        """
        # Detect file format
        format_type = detect_file_format(file_path)
        
        if format_type not in self.supported_formats:
            return {
                'status': 'error',
                'message': f'Unsupported file format: {format_type}',
                'format': format_type
            }
        
        # Extract content based on format
        content = None
        if format_type == 'pdf':
            text_content = extract_text_from_pdf(file_path)
            intent, confidence = detect_intent_from_text(text_content)
            content = {'text': text_content}
        elif format_type == 'json':
            json_content = parse_json_file(file_path)
            intent, confidence = detect_intent_from_json(json_content)
            content = json_content
        elif format_type == 'email':
            email_content = parse_email(file_path)
            intent, confidence = detect_intent_from_email(
                email_content.get('subject', ''), 
                email_content.get('body', '')
            )
            content = email_content
        
        # Create memory thread
        thread_id = self.memory.create_thread(
            input_source=file_path,
            format_type=format_type,
            intent=intent
        )
        
        # Log classification result
        self.memory.update_metadata(thread_id, {
            'confidence': confidence,
            'content_sample': str(content)[:200] if content else None  # Store a sample of content
        })
        
        # Determine target agent based on format
        target_agent = 'json_agent' if format_type == 'json' else 'email_agent'
        
        # Log routing decision
        self.memory.log_routing(
            thread_id=thread_id,
            from_agent='classifier_agent',
            to_agent=target_agent,
            reason=f"Detected format: {format_type}, intent: {intent} with confidence: {confidence:.2f}"
        )
        
        # Return classification result
        return {
            'status': 'success',
            'thread_id': thread_id,
            'format': format_type,
            'intent': intent,
            'confidence': confidence,
            'target_agent': target_agent,
            'content': content
        }
