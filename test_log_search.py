#!/usr/bin/env python3
"""
测试日志搜索功能的脚本
"""

from service import SerialService
from mcp_server import set_serial_service, query_serial_logs, get_log_buffer_info, clear_log_buffer

def test_log_search():
    """测试日志搜索功能"""
    print("=== 测试日志搜索功能 ===")
    
    # 创建串口服务实例
    serial_service = SerialService(max_log_lines=50)
    set_serial_service(serial_service)
    
    # 模拟添加一些日志条目
    test_logs = [
        "System startup complete",
        "reminder: Check battery level",
        "Error: Connection timeout",
        "reminder: Update firmware",
        "Info: Temperature = 25.3°C",
        "Warning: Low memory",
        "reminder: Calibrate sensors",
        "Debug: Processing data packet",
    ]
    
    print("添加测试日志条目...")
    for log in test_logs:
        serial_service.add_log_entry(log)
    
    # 测试缓冲区信息
    print("\n1. 测试缓冲区信息:")
    buffer_info = get_log_buffer_info()
    print(f"   缓冲区大小: {buffer_info['buffer_size']}")
    print(f"   最大缓冲区大小: {buffer_info['max_buffer_size']}")
    
    # 测试搜索 "reminder" 关键字
    print("\n2. 搜索包含 'reminder' 的日志:")
    result = query_serial_logs(".*reminder.*", max_results=10)
    print(f"   状态: {result['status']}")
    print(f"   消息: {result['message']}")
    print(f"   匹配数量: {result['total_matches']}")
    for i, match in enumerate(result['matches'], 1):
        print(f"   {i}. {match}")
    
    # 测试正则表达式搜索
    print("\n3. 使用正则表达式搜索以 'Error' 或 'Warning' 开头的日志:")
    result = query_serial_logs("^.*(?:Error|Warning):.*$", max_results=10)
    print(f"   状态: {result['status']}")
    print(f"   消息: {result['message']}")
    print(f"   匹配数量: {result['total_matches']}")
    for i, match in enumerate(result['matches'], 1):
        print(f"   {i}. {match}")
    
    # 测试温度相关的搜索
    print("\n4. 搜索温度相关信息 (包含数字和°C):")
    result = query_serial_logs(r".*Temperature.*\d+\.\d+°C.*", max_results=10)
    print(f"   状态: {result['status']}")
    print(f"   消息: {result['message']}")
    print(f"   匹配数量: {result['total_matches']}")
    for i, match in enumerate(result['matches'], 1):
        print(f"   {i}. {match}")
    
    # 测试无效正则表达式
    print("\n5. 测试无效正则表达式:")
    result = query_serial_logs("[invalid regex", max_results=10)
    print(f"   状态: {result['status']}")
    print(f"   消息: {result['message']}")
    
    # 测试清空缓冲区
    print("\n6. 清空日志缓冲区:")
    clear_result = clear_log_buffer()
    print(f"   状态: {clear_result['status']}")
    print(f"   消息: {clear_result['message']}")
    
    # 验证缓冲区已清空
    buffer_info_after = get_log_buffer_info()
    print(f"   清空后缓冲区大小: {buffer_info_after['buffer_size']}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_log_search()