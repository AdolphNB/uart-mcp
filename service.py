import serial
import serial.tools.list_ports
import threading
from datetime import datetime
from collections import deque
from PyQt6.QtCore import QObject, pyqtSignal

class SerialService(QObject):
    """
    封装了所有串口通信逻辑的服务层。
    这个类是线程安全的，可以在GUI和MCP服务之间共享。
    """
    # Signals for GUI to connect to
    data_received = pyqtSignal(str)
    connection_status_changed = pyqtSignal(bool, str) # is_connected, message
    error_occurred = pyqtSignal(str)

    def __init__(self, max_log_lines=1000):
        super().__init__()
        self.serial_port = None
        self._is_running = False
        self._reader_thread = None
        self._lock = threading.Lock()
        
        # 日志缓冲区 - 使用 deque 实现固定大小的环形缓冲区
        self.max_log_lines = max_log_lines
        self._log_buffer = deque(maxlen=max_log_lines)
        self._log_lock = threading.Lock()

    def get_available_ports(self):
        """获取系统上所有可用的串口列表"""
        return serial.tools.list_ports.comports()

    def connect(self, port, baudrate):
        """连接到指定的串口"""
        with self._lock:
            if self.serial_port and self.serial_port.is_open:
                if self.serial_port.port == port and self.serial_port.baudrate == baudrate:
                    return # Already connected to the same port
                self.disconnect() # Disconnect if connecting to a new port

            try:
                self.serial_port = serial.Serial(port, baudrate, timeout=0.1)
                self._is_running = True
                self._reader_thread = threading.Thread(target=self._read_data, daemon=True)
                self._reader_thread.start()
                self.connection_status_changed.emit(True, f"已连接到 {port} @ {baudrate} bps")
                return True
            except serial.SerialException as e:
                self.error_occurred.emit(f"无法打开串口 {port}: {e}")
                self.serial_port = None
                return False

    def disconnect(self):
        """断开当前串口连接"""
        with self._lock:
            if self.serial_port and self.serial_port.is_open:
                self._is_running = False
                # The thread will exit on its own
                self.serial_port.close()
                self.serial_port = None
                self.connection_status_changed.emit(False, "连接已断开")

    def send(self, data, is_hex=False, add_newline=True):
        """发送数据到串口"""
        with self._lock:
            if not self.is_connected():
                self.error_occurred.emit("发送失败: 串口未连接。")
                return False
            
            try:
                if is_hex:
                    byte_data = bytes.fromhex(data.replace(" ", ""))
                else:
                    if add_newline:
                        data += '\r\n'
                    byte_data = data.encode('utf-8')
                
                self.serial_port.write(byte_data)
                return True
            except (ValueError, serial.SerialException) as e:
                self.error_occurred.emit(f"发送失败: {e}")
                return False

    def is_connected(self):
        """检查串口是否连接"""
        return self.serial_port is not None and self.serial_port.is_open

    def add_log_entry(self, log_line: str):
        """添加日志条目到缓冲区"""
        with self._log_lock:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            timestamped_line = f"[{timestamp}] {log_line}"
            self._log_buffer.append(timestamped_line)

    def get_log_buffer(self):
        """获取当前日志缓冲区的所有内容"""
        with self._log_lock:
            return list(self._log_buffer)

    def clear_log_buffer(self):
        """清空日志缓冲区"""
        with self._log_lock:
            self._log_buffer.clear()

    def search_logs(self, pattern: str, max_results: int = 100):
        """在日志缓冲区中搜索匹配正则表达式的行"""
        import re
        try:
            regex = re.compile(pattern)
            with self._log_lock:
                matches = []
                for line in self._log_buffer:
                    if regex.search(line):
                        matches.append(line)
                        if len(matches) >= max_results:
                            break
                return matches
        except re.error as e:
            raise ValueError(f"无效的正则表达式: {e}")

    def _read_data(self):
        """在后台线程中持续读取串口数据"""
        while self._is_running:
            try:
                # Check running flag again in case disconnect was called
                if not self.serial_port or not self.serial_port.is_open:
                    break
                
                # For now, we will just read lines for simplicity.
                # A more robust solution might read bytes and use a buffer.
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline()
                    if line:
                        # 尝试解码为文本
                        try:
                            decoded_line = line.decode('utf-8').strip()
                            # 添加到日志缓冲区
                            self.add_log_entry(decoded_line)
                            # 发送原始 hex 数据给 GUI
                            self.data_received.emit(line.hex())
                        except UnicodeDecodeError:
                            # 如果无法解码为文本，仍然添加 hex 表示到日志
                            hex_repr = line.hex().upper()
                            self.add_log_entry(f"[HEX] {hex_repr}")
                            self.data_received.emit(line.hex())
            except serial.SerialException as e:
                self._is_running = False
                self.error_occurred.emit(f"串口错误: {e}")
                self.connection_status_changed.emit(False, "连接因错误而中断")
            except Exception as e:
                # Catch unexpected errors to prevent thread crash
                self._is_running = False
                self.error_occurred.emit(f"读取线程发生未知错误: {e}")

        # Clean up after loop exits
        with self._lock:
            if self.serial_port:
                self.serial_port.close()
            self.serial_port = None 