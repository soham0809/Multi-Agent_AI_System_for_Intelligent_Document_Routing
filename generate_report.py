"""
Report Generation Script for Multi-Agent AI System
Generates HTML reports with processing statistics and visualizations.
"""

import os
import sys
import argparse
from utils.visualization import generate_processing_report

def main():
    """Main entry point for report generation"""
    parser = argparse.ArgumentParser(description="Generate processing reports for Multi-Agent AI System")
    parser.add_argument("--db", default="outputs/memory.db", help="Path to memory database")
    parser.add_argument("--output", default="outputs/report.html", help="Path to save the HTML report")
    
    args = parser.parse_args()
    
    print(f"Generating report from database: {args.db}")
    
    try:
        report_path = generate_processing_report(args.db, args.output)
        print(f"Report generated successfully: {report_path}")
        
        # Open the report in the default browser
        if sys.platform == 'win32':
            os.system(f'start {report_path}')
        elif sys.platform == 'darwin':
            os.system(f'open {report_path}')
        else:
            os.system(f'xdg-open {report_path}')
            
    except Exception as e:
        print(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
