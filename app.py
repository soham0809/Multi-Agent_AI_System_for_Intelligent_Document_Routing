"""
Streamlit Web Interface for Multi-Agent AI System
Provides a user-friendly interface for document processing and visualization.
"""

import os
import json
import streamlit as st
import pandas as pd
from datetime import datetime
import tempfile
import sqlite3
import uuid

# Import our multi-agent system
from main import MultiAgentSystem

# Set page configuration
st.set_page_config(
    page_title="Multi-Agent Document Router",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'system' not in st.session_state:
    st.session_state.system = MultiAgentSystem()
    
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []
    
if 'selected_thread' not in st.session_state:
    st.session_state.selected_thread = None

# Helper functions
def load_processing_results():
    """Load processing results from the memory database"""
    try:
        conn = sqlite3.connect('outputs/memory.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all threads
        cursor.execute("SELECT thread_id, input_source, timestamp, format, intent, status FROM memory")
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append(dict(row))
            
        conn.close()
        return results
    except Exception as e:
        st.error(f"Error loading results: {e}")
        return []

def get_thread_details(thread_id):
    """Get detailed information for a specific thread"""
    try:
        return st.session_state.system.memory.get_thread_info(thread_id)
    except Exception as e:
        st.error(f"Error getting thread details: {e}")
        return {}

def process_uploaded_file(uploaded_file):
    """Process an uploaded file through the multi-agent system"""
    # Create a temporary file to save the uploaded content
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        file_path = tmp_file.name
    
    try:
        # Process the file
        result = st.session_state.system.process_document(file_path)
        
        # Add to processed files list
        if result['status'] == 'success':
            st.session_state.processed_files.append({
                'filename': uploaded_file.name,
                'thread_id': result['thread_id'],
                'format': result['format'],
                'intent': result['intent'],
                'timestamp': datetime.now().isoformat()
            })
            
        # Clean up the temporary file
        os.unlink(file_path)
        
        return result
    except Exception as e:
        # Clean up the temporary file
        os.unlink(file_path)
        raise e

# Sidebar
st.sidebar.title("📄 Document Router")
st.sidebar.markdown("---")

# File upload section
st.sidebar.header("Upload Documents")
uploaded_file = st.sidebar.file_uploader("Choose a file", type=['txt', 'json', 'pdf', 'eml'])

if uploaded_file is not None:
    if st.sidebar.button("Process Document"):
        with st.spinner("Processing document..."):
            try:
                result = process_uploaded_file(uploaded_file)
                if result['status'] == 'success':
                    st.sidebar.success(f"Document processed successfully as {result['format']} with intent {result['intent']}")
                else:
                    st.sidebar.error(f"Error: {result.get('message', 'Unknown error')}")
            except Exception as e:
                st.sidebar.error(f"Error processing document: {e}")

# History section
st.sidebar.markdown("---")
st.sidebar.header("Processing History")

# Load processing results
processing_results = load_processing_results()

if processing_results:
    # Convert to DataFrame for display
    df = pd.DataFrame(processing_results)
    df = df.rename(columns={
        'thread_id': 'Thread ID',
        'input_source': 'Source',
        'timestamp': 'Time',
        'format': 'Format',
        'intent': 'Intent',
        'status': 'Status'
    })
    
    # Format the source path to show only filename
    df['Source'] = df['Source'].apply(lambda x: os.path.basename(x))
    
    # Format timestamp
    df['Time'] = pd.to_datetime(df['Time']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Display as a table
    st.sidebar.dataframe(df[['Source', 'Format', 'Intent', 'Status']], use_container_width=True)
    
    # Select thread for detailed view
    selected_index = st.sidebar.selectbox(
        "Select a document to view details:",
        options=range(len(df)),
        format_func=lambda i: f"{df.iloc[i]['Source']} ({df.iloc[i]['Intent']})"
    )
    
    if selected_index is not None:
        st.session_state.selected_thread = df.iloc[selected_index]['Thread ID']
else:
    st.sidebar.info("No documents processed yet.")

# Main content area
st.title("Multi-Agent AI System for Intelligent Document Routing")

# Overview section
st.markdown("""
This system processes various document formats (PDF, JSON, Email) and routes them to specialized agents 
for extraction and normalization. The system uses a shared memory component to maintain context and track 
the processing pipeline.
""")

# Display tabs
tab1, tab2, tab3 = st.tabs(["Document Details", "Agent Pipeline", "System Logs"])

with tab1:
    if st.session_state.selected_thread:
        thread_details = get_thread_details(st.session_state.selected_thread)
        
        if thread_details:
            # Document info
            st.subheader("Document Information")
            col1, col2, col3 = st.columns(3)
            col1.metric("Format", thread_details.get('format', 'Unknown'))
            col2.metric("Intent", thread_details.get('intent', 'Unknown'))
            col3.metric("Status", thread_details.get('status', 'Unknown'))
            
            # Metadata
            st.subheader("Metadata")
            metadata = thread_details.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    pass
            
            st.json(metadata)
            
            # Extracted fields
            st.subheader("Extracted Fields")
            extracted_fields = thread_details.get('extracted_fields', {})
            
            if extracted_fields:
                for field, value in extracted_fields.items():
                    # Try to parse JSON strings
                    if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                        try:
                            parsed_value = json.loads(value)
                            st.write(f"**{field}:**")
                            st.json(parsed_value)
                        except:
                            st.write(f"**{field}:** {value}")
                    else:
                        st.write(f"**{field}:** {value}")
            else:
                st.info("No fields extracted")
            
            # Routing history
            st.subheader("Routing History")
            routing_history = thread_details.get('routing_history', [])
            
            if routing_history:
                history_data = []
                for entry in routing_history:
                    history_data.append({
                        'Time': pd.to_datetime(entry.get('timestamp')).strftime('%Y-%m-%d %H:%M:%S'),
                        'From': entry.get('from_agent'),
                        'To': entry.get('to_agent'),
                        'Reason': entry.get('reason')
                    })
                
                st.dataframe(pd.DataFrame(history_data), use_container_width=True)
            else:
                st.info("No routing history available")
    else:
        st.info("Select a document from the sidebar to view details")

with tab2:
    st.subheader("Agent Pipeline")
    
    # Display the agent pipeline as a flowchart
    st.markdown("""
    ```mermaid
    graph TD
        A[Input Document] --> B[Classifier Agent]
        B -->|PDF| C[Future PDF Agent]
        B -->|JSON| D[JSON Agent]
        B -->|Email| E[Email Agent]
        C --> F[Shared Memory]
        D --> F
        E --> F
        F --> G[Output/Results]
    ```
    """)
    
    # Agent descriptions
    st.subheader("Agent Descriptions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Classifier Agent**
        - Detects document format
        - Identifies document intent
        - Routes to specialized agents
        
        **JSON Agent**
        - Validates against schemas
        - Extracts essential fields
        - Flags missing or anomalous fields
        """)
        
    with col2:
        st.markdown("""
        **Email Agent**
        - Extracts sender, subject, urgency
        - Identifies contacts and dates
        - Normalizes to CRM-friendly format
        
        **Shared Memory**
        - Maintains processing context
        - Tracks document flow
        - Stores extracted information
        """)

with tab3:
    st.subheader("System Logs")
    
    try:
        with open("outputs/processing.log", "r") as log_file:
            log_content = log_file.read()
            st.text_area("Log Output", log_content, height=400)
    except FileNotFoundError:
        st.info("No log file found")

# Footer
st.markdown("---")
st.markdown("© 2025 Multi-Agent AI System | Developed for Internshala Project")
