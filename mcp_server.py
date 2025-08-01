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

@mcp.tool()
def query_serial_logs(pattern: str, max_results: int = 100) -> dict:
    """在串口日志缓冲区中搜索匹配正则表达式的行
    
    Args:
        pattern: 正则表达式模式，例如 "^.*reminder.*$"
        max_results: 最大返回结果数量，默认100
    
    Returns:
        包含匹配行和统计信息的字典
    """
    if not serial_service:
        return {
            "status": "error",
            "message": "串口服务未初始化",
            "matches": [],
            "total_matches": 0,
            "buffer_size": 0
        }
    
    try:
        # 搜索日志
        matches = serial_service.search_logs(pattern, max_results)
        buffer_size = len(serial_service.get_log_buffer())
        
        return {
            "status": "success",
            "message": f"找到 {len(matches)} 条匹配记录",
            "matches": matches,
            "total_matches": len(matches),
            "buffer_size": buffer_size,
            "pattern": pattern,
            "max_results": max_results
        }
    except ValueError as e:
        return {
            "status": "error",
            "message": str(e),
            "matches": [],
            "total_matches": 0,
            "buffer_size": len(serial_service.get_log_buffer()) if serial_service else 0
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"搜索过程中发生错误: {str(e)}",
            "matches": [],
            "total_matches": 0,
            "buffer_size": len(serial_service.get_log_buffer()) if serial_service else 0
        }

@mcp.tool()
def get_log_buffer_info() -> dict:
    """获取日志缓冲区的基本信息"""
    if not serial_service:
        return {
            "status": "error",
            "message": "串口服务未初始化",
            "buffer_size": 0,
            "max_buffer_size": 0
        }
    
    buffer = serial_service.get_log_buffer()
    return {
        "status": "success",
        "buffer_size": len(buffer),
        "max_buffer_size": serial_service.max_log_lines,
        "oldest_entry": buffer[0] if buffer else None,
        "newest_entry": buffer[-1] if buffer else None
    }

@mcp.tool()
def clear_log_buffer() -> dict:
    """清空串口日志缓冲区"""
    if not serial_service:
        return {
            "status": "error",
            "message": "串口服务未初始化"
        }
    
    try:
        serial_service.clear_log_buffer()
        return {
            "status": "success",
            "message": "日志缓冲区已清空"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"清空缓冲区时发生错误: {str(e)}"
        }

@mcp.tool()
def get_recent_logs(lines: int = 500) -> dict:
    """获取最近N行串口日志（最新接收到的N行）
    
    Args:
        lines: 要获取的日志行数，默认500行
    
    Returns:
        包含最近N行日志和统计信息的字典
    """
    if not serial_service:
        return {
            "status": "error",
            "message": "串口服务未初始化",
            "logs": [],
            "requested_lines": lines,
            "actual_lines": 0,
            "buffer_size": 0
        }
    
    try:
        # 参数验证
        if lines < 0:
            return {
                "status": "error",
                "message": "请求的日志行数不能为负数",
                "logs": [],
                "requested_lines": lines,
                "actual_lines": 0,
                "buffer_size": 0
            }
        
        buffer = serial_service.get_log_buffer()
        buffer_size = len(buffer)
        
        # 获取最近N行（最新的N行）
        if lines == 0:
            recent_logs = []
        elif lines >= buffer_size:
            # 如果请求的行数大于等于缓冲区大小，返回所有日志
            recent_logs = buffer
        else:
            # 取最后N行（最新的N行）
            recent_logs = buffer[-lines:]
        
        return {
            "status": "success",
            "message": f"成功获取最近 {len(recent_logs)} 行日志",
            "logs": recent_logs,
            "requested_lines": lines,
            "actual_lines": len(recent_logs),
            "buffer_size": buffer_size
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取日志时发生错误: {str(e)}",
            "logs": [],
            "requested_lines": lines,
            "actual_lines": 0,
            "buffer_size": len(serial_service.get_log_buffer()) if serial_service else 0
        }

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