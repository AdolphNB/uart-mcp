#!/usr/bin/env python3
"""
UART MCP 服务器 - 仅 MCP 模式
专门用于 MCP 客户端连接，不启动 GUI 界面
"""

import asyncio
import sys

from service import SerialService
from mcp_server import McpService

def main():
    """启动 MCP 服务器（同步版本，更简单）"""
    print("正在启动 UART MCP 服务器...")
    
    # 创建共享的串口服务实例
    serial_service = SerialService()
    
    # 创建 MCP 服务
    mcp_service = McpService(serial_service)
    
    try:
        # 启动 MCP 服务器（STDIO 模式）
        mcp_service.start()
    except KeyboardInterrupt:
        print("\n正在关闭 MCP 服务器...")
        serial_service.disconnect()
        print("MCP 服务器已关闭")

if __name__ == "__main__":
    main() 