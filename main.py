"""
Multi-Agent AI System for Intelligent Document Routing
Main entry point for the system that orchestrates the document processing pipeline.
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import agent modules
from agents.classifier_agent import ClassifierAgent
from agents.email_agent import EmailAgent
from agents.json_agent import JSONAgent
from memory.shared_memory import SharedMemory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("outputs/processing.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("MultiAgentSystem")

class MultiAgentSystem:
    """
    Main orchestrator for the Multi-Agent AI System.
    Coordinates the document processing pipeline and agent interactions.
    """
    
    def __init__(self, memory_path: str = "outputs/memory.db"):
        """
        Initialize the multi-agent system
        
        Args:
            memory_path: Path to the shared memory database
        """
        # Ensure outputs directory exists
        os.makedirs("outputs", exist_ok=True)
        
        # Initialize shared memory
        self.memory = SharedMemory(memory_path)
        
        # Initialize agents
        self.classifier_agent = ClassifierAgent(self.memory)
        self.email_agent = EmailAgent(self.memory)
        self.json_agent = JSONAgent(self.memory)
        
        logger.info("Multi-Agent System initialized")
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document through the agent pipeline
        
        Args:
            file_path: Path to the input document
            
        Returns:
            dict: Processing result
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {"status": "error", "message": f"File not found: {file_path}"}
        
        logger.info(f"Processing document: {file_path}")
        
        try:
            # Step 1: Classify document with Classifier Agent
            classification = self.classifier_agent.process(file_path)
            
            if classification["status"] != "success":
                logger.error(f"Classification failed: {classification.get('message', 'Unknown error')}")
                return classification
            
            thread_id = classification["thread_id"]
            format_type = classification["format"]
            target_agent = classification["target_agent"]
            content = classification["content"]
            
            logger.info(f"Document classified as {format_type}, intent: {classification['intent']}")
            logger.info(f"Routing to {target_agent}")
            
            # Step 2: Route to appropriate specialized agent
            if target_agent == "email_agent":
                result = self.email_agent.process(thread_id, content)
            elif target_agent == "json_agent":
                result = self.json_agent.process(thread_id, content)
            else:
                logger.error(f"Unknown target agent: {target_agent}")
                return {"status": "error", "message": f"Unknown target agent: {target_agent}"}
            
            # Step 3: Export results to JSON
            output_path = self.memory.export_to_json(f"outputs/document_{thread_id}.json")
            
            logger.info(f"Document processing completed. Results saved to {output_path}")
            
            # Return the combined result
            return {
                "status": "success",
                "thread_id": thread_id,
                "format": format_type,
                "intent": classification["intent"],
                "processing_result": result,
                "output_path": output_path
            }
            
        except Exception as e:
            logger.exception(f"Error processing document: {e}")
            return {"status": "error", "message": str(e)}
    
    def process_batch(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        Process all documents in a directory
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            list: List of processing results
        """
        if not os.path.isdir(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return [{"status": "error", "message": f"Directory not found: {directory_path}"}]
        
        results = []
        
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                result = self.process_document(file_path)
                results.append(result)
        
        # Export final combined results
        self.memory.export_to_json("outputs/logs.json")
        
        return results


def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Multi-Agent AI System for Intelligent Document Routing")
    parser.add_argument("--input", "-i", required=True, help="Input file or directory path")
    parser.add_argument("--memory", "-m", default="outputs/memory.db", help="Path to shared memory database")
    parser.add_argument("--batch", "-b", action="store_true", help="Process all files in the input directory")
    
    args = parser.parse_args()
    
    # Initialize the multi-agent system
    system = MultiAgentSystem(memory_path=args.memory)
    
    # Process input
    if args.batch and os.path.isdir(args.input):
        results = system.process_batch(args.input)
        logger.info(f"Batch processing completed. Processed {len(results)} documents.")
    else:
        result = system.process_document(args.input)
        logger.info(f"Document processing completed with status: {result['status']}")
    
    logger.info("All processing completed. Results saved in outputs directory.")


if __name__ == "__main__":
    main()
