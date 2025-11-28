"""
Audit Logger for tracking case processing activities.

This module provides structured audit logging for the Ultrasound Report Generator,
tracking user actions, case processing, and system metrics.

Supports two storage backends:
1. Google Sheets (preferred for cloud deployments like Streamlit Community Cloud)
2. Local CSV file (fallback for local development)
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any
import hashlib

from src.utils.logger import LoggerManager

logger = LoggerManager.get_logger(__name__)

# Try to import Google Sheets dependencies
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    logger.warning("gspread not installed - Google Sheets logging unavailable")

# Try to import Streamlit for secrets management
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


class AuditLogger:
    """
    Audit logger that writes case processing events to Google Sheets or CSV.
    
    Tracks:
    - Timestamp of the event
    - Anonymized user identifier (hashed for privacy)
    - Anonymized case ID (hashed for privacy)
    - Processing status (SUCCESS/FAILURE)
    - Number of LLM API calls made
    - Processing duration in seconds
    
    Storage Priority:
    1. Google Sheets (if credentials are configured)
    2. Local CSV file (fallback)
    """
    
    HEADERS = ["timestamp", "user", "case_id", "status", "llm_calls", "duration_seconds"]
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(
        self, 
        log_file: str = "logs/audit_log.csv",
        spreadsheet_name: str = "Ultrasound_Report_Audit_Log",
        worksheet_name: str = "audit_log"
    ):
        """
        Initialize the AuditLogger.
        
        Args:
            log_file: Path to the local CSV log file (fallback)
            spreadsheet_name: Name of the Google Sheets spreadsheet
            worksheet_name: Name of the worksheet within the spreadsheet
        """
        self.log_file = Path(log_file)
        self.spreadsheet_name = spreadsheet_name
        self.worksheet_name = worksheet_name
        
        # Initialize Google Sheets client if available
        self.gspread_client = None
        self.worksheet = None
        self.use_google_sheets = False
        
        if GSPREAD_AVAILABLE:
            self._initialize_google_sheets()
        
        # Ensure local CSV exists as fallback
        if not self.use_google_sheets:
            self._ensure_local_log_file_exists()
            logger.info(f"AuditLogger initialized with local CSV: {self.log_file}")
    
    def _get_google_credentials(self) -> Optional[dict]:
        """
        Get Google service account credentials from Streamlit secrets or environment.
        
        Returns:
            Dictionary of credentials or None if not available
        """
        credentials_dict = None
        
        # Try Streamlit secrets first (for Streamlit Cloud deployment)
        if STREAMLIT_AVAILABLE:
            try:
                if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
                    credentials_dict = dict(st.secrets['gcp_service_account'])
                    logger.info("Loaded Google credentials from Streamlit secrets")
            except Exception as e:
                logger.debug(f"Could not load from Streamlit secrets: {e}")
        
        # Try environment variable (for local development or other deployments)
        if not credentials_dict:
            import json
            gcp_creds_json = os.environ.get('GCP_SERVICE_ACCOUNT_JSON')
            if gcp_creds_json:
                try:
                    credentials_dict = json.loads(gcp_creds_json)
                    logger.info("Loaded Google credentials from environment variable")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse GCP_SERVICE_ACCOUNT_JSON: {e}")
        
        return credentials_dict
    
    def _initialize_google_sheets(self) -> None:
        """Initialize Google Sheets client and worksheet."""
        try:
            credentials_dict = self._get_google_credentials()
            
            if not credentials_dict:
                logger.info("No Google credentials found - using local CSV fallback")
                return
            
            # Create credentials object
            credentials = Credentials.from_service_account_info(
                credentials_dict,
                scopes=self.SCOPES
            )
            
            # Authorize gspread client
            self.gspread_client = gspread.authorize(credentials)
            
            # Try to open or create the spreadsheet
            try:
                spreadsheet = self.gspread_client.open(self.spreadsheet_name)
            except gspread.SpreadsheetNotFound:
                # Create new spreadsheet
                spreadsheet = self.gspread_client.create(self.spreadsheet_name)
                logger.info(f"Created new spreadsheet: {self.spreadsheet_name}")
            
            # Try to get or create the worksheet
            try:
                self.worksheet = spreadsheet.worksheet(self.worksheet_name)
            except gspread.WorksheetNotFound:
                self.worksheet = spreadsheet.add_worksheet(
                    title=self.worksheet_name,
                    rows=1000,
                    cols=len(self.HEADERS)
                )
                # Add headers to new worksheet
                self.worksheet.append_row(self.HEADERS)
                logger.info(f"Created new worksheet: {self.worksheet_name}")
            
            # Check if headers exist, add if not
            first_row = self.worksheet.row_values(1)
            if not first_row or first_row != self.HEADERS:
                if not first_row:
                    self.worksheet.insert_row(self.HEADERS, 1)
                    logger.info("Added headers to worksheet")
            
            self.use_google_sheets = True
            logger.info(f"AuditLogger initialized with Google Sheets: {self.spreadsheet_name}/{self.worksheet_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            logger.info("Falling back to local CSV storage")
            self.use_google_sheets = False
    
    def _ensure_local_log_file_exists(self) -> None:
        """Ensure the local log directory and file exist with proper headers."""
        # Create directory if it doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists and has content
        if not self.log_file.exists() or self.log_file.stat().st_size == 0:
            # Write headers to new file
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.HEADERS)
            logger.info(f"Created new local audit log file with headers: {self.log_file}")
    
    @staticmethod
    def anonymize_user(raw_user: str) -> str:
        """
        Anonymize the user name by hashing it for privacy.
        
        Uses SHA-256 hash truncated to 8 characters to provide a consistent,
        privacy-preserving identifier for users without storing their actual name.
        
        Args:
            raw_user: Original user name or identifier
            
        Returns:
            Anonymized user ID (first 8 characters of SHA-256 hash)
        """
        hash_object = hashlib.sha256(raw_user.encode('utf-8'))
        return hash_object.hexdigest()[:8]
    
    @staticmethod
    def anonymize_case_id(raw_case_id: str) -> str:
        """
        Anonymize the case ID by hashing it for privacy.
        
        Uses SHA-256 hash truncated to 12 characters for a balance
        between uniqueness and readability.
        
        Args:
            raw_case_id: Original case identifier (e.g., patient name or filename)
            
        Returns:
            Anonymized case ID (first 12 characters of SHA-256 hash)
        """
        hash_object = hashlib.sha256(raw_case_id.encode('utf-8'))
        return hash_object.hexdigest()[:12]
    
    def _log_to_google_sheets(self, row: List[Any]) -> bool:
        """
        Append a row to Google Sheets.
        
        Args:
            row: List of values to append
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.worksheet.append_row(row, value_input_option='USER_ENTERED')
            return True
        except Exception as e:
            logger.error(f"Failed to log to Google Sheets: {e}")
            return False
    
    def _log_to_csv(self, row: List[Any]) -> bool:
        """
        Append a row to local CSV file.
        
        Args:
            row: List of values to append
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._ensure_local_log_file_exists()
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            return True
        except Exception as e:
            logger.error(f"Failed to log to CSV: {e}")
            return False
    
    def log_case(
        self,
        user: str,
        case_id: str,
        status: str,
        llm_calls: int,
        duration: float
    ) -> None:
        """
        Log a case processing event to the audit log.
        
        Attempts to log to Google Sheets first (if configured), 
        falls back to local CSV if Google Sheets fails.
        
        Args:
            user: Username or identifier of the person who initiated processing (will be anonymized before logging)
            case_id: Case identifier (will be anonymized before logging)
            status: Processing status ("SUCCESS" or "FAILURE")
            llm_calls: Number of LLM API calls made during processing
            duration: Processing duration in seconds
        """
        try:
            # Generate timestamp in ISO 8601 format
            timestamp = datetime.utcnow().isoformat() + "Z"
            
            # Anonymize both user and case ID for privacy
            anonymized_user = self.anonymize_user(user)
            anonymized_case_id = self.anonymize_case_id(case_id)
            
            # Prepare the row data
            row = [
                timestamp,
                anonymized_user,
                anonymized_case_id,
                status,
                llm_calls,
                f"{duration:.2f}"
            ]
            
            # Try Google Sheets first, then fall back to CSV
            logged = False
            if self.use_google_sheets:
                logged = self._log_to_google_sheets(row)
                if not logged:
                    logger.warning("Google Sheets logging failed, falling back to CSV")
            
            if not logged:
                logged = self._log_to_csv(row)
            
            if logged:
                storage = "Google Sheets" if self.use_google_sheets else "local CSV"
                logger.info(
                    f"Audit log entry ({storage}): user={anonymized_user}, case_id={anonymized_case_id}, "
                    f"status={status}, llm_calls={llm_calls}, duration={duration:.2f}s"
                )
            else:
                logger.error("Failed to log audit entry to any storage")
            
        except Exception as e:
            logger.error(f"Failed to write audit log entry: {e}")
            # Don't raise - audit logging failure shouldn't break the main workflow