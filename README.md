# UART MCP Tool

A Model Context Protocol (MCP) server that provides AI assistants with standardized interfaces for serial port communication, enabling seamless interaction with embedded systems and hardware devices.

## Overview

The UART MCP Tool offers both a comprehensive GUI application for development and debugging, and a lightweight MCP server for AI integration. It supports real-time serial communication, log management, and command transmission with AI assistants like Claude.

## Features

- 🔌 **Serial Port Management**: Connect to and manage serial devices with configurable parameters
- 📊 **Real-time Data Monitoring**: Continuous serial data reception with timestamp support
- 🔍 **Advanced Log Search**: Regex-based log filtering and querying capabilities
- 📡 **Command Transmission**: Send text or hex commands to connected devices
- 🤖 **AI Integration**: Full MCP server for seamless AI assistant interaction
- 🎨 **GUI Application**: User-friendly interface for direct device interaction
- ⚙️ **Configurable Settings**: Persistent configuration and preset commands

## Installation

### Prerequisites

- Python 3.8 or higher
- UV package manager (recommended) or pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd uart-mcp
```

2. Install dependencies:
```bash
uv sync
```

## Usage

### 1. GUI Mode (Recommended for Development)

```bash
uv run python main.py
```

**Features:**
- Complete graphical interface with serial port configuration
- Real-time data display with hex/text modes
- Timestamp display toggle option
- Log filtering and searching
- Preset command buttons
- Manual command transmission

**Interface Layout:**
- **Left Panel**: Port configuration, receive/send settings
- **Center Panel**: Real-time serial data display
- **Right Panel**: Log filtering and command transmission

### 2. MCP Service Mode (Recommended for AI Integration)

```bash
uv run python mcp_only.py
```

**Features:**
- Lightweight MCP server without GUI
- Lower resource consumption
- Perfect for AI assistant backend service
- STDIO transport for direct integration

## MCP Client Configuration

### Claude Desktop Setup

1. Locate your Claude Desktop configuration file:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Add the following configuration (adjust the `cwd` path to your actual project directory):

```json
{
  "mcpServers": {
    "uart-mcp": {
      "command": "uv",
      "args": ["run", "python", "mcp_only.py"],
      "cwd": "D:\\workspace\\pythonTools\\uart-mcp",
      "env": {
        "PYTHONPATH": "D:\\workspace\\pythonTools\\uart-mcp"
      }
    }
  }
}
```

3. Restart Claude Desktop

## MCP Interface Reference

### 1. `get_serial_status`

**Description**: Get current serial port connection status and configuration information.

**Parameters**: None

**Returns**:
```json
{
  "status": "connected|disconnected",
  "port": "COM3",
  "baudrate": 115200,
  "bytesize": 8,
  "parity": "N",
  "stopbits": 1
}
```

**Usage Example**: 
> "Please check the serial port connection status"

### 2. `query_serial_logs`

**Description**: Search for lines matching a regular expression pattern in the serial log buffer.

**Parameters**:
- `pattern` (str): Regular expression pattern (e.g., `"^.*reminder.*$"`)
- `max_results` (int, optional): Maximum number of results to return (default: 100)

**Returns**:
```json
{
  "status": "success",
  "message": "Found 5 matching records",
  "matches": ["[10:23:45.123] reminder: task completed", ...],
  "total_matches": 5,
  "buffer_size": 1000,
  "pattern": ".*reminder.*",
  "max_results": 100
}
```

**Usage Examples**:
> "Search for lines containing 'reminder' in the serial logs"
> "Use regex '^.*Error.*$' to find all error logs"
> "Search for temperature logs with pattern '.*Temperature.*\\d+.*°C.*'"

### 3. `get_log_buffer_info`

**Description**: Get basic information about the log buffer.

**Parameters**: None

**Returns**:
```json
{
  "status": "success",
  "buffer_size": 850,
  "max_buffer_size": 1000,
  "oldest_entry": "[09:15:32.456] System startup",
  "newest_entry": "[10:23:45.789] Data received"
}
```

**Usage Example**: 
> "Tell me about the current log buffer status"

### 4. `clear_log_buffer`

**Description**: Clear the serial port log buffer.

**Parameters**: None

**Returns**:
```json
{
  "status": "success",
  "message": "Log buffer cleared successfully"
}
```

**Usage Example**: 
> "Please clear the serial log buffer"

### 5. `get_recent_logs`

**Description**: Get the most recent N lines from the serial log buffer.

**Parameters**:
- `lines` (int, optional): Number of log lines to retrieve (default: 500)

**Returns**:
```json
{
  "status": "success",
  "message": "Successfully retrieved 500 recent log lines",
  "logs": ["[10:23:45.123] Data line 1", "..."],
  "requested_lines": 500,
  "actual_lines": 500,
  "buffer_size": 1000
}
```

**Usage Examples**:
> "Get the last 100 lines from serial logs"
> "Show me the most recent serial data"

### 6. `send_serial_command`

**Description**: Send commands to the serial port device.

**Parameters**:
- `command` (str): Command string to send (e.g., `"dbg reboot"`)
- `is_hex` (bool, optional): Whether data is hexadecimal (default: False)
- `add_newline` (bool, optional): Whether to automatically add `\r\n` (default: True)

**Returns**:
```json
{
  "status": "success",
  "message": "Command sent successfully: \"dbg reboot\" + \\r\\n",
  "command": "dbg reboot",
  "sent": true,
  "is_hex": false,
  "add_newline": true
}
```

**Usage Examples**:
> "Send command 'dbg reboot' to the serial device"
> "Send hex data '48656C6C6F' to the device"
> "Send 'AT+GMR' without newline characters"

## Configuration Files

### `config.json`

Main configuration file containing:

```json
{
  "mcp_host": "127.0.0.1",
  "mcp_port": 8000,
  "last_serial_port": "COM3",
  "last_baud_rate": 115200,
  "show_timestamp": true
}
```

- `mcp_host`: MCP server listening address
- `mcp_port`: MCP server port (unused in STDIO mode)
- `last_serial_port`: Last used serial port
- `last_baud_rate`: Last used baud rate
- `show_timestamp`: Whether to display timestamps in logs

### `presets.json`

Preset command configuration for quick access:

```json
[
  {"name": "Reboot", "command": "dbg reboot"},
  {"name": "ADFU Mode", "command": "dbg reboot adfu"},
  {"name": "AT Command", "command": "AT"},
  {"name": "Version", "command": "AT+GMR"}
]
```

## GUI Features

### Left Panel - Configuration
- **Port Configuration**: Select COM port and baud rate
- **Receive Settings**: 
  - HEX display mode toggle
  - Timestamp display toggle
- **Send Settings**: 
  - HEX send mode
  - Automatic newline addition

### Center Panel - Data Display
- Real-time serial data reception
- Automatic scrolling
- Copy and save functionality
- Clear buffer button

### Right Panel - Functions
- **Log Filtering**: Keyword-based log filtering
- **Command Transmission**: Manual command entry and sending
- **Preset Commands**: Quick-access buttons for common commands

## Troubleshooting

### 1. MCP Server Issues
- Verify Python environment and dependencies are installed correctly
- Check that no other process is using the same resources
- Ensure proper file permissions

### 2. Claude Desktop Connection Issues
- Verify configuration file path is correct
- Confirm `cwd` path points to the project directory
- Restart Claude Desktop after configuration changes
- Check console output for error messages

### 3. Serial Port Connection Issues
- Confirm serial device is properly connected
- Check serial port permissions (Linux/macOS: may need to add user to dialout group)
- Verify correct baud rate and communication parameters
- Ensure no other application is using the serial port

### 4. Permission Issues (Linux/macOS)
```bash
# Add user to dialout group for serial port access
sudo usermod -a -G dialout $USER
# Log out and log back in for changes to take effect
```

## Development

### Adding New MCP Tools

To extend functionality, add new tools in `mcp_server.py`:

```python
@mcp.tool()
def your_new_tool(param1: str, param2: int = 100) -> dict:
    """Your tool description for AI context"""
    try:
        # Implement your functionality here
        result = your_implementation(param1, param2)
        return {
            "status": "success",
            "data": result,
            "message": "Operation completed successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error occurred: {str(e)}"
        }
```

### Project Structure

```
uart-mcp/
├── main.py              # GUI application entry point
├── mcp_only.py          # MCP server only mode
├── mcp_server.py        # MCP server implementation
├── service.py           # Serial communication service
├── config.py            # Configuration management
├── config.json          # Runtime configuration
├── presets.json         # Command presets
└── requirements.txt     # Python dependencies
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check console output for detailed error messages
2. Verify configuration file formats are correct
3. Ensure all dependencies are properly installed
4. Review the troubleshooting section above 