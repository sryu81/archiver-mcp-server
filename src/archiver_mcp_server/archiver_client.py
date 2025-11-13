import httpx
from typing import Optional
from datetime import datetime

class ArchiverClient:
    """Client for EPICS Archiver Appliance API."""
    
    def __init__(self, base_url: str):
        """
        Initialize the archiver client.
        
        Args:
            base_url: Base URL of the archiver appliance (e.g., http://archiver.example.com)
        """
        self.base_url = base_url.rstrip('/')
        self.retrieval_url = f"{self.base_url}/retrieval/data/getData.raw"
    
    async def fetch_pv_data(
        self, 
        pv_name: str, 
        start_time: str, 
        end_time: str,
        timeout: float = 30.0
    ) -> Optional[bytes]:
        """
        Fetch raw protobuf data for a PV.
        
        Args:
            pv_name: Process Variable name
            start_time: ISO 8601 start time (e.g., 2024-01-01T00:00:00Z)
            end_time: ISO 8601 end time
            timeout: Request timeout in seconds
            
        Returns:
            Raw protobuf bytes or None on error
        """
        params = {
            "pv": pv_name,
            "from": start_time,
            "to": end_time,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.retrieval_url,
                    params=params,
                    timeout=timeout
                )
                response.raise_for_status()
                return response.content
            except httpx.HTTPStatusError as e:
                print(f"HTTP error fetching {pv_name}: {e.response.status_code}")
                return None
            except httpx.RequestError as e:
                print(f"Request error fetching {pv_name}: {e}")
                return None