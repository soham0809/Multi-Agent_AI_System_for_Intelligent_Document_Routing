"""
Demo Script for Multi-Agent AI System
Runs a demonstration of the system by processing all sample files and generating a report.
"""

import os
import sys
import time
import logging
from main import MultiAgentSystem
from utils.visualization import generate_processing_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("outputs/demo.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("MultiAgentDemo")

def run_demo():
    """Run a demonstration of the Multi-Agent AI System"""
    logger.info("Starting Multi-Agent AI System Demo")
    
    # Initialize the system
    system = MultiAgentSystem()
    
    # Get all sample files
    input_dir = "inputs"
    sample_files = []
    
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        if os.path.isfile(file_path):
            sample_files.append(file_path)
    
    logger.info(f"Found {len(sample_files)} sample files: {', '.join(os.path.basename(f) for f in sample_files)}")
    
    # Process each file
    results = []
    for file_path in sample_files:
        logger.info(f"Processing file: {os.path.basename(file_path)}")
        
        # Add a delay for demonstration purposes
        time.sleep(1)
        
        try:
            result = system.process_document(file_path)
            results.append(result)
            
            if result['status'] == 'success':
                logger.info(f"Successfully processed as {result['format']} with intent {result['intent']}")
                
                # Print some extracted fields for demonstration
                thread_info = system.memory.get_thread_info(result['thread_id'])
                extracted_fields = thread_info.get('extracted_fields', {})
                
                if extracted_fields:
                    logger.info("Extracted fields:")
                    for field, value in list(extracted_fields.items())[:5]:  # Show first 5 fields
                        logger.info(f"  - {field}: {value}")
            else:
                logger.error(f"Failed to process: {result.get('message', 'Unknown error')}")
        
        except Exception as e:
            logger.exception(f"Error processing {os.path.basename(file_path)}: {e}")
    
    # Generate a report
    logger.info("Generating processing report")
    report_path = generate_processing_report()
    logger.info(f"Report generated: {report_path}")
    
    # Print summary
    success_count = len([r for r in results if r.get('status') == 'success'])
    logger.info(f"Demo completed. Successfully processed {success_count} out of {len(sample_files)} files.")
    
    # Open the report in the default browser
    if sys.platform == 'win32':
        os.system(f'start {report_path}')
    elif sys.platform == 'darwin':
        os.system(f'open {report_path}')
    else:
        os.system(f'xdg-open {report_path}')

if __name__ == "__main__":
    run_demo()
