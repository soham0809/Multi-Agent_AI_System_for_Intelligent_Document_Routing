"""
Email Agent Module for Multi-Agent AI System
Responsible for processing email documents and extracting structured information.
"""

import os
import sys
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.shared_memory import SharedMemory

class EmailAgent:
    """
    Agent responsible for processing email documents,
    extracting key information and normalizing to a standard format.
    """
    
    def __init__(self, memory: SharedMemory):
        """
        Initialize the email agent
        
        Args:
            memory: Shared memory instance for logging and context
        """
        self.memory = memory
    
    def process(self, thread_id: str, email_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an email document
        
        Args:
            thread_id: The thread ID from the classifier agent
            email_content: Parsed email content
            
        Returns:
            dict: Processing result with extracted information
        """
        # Log start of processing
        self.memory.update_status(thread_id, "processing_email")
        
        # Extract basic email fields
        sender = email_content.get('from', '')
        subject = email_content.get('subject', '')
        body = email_content.get('body', '')
        date = email_content.get('date', '')
        
        # Store extracted fields in memory
        self.memory.store_extracted_field(thread_id, 'sender', sender)
        self.memory.store_extracted_field(thread_id, 'subject', subject)
        self.memory.store_extracted_field(thread_id, 'date', date)
        
        # Extract email domain from sender
        sender_domain = self._extract_domain(sender)
        if sender_domain:
            self.memory.store_extracted_field(thread_id, 'sender_domain', sender_domain)
        
        # Determine urgency based on subject and content
        urgency = self._determine_urgency(subject, body)
        self.memory.store_extracted_field(thread_id, 'urgency', urgency)
        
        # Extract any mentioned contacts
        contacts = self._extract_contacts(body)
        if contacts:
            self.memory.store_extracted_field(thread_id, 'mentioned_contacts', contacts)
        
        # Extract any dates mentioned
        dates = self._extract_dates(body)
        if dates:
            self.memory.store_extracted_field(thread_id, 'mentioned_dates', dates)
        
        # Extract any amounts/numbers
        amounts = self._extract_amounts(body)
        if amounts:
            self.memory.store_extracted_field(thread_id, 'mentioned_amounts', amounts)
        
        # Create normalized CRM-friendly output
        crm_output = self._normalize_to_crm(
            thread_id, sender, subject, body, urgency, 
            sender_domain, contacts, dates, amounts
        )
        
        # Store the normalized output
        self.memory.store_extracted_field(thread_id, 'crm_normalized', crm_output)
        
        # Update status to completed
        self.memory.update_status(thread_id, "completed")
        
        # Return processing result
        return {
            'status': 'success',
            'thread_id': thread_id,
            'extracted_fields': {
                'sender': sender,
                'subject': subject,
                'urgency': urgency,
                'sender_domain': sender_domain,
                'contacts': contacts,
                'dates': dates,
                'amounts': amounts
            },
            'crm_normalized': crm_output
        }
    
    def _extract_domain(self, email_address: str) -> Optional[str]:
        """Extract domain from email address"""
        match = re.search(r'@([^@]+)$', email_address)
        if match:
            return match.group(1)
        return None
    
    def _determine_urgency(self, subject: str, body: str) -> str:
        """
        Determine email urgency based on content
        
        Returns:
            str: 'high', 'medium', or 'low'
        """
        # Keywords indicating high urgency
        high_urgency = ['urgent', 'asap', 'emergency', 'immediate', 'critical', 'important']
        
        # Keywords indicating medium urgency
        medium_urgency = ['soon', 'timely', 'attention', 'priority', 'please respond']
        
        # Check for high urgency keywords
        combined_text = (subject + " " + body).lower()
        for keyword in high_urgency:
            if re.search(r'\b' + re.escape(keyword) + r'\b', combined_text):
                return 'high'
        
        # Check for medium urgency keywords
        for keyword in medium_urgency:
            if re.search(r'\b' + re.escape(keyword) + r'\b', combined_text):
                return 'medium'
        
        # Default to low urgency
        return 'low'
    
    def _extract_contacts(self, text: str) -> List[str]:
        """Extract potential contact information from text"""
        contacts = []
        
        # Extract email addresses
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        contacts.extend(emails)
        
        # Extract phone numbers (simple pattern)
        phones = re.findall(r'\b(?:\+\d{1,3}[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b', text)
        contacts.extend(phones)
        
        return contacts
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates mentioned in the text"""
        dates = []
        
        # Common date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?,? \d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2}(?:st|nd|rd|th)? (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'  # DD Month YYYY
        ]
        
        for pattern in date_patterns:
            found_dates = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(found_dates)
        
        return dates
    
    def _extract_amounts(self, text: str) -> List[str]:
        """Extract monetary amounts or numbers from text"""
        amounts = []
        
        # Currency patterns
        currency_patterns = [
            r'\$\s?\d+(?:,\d{3})*(?:\.\d{2})?',  # $1,000.00
            r'\d+(?:,\d{3})*(?:\.\d{2})?\s?(?:dollars|USD|EUR|GBP)',  # 1,000.00 dollars
            r'(?:USD|EUR|GBP)\s?\d+(?:,\d{3})*(?:\.\d{2})?'  # USD 1,000.00
        ]
        
        for pattern in currency_patterns:
            found_amounts = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(found_amounts)
        
        return amounts
    
    def _normalize_to_crm(self, thread_id: str, sender: str, subject: str, 
                         body: str, urgency: str, sender_domain: Optional[str],
                         contacts: List[str], dates: List[str], 
                         amounts: List[str]) -> Dict[str, Any]:
        """
        Normalize extracted information to a CRM-friendly format
        
        Returns:
            dict: Normalized CRM data
        """
        # Get thread info from memory
        thread_info = self.memory.get_thread_info(thread_id)
        intent = thread_info.get('intent', 'unknown')
        
        # Create normalized output
        crm_data = {
            'contact': {
                'email': sender,
                'domain': sender_domain or '',
                'organization': sender_domain or '',
                'related_contacts': contacts
            },
            'communication': {
                'channel': 'email',
                'subject': subject,
                'urgency': urgency,
                'category': intent,
                'received_date': thread_info.get('timestamp', ''),
                'mentioned_dates': dates
            },
            'business': {
                'mentioned_amounts': amounts,
                'potential_value': self._estimate_potential_value(intent, amounts),
                'follow_up_required': urgency != 'low'
            }
        }
        
        return crm_data
    
    def _estimate_potential_value(self, intent: str, amounts: List[str]) -> Optional[float]:
        """
        Estimate potential business value based on intent and mentioned amounts
        
        Returns:
            float or None: Estimated value or None if can't be determined
        """
        if not amounts:
            return None
            
        # Extract numeric values from amounts
        values = []
        for amount in amounts:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[^\d.]', '', amount)
            try:
                values.append(float(cleaned))
            except ValueError:
                continue
        
        if not values:
            return None
            
        # Use the highest value as potential value
        return max(values)
