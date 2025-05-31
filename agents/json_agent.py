"""
JSON Agent Module for Multi-Agent AI System
Responsible for processing JSON documents, validating against schemas, and extracting information.
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from jsonschema import validate, ValidationError, Draft7Validator

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.shared_memory import SharedMemory

class JSONAgent:
    """
    Agent responsible for processing JSON documents,
    validating against schemas, and extracting structured information.
    """
    
    def __init__(self, memory: SharedMemory, schemas_dir: str = None):
        """
        Initialize the JSON agent
        
        Args:
            memory: Shared memory instance for logging and context
            schemas_dir: Directory containing JSON schemas (optional)
        """
        self.memory = memory
        self.schemas_dir = schemas_dir
        self.schemas = {}
        
        # Load schemas if directory is provided
        if schemas_dir and os.path.isdir(schemas_dir):
            self._load_schemas()
        else:
            # Default schemas for common document types
            self._initialize_default_schemas()
    
    def _load_schemas(self):
        """Load JSON schemas from schemas directory"""
        for filename in os.listdir(self.schemas_dir):
            if filename.endswith('.json'):
                schema_name = os.path.splitext(filename)[0]
                schema_path = os.path.join(self.schemas_dir, filename)
                
                try:
                    with open(schema_path, 'r') as f:
                        self.schemas[schema_name] = json.load(f)
                except Exception as e:
                    print(f"Error loading schema {schema_name}: {e}")
    
    def _initialize_default_schemas(self):
        """Initialize default schemas for common document types"""
        # Invoice schema
        self.schemas['invoice'] = {
            "type": "object",
            "required": ["invoice_number", "date", "total_amount"],
            "properties": {
                "invoice_number": {"type": "string"},
                "date": {"type": "string"},
                "total_amount": {"type": ["number", "string"]},
                "currency": {"type": "string"},
                "vendor": {"type": "object"},
                "customer": {"type": "object"},
                "items": {"type": "array"},
                "payment_terms": {"type": "string"}
            }
        }
        
        # RFQ schema
        self.schemas['rfq'] = {
            "type": "object",
            "required": ["rfq_number", "date", "items"],
            "properties": {
                "rfq_number": {"type": "string"},
                "date": {"type": "string"},
                "customer": {"type": "object"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["description", "quantity"],
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": ["number", "string"]},
                            "unit": {"type": "string"}
                        }
                    }
                },
                "delivery_date": {"type": "string"},
                "contact_person": {"type": "string"}
            }
        }
        
        # Complaint schema
        self.schemas['complaint'] = {
            "type": "object",
            "required": ["type", "customer_id", "message"],
            "properties": {
                "type": {"type": "string"},
                "customer_id": {"type": "string"},
                "message": {"type": "string"},
                "severity": {"type": "string"},
                "category": {"type": "string"},
                "date": {"type": "string"}
            }
        }
    
    def process(self, thread_id: str, json_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a JSON document
        
        Args:
            thread_id: The thread ID from the classifier agent
            json_content: Parsed JSON content
            
        Returns:
            dict: Processing result with validation status and extracted information
        """
        # Log start of processing
        self.memory.update_status(thread_id, "processing_json")
        
        # Get intent from thread info
        thread_info = self.memory.get_thread_info(thread_id)
        intent = thread_info.get('intent', 'unknown')
        
        # Validate against schema if available
        validation_result = self._validate_json(json_content, intent)
        
        # Store validation result
        self.memory.store_extracted_field(thread_id, 'validation_result', validation_result)
        
        # Extract essential fields
        extracted_fields = self._extract_fields(json_content, intent)
        
        # Store extracted fields
        for field_name, field_value in extracted_fields.items():
            self.memory.store_extracted_field(thread_id, field_name, field_value)
        
        # Check for missing or anomalous fields
        missing_fields, anomalous_fields = self._check_data_quality(json_content, intent)
        
        # Store data quality issues
        if missing_fields:
            self.memory.store_extracted_field(thread_id, 'missing_fields', missing_fields)
        
        if anomalous_fields:
            self.memory.store_extracted_field(thread_id, 'anomalous_fields', anomalous_fields)
        
        # Update status to completed
        self.memory.update_status(thread_id, "completed")
        
        # Return processing result
        return {
            'status': 'success',
            'thread_id': thread_id,
            'validation': validation_result,
            'extracted_fields': extracted_fields,
            'data_quality': {
                'missing_fields': missing_fields,
                'anomalous_fields': anomalous_fields
            }
        }
    
    def _validate_json(self, json_content: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """
        Validate JSON against schema for the given intent
        
        Returns:
            dict: Validation result with status and errors
        """
        # Check if we have a schema for this intent
        if intent in self.schemas:
            schema = self.schemas[intent]
            validator = Draft7Validator(schema)
            errors = list(validator.iter_errors(json_content))
            
            if errors:
                # Format validation errors
                formatted_errors = []
                for error in errors:
                    formatted_errors.append({
                        'path': '.'.join(str(p) for p in error.path) if error.path else 'root',
                        'message': error.message
                    })
                
                return {
                    'valid': False,
                    'schema': intent,
                    'errors': formatted_errors
                }
            else:
                return {
                    'valid': True,
                    'schema': intent,
                    'errors': []
                }
        else:
            # No schema available, can't validate
            return {
                'valid': None,
                'schema': None,
                'message': f"No schema available for intent: {intent}"
            }
    
    def _extract_fields(self, json_content: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """
        Extract essential fields based on intent
        
        Returns:
            dict: Extracted fields
        """
        extracted = {}
        
        # Common fields to extract for all intents
        if 'id' in json_content:
            extracted['id'] = json_content['id']
        
        if 'date' in json_content:
            extracted['date'] = json_content['date']
        
        if 'type' in json_content:
            extracted['type'] = json_content['type']
        
        # Intent-specific field extraction
        if intent == 'invoice':
            # Extract invoice-specific fields
            for field in ['invoice_number', 'total_amount', 'currency', 'payment_terms']:
                if field in json_content:
                    extracted[field] = json_content[field]
            
            # Extract vendor and customer info
            if 'vendor' in json_content and isinstance(json_content['vendor'], dict):
                extracted['vendor_name'] = json_content['vendor'].get('name')
            
            if 'customer' in json_content and isinstance(json_content['customer'], dict):
                extracted['customer_name'] = json_content['customer'].get('name')
            
            # Extract items count if available
            if 'items' in json_content and isinstance(json_content['items'], list):
                extracted['items_count'] = len(json_content['items'])
                extracted['items_total'] = sum(
                    item.get('amount', 0) for item in json_content['items'] 
                    if isinstance(item, dict) and 'amount' in item
                )
        
        elif intent == 'rfq':
            # Extract RFQ-specific fields
            for field in ['rfq_number', 'delivery_date', 'contact_person']:
                if field in json_content:
                    extracted[field] = json_content[field]
            
            # Extract customer info
            if 'customer' in json_content and isinstance(json_content['customer'], dict):
                extracted['customer_name'] = json_content['customer'].get('name')
            
            # Extract items information
            if 'items' in json_content and isinstance(json_content['items'], list):
                extracted['items_count'] = len(json_content['items'])
                extracted['items_summary'] = [
                    item.get('description', 'Unknown item') 
                    for item in json_content['items'] 
                    if isinstance(item, dict)
                ]
        
        elif intent == 'complaint':
            # Extract complaint-specific fields
            for field in ['customer_id', 'message', 'severity', 'category']:
                if field in json_content:
                    extracted[field] = json_content[field]
        
        return extracted
    
    def _check_data_quality(self, json_content: Dict[str, Any], intent: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Check for missing required fields and anomalous values
        
        Returns:
            tuple: (missing_fields, anomalous_fields)
        """
        missing_fields = []
        anomalous_fields = []
        
        # Check against schema if available
        if intent in self.schemas:
            schema = self.schemas[intent]
            
            # Check for missing required fields
            if 'required' in schema:
                for field in schema['required']:
                    if field not in json_content:
                        missing_fields.append(field)
            
            # Check properties for anomalies
            if 'properties' in schema:
                for field, spec in schema['properties'].items():
                    if field in json_content:
                        # Check type
                        if 'type' in spec:
                            expected_type = spec['type']
                            if isinstance(expected_type, list):
                                valid_types = expected_type
                            else:
                                valid_types = [expected_type]
                            
                            # Check if value matches any of the valid types
                            value_type = self._get_json_type(json_content[field])
                            if value_type not in valid_types:
                                anomalous_fields.append({
                                    'field': field,
                                    'issue': f"Expected type {expected_type}, got {value_type}",
                                    'value': str(json_content[field])
                                })
        
        return missing_fields, anomalous_fields
    
    def _get_json_type(self, value: Any) -> str:
        """Get JSON schema type for a value"""
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int) or isinstance(value, float):
            return 'number'
        elif isinstance(value, str):
            return 'string'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        else:
            return 'unknown'
