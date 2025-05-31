"""
Parser Utilities Module for Multi-Agent AI System
Provides utilities for parsing different document formats.
"""

import os
import json
import email
from email import policy
from email.parser import BytesParser, Parser
from typing import Dict, Any, Tuple, Optional, Union, BinaryIO, TextIO

# PDF parsing utilities
try:
    import pdfplumber
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

def detect_file_format(file_path: str) -> str:
    """
    Detect the format of a file based on extension and content
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: Detected format ('pdf', 'json', 'email', 'unknown')
    """
    # Check file extension
    _, ext = os.path.splitext(file_path.lower())
    
    if ext == '.pdf':
        return 'pdf'
    elif ext == '.json':
        # Validate JSON content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return 'json'
        except json.JSONDecodeError:
            pass
    elif ext in ('.eml', '.txt'):
        # Try to parse as email
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'From:' in content and ('Subject:' in content or 'To:' in content):
                    return 'email'
        except UnicodeDecodeError:
            pass
    
    # If extension check failed, try content-based detection
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # Read first 1000 chars
            
            # Check for JSON format
            if content.strip().startswith('{') and content.strip().endswith('}'):
                try:
                    json.loads(content)
                    return 'json'
                except json.JSONDecodeError:
                    pass
            
            # Check for email format
            if 'From:' in content and ('Subject:' in content or 'To:' in content):
                return 'email'
    except UnicodeDecodeError:
        # Binary file, could be PDF
        if ext == '.pdf':
            return 'pdf'
    
    return 'unknown'

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text content from a PDF file
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    if not PDF_SUPPORT:
        raise ImportError("PDF support requires pdfplumber and PyMuPDF libraries")
    
    # Try PyMuPDF first (usually better performance)
    try:
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        print(f"PyMuPDF extraction failed: {e}, trying pdfplumber...")
    
    # Fallback to pdfplumber
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"PDF text extraction failed: {e}")
        return ""

def parse_email(file_path: str) -> Dict[str, Any]:
    """
    Parse an email file (.eml or .txt) into structured data
    
    Args:
        file_path: Path to the email file
        
    Returns:
        dict: Structured email data
    """
    try:
        # Try to parse as .eml file first
        with open(file_path, 'rb') as f:
            try:
                msg = BytesParser(policy=policy.default).parse(f)
                
                # Extract email parts
                email_data = {
                    'from': msg.get('From', ''),
                    'to': msg.get('To', ''),
                    'subject': msg.get('Subject', ''),
                    'date': msg.get('Date', ''),
                    'body': '',
                }
                
                # Get email body
                if msg.is_multipart():
                    for part in msg.iter_parts():
                        if part.get_content_type() == 'text/plain':
                            email_data['body'] = part.get_content()
                            break
                else:
                    email_data['body'] = msg.get_content()
                
                return email_data
            except Exception:
                # If .eml parsing fails, try as plain text
                pass
        
        # Try to parse as plain text email
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Simple parsing for plain text emails
            email_data = {
                'from': '',
                'to': '',
                'subject': '',
                'date': '',
                'body': content,
            }
            
            # Extract headers from plain text
            lines = content.split('\n')
            body_start = 0
            
            for i, line in enumerate(lines):
                if line.startswith('From:'):
                    email_data['from'] = line[5:].strip()
                elif line.startswith('To:'):
                    email_data['to'] = line[3:].strip()
                elif line.startswith('Subject:'):
                    email_data['subject'] = line[8:].strip()
                elif line.startswith('Date:'):
                    email_data['date'] = line[5:].strip()
                
                # Empty line usually marks the start of the body
                if line.strip() == '' and i > 0:
                    body_start = i + 1
                    break
            
            # Set body if headers were found
            if body_start > 0:
                email_data['body'] = '\n'.join(lines[body_start:])
            
            return email_data
    
    except Exception as e:
        print(f"Email parsing failed: {e}")
        return {
            'from': '',
            'to': '',
            'subject': '',
            'date': '',
            'body': '',
            'error': str(e)
        }

def parse_json_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a JSON file into a Python dictionary
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        dict: Parsed JSON data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        return {}
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return {}
