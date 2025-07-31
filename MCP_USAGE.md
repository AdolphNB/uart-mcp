# UART MCP 工具使用说明

## 概述

UART MCP 工具提供了一个基于 Model Context Protocol (MCP) 的串口通信服务，允许 AI 助手通过标准化接口与串口设备进行交互。

## 启动模式

### 1. GUI 模式（推荐用于开发调试）
```bash
uv run python main.py
```
- 启动完整的图形界面应用
- 同时在后台运行 MCP 服务
- 适合直接操作和调试

### 2. MCP 服务模式（推荐用于 AI 集成）
```bash
uv run python mcp_only.py
```
- 仅启动 MCP 服务，无 GUI
- 资源占用更少
- 适合作为 AI 助手的后台服务

## MCP 客户端配置

### Claude Desktop 配置

1. 找到 Claude Desktop 配置文件：
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. 添加以下配置（请根据您的实际路径修改 `cwd` 字段）：

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

3. 重启 Claude Desktop

## 可用的 MCP 工具

### get_serial_status
获取当前串口连接状态和配置信息。

**使用示例：**
```
请帮我检查串口连接状态
```

**返回信息：**
- 连接状态（connected/disconnected）
- 端口名称
- 波特率
- 数据位、停止位、校验位
- 缓冲区统计（待实现）

## 配置文件

### config.json
主配置文件，包含：
- `mcp_host`: MCP 服务监听地址（默认：127.0.0.1）
- `mcp_port`: MCP 服务端口（默认：8000）
- `last_serial_port`: 上次使用的串口
- `last_baud_rate`: 上次使用的波特率

### presets.json
预设命令配置，包含常用的串口命令：
```json
[
  {"name": "Reboot", "command": "dbg reboot"},
  {"name": "LED On", "command": "dbg led on"},
  {"name": "AT", "command": "AT"},
  {"name": "Version", "command": "AT+GMR"}
]
```

## 故障排除

### 1. MCP 服务无法启动
- 检查端口 8000 是否被占用
- 确认 Python 环境和依赖是否正确安装

### 2. Claude Desktop 无法连接
- 检查配置文件路径是否正确
- 确认 `cwd` 路径指向项目目录
- 重启 Claude Desktop

### 3. 串口连接问题
- 确认串口设备已连接
- 检查串口权限（Linux/macOS）
- 确认波特率设置正确

## 开发扩展

要添加新的 MCP 工具，请在 `mcp_server.py` 的 `McpService.__init__` 方法中使用装饰器模式：

```python
@self.mcp_server.tool()
async def your_new_tool(param1: str, param2: int) -> dict:
    """您的新工具描述"""
    # 实现您的功能
    return {"result": "success"}
```

## 技术支持

如有问题，请检查：
1. 控制台输出的错误信息
2. 配置文件格式是否正确
3. 依赖库是否完整安装 