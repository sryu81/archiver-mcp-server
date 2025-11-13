# Archiver MCP Server

An MCP (Model Context Protocol) server that provides AI applications with access to EPICS Archiver Appliance data.

## Overview

This server enables AI applications to query and analyze Process Variable (PV) data from EPICS Archiver Appliance through the standardized Model Context Protocol. The archiver stores data in Google Protocol Buffer format, which this server fetches, parses, and presents in a structured format for AI consumption.

## Prerequisites

```sh
# create local venv
python3 -m venv venv 

source venv/bin/activate

# install protobuf
sudo apt install protobuf-compiler

```


## Setup

1. **Compile the protobuf file:**
   ```bash
   protoc -I=src --python_out=src/archiver_mcp_server/generated src/payload.proto
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your archiver URL
   ```

4. **Run the server:**
   ```bash
   python -m epics_mcp_server.server
   ```

## Using with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "archiver": {
      "command": "python",
      "args": ["-m", "archiver_mcp_server.server"],
      "env": {
        "EPICS_ARCHIVER_URL": "http://your-archiver-host.example.com:17665"
      }
    }
  }
}
```

## Available Tools

- `get_pv_data`: Retrieve full time-series data for a PV
- `get_pv_statistics`: Get statistical summary of PV data

## Example Usage

Once connected, you can ask Claude things like:

- "Get the data for PV 'MACHINE:TEMP:SENSOR1' from yesterday"
- "Show me statistics for 'MACHINE:PRESSURE:GAUGE2' over the last week"
- "Compare the trends of these three PVs over the last month"


## Next Steps

1. **Compile the protobuf**: Run `protoc -I=src --python_out=src/epics_mcp_server/generated src/payload.proto`
2. **Install**: `pip install -e .`
3. **Configure your archiver URL** in `.env`
4. **Test the server** standalone
5. **Connect it to Claude Desktop** or another MCP client
