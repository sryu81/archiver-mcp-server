from datetime import datetime, timezone
from typing import List, Dict, Any
import pandas as pd

from .generated import payload_pb2

class ProtobufParser:
    """Parser for EPICS Archiver protobuf data."""
    
    @staticmethod
    def parse_to_dataframe(raw_data: bytes) -> pd.DataFrame:
        """
        Parse protobuf data into a Pandas DataFrame.
        
        Args:
            raw_data: Raw protobuf bytes from archiver
            
        Returns:
            DataFrame with columns: timestamp, value, severity, status
        """
        payload = payload_pb2.Payload()
        payload.ParseFromString(raw_data)
        
        year = payload.info.year
        base_date = datetime(year, 1, 1, tzinfo=timezone.utc)
        
        records = []
        for sample in payload.sample:
            # Calculate timestamp
            timestamp = base_date.timestamp() + sample.secondsintoyear + (sample.nano / 1e9)
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            
            # Handle scalar vs waveform data
            value = sample.val[0] if len(sample.val) > 0 else None
            
            records.append({
                'timestamp': dt,
                'value': value,
                'severity': sample.severity,
                'status': sample.status
            })
        
        df = pd.DataFrame(records)
        return df
    
    @staticmethod
    def parse_to_dict(raw_data: bytes) -> Dict[str, Any]:
        """
        Parse protobuf data into a simple dictionary.
        
        Args:
            raw_data: Raw protobuf bytes from archiver
            
        Returns:
            Dictionary with pv_name, timestamps, values, etc.
        """
        df = ProtobufParser.parse_to_dataframe(raw_data)
        
        return {
            'timestamps': df['timestamp'].dt.isoformat().tolist(),
            'values': df['value'].tolist(),
            'severities': df['severity'].tolist(),
            'statuses': df['status'].tolist(),
            'count': len(df)
        }