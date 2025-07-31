import asyncio
from mcp.server.fastmcp import FastMCP
from service import SerialService
import config

# 创建全局的串口服务实例（将在主程序中设置）
serial_service = None

# 创建 MCP 服务器实例
mcp = FastMCP("UART MCP Tool")

@mcp.tool()
def get_serial_status() -> dict:
    """获取当前串口连接状态和配置信息。"""
    if serial_service and serial_service.is_connected():
        port_info = serial_service.serial_port
        status = {
            "status": "connected",
            "port": port_info.port,
            "baudrate": port_info.baudrate,
            "bytesize": port_info.bytesize,
            "parity": port_info.parity,
            "stopbits": port_info.stopbits,
            # TODO: Add buffer statistics as per requirements
            "buffer_stats": "Not implemented yet"
        }
    else:
        status = {
            "status": "disconnected",
            "port": None,
            "baudrate": None
        }
    return status

# TODO: 添加更多工具
# @mcp.tool()
# def send_serial_command(command: str, is_hex: bool = False, add_newline: bool = True) -> dict:
#     """发送命令到串口设备"""
#     # 实现发送逻辑
#     pass

def set_serial_service(service: SerialService):
    """设置全局串口服务实例"""
    global serial_service
    serial_service = service

class McpService:
    """
    运行MCP服务器，处理来自LLM的请求。
    简化版本，基于标准 FastMCP 模式，仅支持 STDIO 传输。
    """
    def __init__(self, serial_service: SerialService):
        # 设置全局串口服务
        set_serial_service(serial_service)

    def start(self):
        """启动MCP服务器（STDIO 模式）"""
        print("MCP Server starting (STDIO mode)")
        mcp.run(transport="stdio")

    def stop(self):
        """停止MCP服务器"""
        print("MCP Server stopping.")
        # STDIO 模式下无需显式停止

if __name__ == '__main__':
    # This is for testing the MCP server independently.
    async def main():
        # In a real scenario, SerialService is shared. Here, we create a new one.
        serial_service = SerialService()
        mcp_service = McpService(serial_service)
        
        # To test, you could manually connect the service here if you have a device
        # For example:
        # success = serial_service.connect('COM3', 115200)
        # if not success:
        #     print("Could not connect to serial port for testing.")

        await mcp_service.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("MCP Server stopped by user.") 