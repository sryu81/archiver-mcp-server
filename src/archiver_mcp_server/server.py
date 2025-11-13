import os
import json
from datetime import datetime
from typing import Any
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .archiver_client import ArchiverClient
from .protobuf_parser import ProtobufParser

# Initialize the MCP server
app = Server("archiver-mcp-server")

# Global archiver client (will be initialized from environment)
archiver_client: ArchiverClient = None

@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List available MCP tools for EPICS data access.
    """
    return [
        Tool(
            name="get_pv_data",
            description="""
            Retrieve time-series data for an EPICS Process Variable (PV) from the Archiver Appliance.
            
            Returns data including timestamps, values, severity, and status information.
            Use this to analyze historical PV trends, detect anomalies, or extract features for ML models.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "pv_name": {
                        "type": "string",
                        "description": "The name of the Process Variable (e.g., 'MACHINE:SUBSYS:DEVICE:PARAM')"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO 8601 format (e.g., '2024-01-01T00:00:00Z')"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO 8601 format (e.g., '2024-01-02T00:00:00Z')"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "summary"],
                        "description": "Output format: 'json' for full data, 'summary' for statistics",
                        "default": "json"
                    }
                },
                "required": ["pv_name", "start_time", "end_time"]
            }
        ),
        Tool(
            name="get_pv_statistics",
            description="""
            Calculate statistical summary for a PV over a time range.
            
            Returns mean, median, std dev, min, max, and data quality metrics.
            Useful for quick data quality checks and feature extraction.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "pv_name": {
                        "type": "string",
                        "description": "The name of the Process Variable"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO 8601 format"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO 8601 format"
                    }
                },
                "required": ["pv_name", "start_time", "end_time"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool execution requests from AI clients.
    """
    if name == "get_pv_data":
        return await get_pv_data_tool(arguments)
    elif name == "get_pv_statistics":
        return await get_pv_statistics_tool(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def get_pv_data_tool(args: dict) -> list[TextContent]:
    """Execute the get_pv_data tool."""
    pv_name = args["pv_name"]
    start_time = args["start_time"]
    end_time = args["end_time"]
    output_format = args.get("format", "json")
    
    # Fetch raw data
    raw_data = await archiver_client.fetch_pv_data(pv_name, start_time, end_time)
    
    if raw_data is None or len(raw_data) == 0:
        return [TextContent(
            type="text",
            text=f"No data found for PV '{pv_name}' between {start_time} and {end_time}"
        )]
    
    try:
        # Parse the protobuf data
        if output_format == "summary":
            df = ProtobufParser.parse_to_dataframe(raw_data)
            summary = {
                "pv_name": pv_name,
                "time_range": {"start": start_time, "end": end_time},
                "sample_count": len(df),
                "mean": float(df['value'].mean()) if len(df) > 0 else None,
                "std": float(df['value'].std()) if len(df) > 0 else None,
                "min": float(df['value'].min()) if len(df) > 0 else None,
                "max": float(df['value'].max()) if len(df) > 0 else None,
            }
            result_text = json.dumps(summary, indent=2)
        else:
            data_dict = ProtobufParser.parse_to_dict(raw_data)
            data_dict["pv_name"] = pv_name
            result_text = json.dumps(data_dict, indent=2)
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error parsing data for {pv_name}: {str(e)}"
        )]

async def get_pv_statistics_tool(args: dict) -> list[TextContent]:
    """Execute the get_pv_statistics tool."""
    pv_name = args["pv_name"]
    start_time = args["start_time"]
    end_time = args["end_time"]
    
    raw_data = await archiver_client.fetch_pv_data(pv_name, start_time, end_time)
    
    if raw_data is None or len(raw_data) == 0:
        return [TextContent(
            type="text",
            text=f"No data available for statistics"
        )]
    
    try:
        df = ProtobufParser.parse_to_dataframe(raw_data)
        
        stats = {
            "pv_name": pv_name,
            "time_range": {"start": start_time, "end": end_time},
            "statistics": {
                "count": int(len(df)),
                "mean": float(df['value'].mean()),
                "median": float(df['value'].median()),
                "std": float(df['value'].std()),
                "min": float(df['value'].min()),
                "max": float(df['value'].max()),
                "first_value": float(df['value'].iloc[0]),
                "last_value": float(df['value'].iloc[-1]),
            },
            "data_quality": {
                "null_count": int(df['value'].isna().sum()),
                "severity_distribution": df['severity'].value_counts().to_dict()
            }
        }
        
        return [TextContent(type="text", text=json.dumps(stats, indent=2))]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error calculating statistics: {str(e)}"
        )]

async def main():
    """Main entry point for the MCP server."""
    global archiver_client
    
    # Initialize archiver client from environment
    archiver_url = os.getenv("EPICS_ARCHIVER_URL", "http://localhost:17665")
    archiver_client = ArchiverClient(archiver_url)
    
    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="archiver-mcp-server",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())