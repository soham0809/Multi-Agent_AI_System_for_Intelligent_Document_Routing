"""
Shared Memory Module for Multi-Agent AI System
Provides a centralized memory store for all agents to log and retrieve information.
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

class SharedMemory:
    """
    A shared memory implementation using SQLite for persistent storage.
    Can be easily swapped with Redis implementation if needed.
    """
    
    def __init__(self, db_path: str = "memory.db"):
        """Initialize the shared memory with SQLite backend"""
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Create the necessary tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create main memory table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            thread_id TEXT PRIMARY KEY,
            input_source TEXT,
            timestamp TEXT,
            format TEXT,
            intent TEXT,
            status TEXT,
            metadata TEXT
        )
        ''')
        
        # Create table for extracted fields
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS extracted_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT,
            field_name TEXT,
            field_value TEXT,
            FOREIGN KEY (thread_id) REFERENCES memory (thread_id)
        )
        ''')
        
        # Create table for agent routing logs
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS routing_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT,
            timestamp TEXT,
            from_agent TEXT,
            to_agent TEXT,
            reason TEXT,
            FOREIGN KEY (thread_id) REFERENCES memory (thread_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_thread(self, input_source: str, format_type: str, intent: str) -> str:
        """
        Create a new memory thread for a document
        
        Args:
            input_source: Path or identifier of the input document
            format_type: Detected format (PDF, JSON, Email)
            intent: Detected intent (Invoice, RFQ, etc.)
            
        Returns:
            thread_id: Unique identifier for this processing thread
        """
        thread_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO memory VALUES (?, ?, ?, ?, ?, ?, ?)",
            (thread_id, input_source, timestamp, format_type, intent, "started", "{}")
        )
        
        conn.commit()
        conn.close()
        
        return thread_id
    
    def log_routing(self, thread_id: str, from_agent: str, to_agent: str, reason: str):
        """Log an agent routing event"""
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO routing_log (thread_id, timestamp, from_agent, to_agent, reason) VALUES (?, ?, ?, ?, ?)",
            (thread_id, timestamp, from_agent, to_agent, reason)
        )
        
        conn.commit()
        conn.close()
    
    def store_extracted_field(self, thread_id: str, field_name: str, field_value: Any):
        """Store an extracted field from a document"""
        # Convert non-string values to JSON
        if not isinstance(field_value, str):
            field_value = json.dumps(field_value)
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO extracted_fields (thread_id, field_name, field_value) VALUES (?, ?, ?)",
            (thread_id, field_name, field_value)
        )
        
        conn.commit()
        conn.close()
    
    def update_status(self, thread_id: str, status: str):
        """Update the processing status of a thread"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE memory SET status = ? WHERE thread_id = ?",
            (status, thread_id)
        )
        
        conn.commit()
        conn.close()
    
    def update_metadata(self, thread_id: str, metadata: Dict[str, Any]):
        """Update the metadata for a thread"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE memory SET metadata = ? WHERE thread_id = ?",
            (json.dumps(metadata), thread_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_thread_info(self, thread_id: str) -> Dict[str, Any]:
        """Get all information about a thread"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get main thread info
        cursor.execute("SELECT * FROM memory WHERE thread_id = ?", (thread_id,))
        thread_data = dict(cursor.fetchone())
        
        # Get extracted fields
        cursor.execute("SELECT field_name, field_value FROM extracted_fields WHERE thread_id = ?", (thread_id,))
        fields = {row['field_name']: row['field_value'] for row in cursor.fetchall()}
        
        # Get routing logs
        cursor.execute("SELECT timestamp, from_agent, to_agent, reason FROM routing_log WHERE thread_id = ?", (thread_id,))
        routing = [dict(row) for row in cursor.fetchall()]
        
        # Parse metadata
        if 'metadata' in thread_data and thread_data['metadata']:
            thread_data['metadata'] = json.loads(thread_data['metadata'])
        
        # Add fields and routing to result
        thread_data['extracted_fields'] = fields
        thread_data['routing_history'] = routing
        
        conn.close()
        return thread_data
    
    def export_to_json(self, output_path: str = "outputs/logs.json"):
        """Export all memory data to a JSON file"""
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all threads
        cursor.execute("SELECT thread_id FROM memory")
        thread_ids = [row['thread_id'] for row in cursor.fetchall()]
        
        # Get complete info for each thread
        threads_data = [self.get_thread_info(thread_id) for thread_id in thread_ids]
        
        conn.close()
        
        # Write to JSON file
        with open(output_path, 'w') as f:
            json.dump(threads_data, f, indent=2)
        
        return output_path


# Alternative Redis implementation (commented out)
"""
import redis
import json

class RedisSharedMemory:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db)
    
    def create_thread(self, input_source, format_type, intent):
        thread_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        thread_key = f"thread:{thread_id}"
        self.redis.hset(thread_key, mapping={
            "input_source": input_source,
            "timestamp": timestamp,
            "format": format_type,
            "intent": intent,
            "status": "started"
        })
        
        return thread_id
        
    # Other methods would be implemented similarly
"""
