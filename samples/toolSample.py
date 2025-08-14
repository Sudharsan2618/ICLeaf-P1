import requests
import os
import logging
from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Microsoft Graph API endpoint
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

# Set up logging
logger = logging.getLogger(__name__)

class ExcelWriterTool:
    """
    A tool for writing data to SharePoint/OneDrive Excel files using Microsoft Graph API.
    
    This tool provides functionality to:
    - Write multiple values to different cells in SharePoint Excel files
    - Read cell values from SharePoint Excel files
    - Handle multiple sheets
    """
    
    def __init__(self):
        """Initialize the Excel writer tool."""
        self.logger = logger.getChild("ExcelWriterTool")
        self._access_token = None
    
    def _get_access_token(self) -> str:
        """Get Microsoft Graph API access token."""
        if self._access_token:
            return self._access_token
            
        try:
            from msal import ConfidentialClientApplication
            
            tenant_id = os.getenv("TENANT_ID")
            client_id = os.getenv("CLIENT_ID")
            client_secret = os.getenv("CLIENT_SECRET")
            
            if not all([tenant_id, client_id, client_secret]):
                raise Exception("Missing SharePoint credentials in environment variables")
            
            authority = f"https://login.microsoftonline.com/{tenant_id}"
            scope = ["https://graph.microsoft.com/.default"]
            
            app = ConfidentialClientApplication(
                client_id,
                authority=authority,
                client_credential=client_secret
            )
            
            result = app.acquire_token_for_client(scopes=scope)
            if "access_token" in result:
                self._access_token = result["access_token"]
                return self._access_token
            else:
                raise Exception(f"Could not obtain access token: {result}")
                
        except Exception as e:
            self.logger.error(f"Failed to get access token: {e}")
            raise
    
    def _extract_item_id_from_url(self, sharepoint_url: str) -> str:
        """Extract item ID from SharePoint URL."""
        try:
            parsed_url = urlparse(sharepoint_url)
            query_params = parse_qs(parsed_url.query)
            item_id = query_params.get('sourcedoc', [None])[0]
            if not item_id:
                raise Exception("Could not extract item_id from SharePoint URL")
            
            # Remove curly braces from item_id if present
            return item_id.strip('{}')
        except Exception as e:
            self.logger.error(f"Failed to extract item ID from URL: {e}")
            raise
    
    def _get_user_id(self) -> str:
        """Get OneDrive user email from environment."""
        user_id = os.getenv("ONEDRIVE_USER_EMAIL")
        if not user_id:
            raise Exception("ONEDRIVE_USER_EMAIL not configured in environment")
        return user_id
    
    def _create_workbook_session(self, user_id: str, item_id: str, headers: Dict[str, str]) -> str:
        """Create a workbook session for Excel operations."""
        session_url = f"{GRAPH_API_ENDPOINT}/users/{user_id}/drive/items/{item_id}/workbook/createSession"
        session_data = {"persistChanges": True}
        
        response = requests.post(session_url, headers=headers, json=session_data)
        if response.status_code != 201:
            raise Exception(f"Failed to create session: {response.status_code} {response.text}")
        
        return response.json().get('id')
    
    def _close_workbook_session(self, user_id: str, item_id: str, headers: Dict[str, str]):
        """Close the workbook session."""
        close_url = f"{GRAPH_API_ENDPOINT}/users/{user_id}/drive/items/{item_id}/workbook/closeSession"
        requests.post(close_url, headers=headers)
    
    def write_multiple_cells(self, sharepoint_url: str, sheet_name: str, cell_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Write multiple values to different cells in a SharePoint Excel file.
        
        Args:
            sharepoint_url: SharePoint URL of the Excel file
            sheet_name: Name of the sheet to write to
            cell_data: List of dictionaries with 'cell_address' and 'value' keys
            
        Returns:
            Dict containing operation status and details
        """
        try:
            self.logger.info(f"Writing {len(cell_data)} values to sheet '{sheet_name}' in SharePoint Excel file")
            
            # Get required credentials and IDs
            access_token = self._get_access_token()
            user_id = self._get_user_id()
            item_id = self._extract_item_id_from_url(sharepoint_url)
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Create workbook session
            session_id = self._create_workbook_session(user_id, item_id, headers)
            headers['workbook-session-id'] = session_id
            
            written_cells = []
            
            try:
                # Write each cell
                for cell_info in cell_data:
                    cell_address = cell_info.get('cell_address')
                    value = cell_info.get('value')
                    
                    if cell_address and value is not None:
                        # Update the cell using Microsoft Graph API
                        update_url = f"{GRAPH_API_ENDPOINT}/users/{user_id}/drive/items/{item_id}/workbook/worksheets/{sheet_name}/range(address='{cell_address}')"
                        update_data = {
                            "values": [[value]]
                        }
                        
                        response = requests.patch(update_url, headers=headers, json=update_data)
                        if response.status_code == 200:
                            written_cells.append({
                                "cell_address": cell_address,
                                "value": value
                            })
                            self.logger.debug(f"Wrote '{value}' to cell {cell_address}")
                        else:
                            self.logger.error(f"Failed to write to cell {cell_address}: {response.status_code} {response.text}")
                
                self.logger.info(f"Successfully wrote {len(written_cells)} cells")
                
                return {
                    "status": "success",
                    "message": f"Successfully wrote {len(written_cells)} cells to sheet '{sheet_name}'",
                    "sharepoint_url": sharepoint_url,
                    "sheet_name": sheet_name,
                    "written_cells": written_cells
                }
                
            finally:
                # Close the workbook session
                self._close_workbook_session(user_id, item_id, headers)
            
        except Exception as e:
            error_msg = f"Failed to write multiple cells: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg,
                "sharepoint_url": sharepoint_url,
                "sheet_name": sheet_name,
                "cell_data": cell_data
            }
    
    def get_cell_value(self, sharepoint_url: str, sheet_name: str, cell_address: str) -> Dict[str, Any]:
        """
        Get the value of a specific cell from a SharePoint Excel file.
        
        Args:
            sharepoint_url: SharePoint URL of the Excel file
            sheet_name: Name of the sheet
            cell_address: Cell address to read
            
        Returns:
            Dict containing the cell value and status
        """
        try:
            self.logger.info(f"Reading cell {cell_address} from sheet '{sheet_name}' in SharePoint Excel file")
            
            # Get required credentials and IDs
            access_token = self._get_access_token()
            user_id = self._get_user_id()
            item_id = self._extract_item_id_from_url(sharepoint_url)
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Create workbook session
            session_id = self._create_workbook_session(user_id, item_id, headers)
            headers['workbook-session-id'] = session_id
            
            try:
                # Get the cell value using Microsoft Graph API
                get_url = f"{GRAPH_API_ENDPOINT}/users/{user_id}/drive/items/{item_id}/workbook/worksheets/{sheet_name}/range(address='{cell_address}')"
                
                response = requests.get(get_url, headers=headers)
                if response.status_code == 200:
                    value = response.json().get('values', [[None]])[0][0]
                    
                    self.logger.info(f"Successfully read cell {cell_address}: {value}")
                    
                    return {
                        "status": "success",
                        "message": f"Successfully read cell {cell_address}",
                        "sharepoint_url": sharepoint_url,
                        "sheet_name": sheet_name,
                        "cell_address": cell_address,
                        "value": value
                    }
                else:
                    raise Exception(f"Failed to read cell: {response.status_code} {response.text}")
                    
            finally:
                # Close the workbook session
                self._close_workbook_session(user_id, item_id, headers)
            
        except Exception as e:
            error_msg = f"Failed to read cell {cell_address}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg,
                "sharepoint_url": sharepoint_url,
                "sheet_name": sheet_name,
                "cell_address": cell_address
            }
