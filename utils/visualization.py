"""
Visualization Utilities for Multi-Agent AI System
Provides functions to visualize processing results and statistics.
"""

import os
import json
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import io
import base64

def get_processing_stats(db_path="outputs/memory.db"):
    """
    Get statistics about processed documents
    
    Args:
        db_path: Path to the memory database
        
    Returns:
        dict: Processing statistics
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get format counts
        cursor.execute("SELECT format, COUNT(*) FROM memory GROUP BY format")
        format_counts = dict(cursor.fetchall())
        
        # Get intent counts
        cursor.execute("SELECT intent, COUNT(*) FROM memory GROUP BY intent")
        intent_counts = dict(cursor.fetchall())
        
        # Get processing timeline (last 7 days)
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute("SELECT DATE(timestamp) as date, COUNT(*) FROM memory WHERE timestamp > ? GROUP BY DATE(timestamp)", (seven_days_ago,))
        timeline = dict(cursor.fetchall())
        
        # Get agent routing counts
        cursor.execute("SELECT to_agent, COUNT(*) FROM routing_log GROUP BY to_agent")
        agent_counts = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'format_counts': format_counts,
            'intent_counts': intent_counts,
            'timeline': timeline,
            'agent_counts': agent_counts
        }
    except Exception as e:
        print(f"Error getting processing stats: {e}")
        return {
            'format_counts': {},
            'intent_counts': {},
            'timeline': {},
            'agent_counts': {}
        }

def plot_format_distribution(stats):
    """
    Generate a pie chart of document format distribution
    
    Args:
        stats: Processing statistics from get_processing_stats()
        
    Returns:
        str: Base64-encoded PNG image
    """
    format_counts = stats.get('format_counts', {})
    
    if not format_counts:
        return None
    
    plt.figure(figsize=(8, 6))
    plt.pie(format_counts.values(), labels=format_counts.keys(), autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('Document Format Distribution')
    
    # Save to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    
    # Convert to base64
    return base64.b64encode(buf.read()).decode('utf-8')

def plot_intent_distribution(stats):
    """
    Generate a bar chart of document intent distribution
    
    Args:
        stats: Processing statistics from get_processing_stats()
        
    Returns:
        str: Base64-encoded PNG image
    """
    intent_counts = stats.get('intent_counts', {})
    
    if not intent_counts:
        return None
    
    plt.figure(figsize=(10, 6))
    plt.bar(intent_counts.keys(), intent_counts.values())
    plt.title('Document Intent Distribution')
    plt.xlabel('Intent')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    
    # Convert to base64
    return base64.b64encode(buf.read()).decode('utf-8')

def plot_processing_timeline(stats):
    """
    Generate a line chart of document processing timeline
    
    Args:
        stats: Processing statistics from get_processing_stats()
        
    Returns:
        str: Base64-encoded PNG image
    """
    timeline = stats.get('timeline', {})
    
    if not timeline:
        return None
    
    # Sort by date
    dates = sorted(timeline.keys())
    counts = [timeline[date] for date in dates]
    
    plt.figure(figsize=(10, 6))
    plt.plot(dates, counts, marker='o')
    plt.title('Document Processing Timeline')
    plt.xlabel('Date')
    plt.ylabel('Documents Processed')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    
    # Convert to base64
    return base64.b64encode(buf.read()).decode('utf-8')

def generate_processing_report(db_path="outputs/memory.db", output_path="outputs/report.html"):
    """
    Generate an HTML report of processing statistics
    
    Args:
        db_path: Path to the memory database
        output_path: Path to save the HTML report
        
    Returns:
        str: Path to the generated report
    """
    stats = get_processing_stats(db_path)
    
    # Generate charts
    format_chart = plot_format_distribution(stats)
    intent_chart = plot_intent_distribution(stats)
    timeline_chart = plot_processing_timeline(stats)
    
    # Create HTML report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi-Agent AI System - Processing Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #2c3e50; }}
            .container {{ display: flex; flex-wrap: wrap; }}
            .chart {{ margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Multi-Agent AI System - Processing Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Processing Statistics</h2>
        <div class="container">
    """
    
    # Add format distribution chart
    if format_chart:
        html += f"""
            <div class="chart">
                <h3>Document Format Distribution</h3>
                <img src="data:image/png;base64,{format_chart}" alt="Format Distribution">
                <table>
                    <tr><th>Format</th><th>Count</th></tr>
                    {''.join(f'<tr><td>{format}</td><td>{count}</td></tr>' for format, count in stats['format_counts'].items())}
                </table>
            </div>
        """
    
    # Add intent distribution chart
    if intent_chart:
        html += f"""
            <div class="chart">
                <h3>Document Intent Distribution</h3>
                <img src="data:image/png;base64,{intent_chart}" alt="Intent Distribution">
                <table>
                    <tr><th>Intent</th><th>Count</th></tr>
                    {''.join(f'<tr><td>{intent}</td><td>{count}</td></tr>' for intent, count in stats['intent_counts'].items())}
                </table>
            </div>
        """
    
    # Add timeline chart
    if timeline_chart:
        html += f"""
            <div class="chart">
                <h3>Processing Timeline</h3>
                <img src="data:image/png;base64,{timeline_chart}" alt="Processing Timeline">
                <table>
                    <tr><th>Date</th><th>Count</th></tr>
                    {''.join(f'<tr><td>{date}</td><td>{count}</td></tr>' for date, count in sorted(stats['timeline'].items()))}
                </table>
            </div>
        """
    
    # Add agent routing stats
    html += f"""
            <div class="chart">
                <h3>Agent Routing Statistics</h3>
                <table>
                    <tr><th>Agent</th><th>Count</th></tr>
                    {''.join(f'<tr><td>{agent}</td><td>{count}</td></tr>' for agent, count in stats['agent_counts'].items())}
                </table>
            </div>
        </div>
    """
    
    # Close HTML
    html += """
    </body>
    </html>
    """
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write HTML to file
    with open(output_path, 'w') as f:
        f.write(html)
    
    return output_path
