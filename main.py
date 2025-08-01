import sys
import asyncio
import threading
from datetime import datetime

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QPushButton, QComboBox, QCheckBox, QLabel, QLineEdit, QSplitter, QMessageBox
from PyQt6.QtCore import Qt, pyqtSlot

import config
from service import SerialService
from mcp_server import McpService

class UartMcpApp(QMainWindow):
    def __init__(self, serial_service, app_config):
        super().__init__()
        self.setWindowTitle("UART MCP Tool")
        self.setGeometry(100, 100, 1200, 800)

        self.serial_service = serial_service
        self.config = app_config

        # --- UI Setup (same as before, but remove direct serial logic) ---
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Create a splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # --- Left Panel: Configuration ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        port_config_label = QLabel("端口配置")
        left_layout.addWidget(port_config_label)
        
        self.port_combo = QComboBox()
        left_layout.addWidget(self.port_combo)

        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "115200", "500000", "1000000", "2000000"])
        self.baudrate_combo.setCurrentText(str(self.config.get("last_baud_rate", 115200)))
        left_layout.addWidget(self.baudrate_combo)

        self.connect_button = QPushButton("连接")
        left_layout.addWidget(self.connect_button)
        
        self.refresh_button = QPushButton("刷新列表")
        left_layout.addWidget(self.refresh_button)

        left_layout.addSpacing(20)

        receive_config_label = QLabel("接收配置")
        left_layout.addWidget(receive_config_label)
        self.hex_receive_checkbox = QCheckBox("HEX显示")
        left_layout.addWidget(self.hex_receive_checkbox)

        left_layout.addSpacing(20)

        send_config_label = QLabel("发送配置")
        left_layout.addWidget(send_config_label)
        self.hex_send_checkbox = QCheckBox("HEX发送")
        left_layout.addWidget(self.hex_send_checkbox)
        self.add_newline_checkbox = QCheckBox("发送 \\r\\n")
        self.add_newline_checkbox.setChecked(True)
        left_layout.addWidget(self.add_newline_checkbox)

        left_layout.addStretch(1)
        splitter.addWidget(left_panel)

        # --- Center Panel: Receive Display ---
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        self.receive_text = QTextEdit()
        self.receive_text.setReadOnly(True)
        self.receive_text.setStyleSheet("background-color: #2b2b2b; color: #f0f0f0; font-family: 'Courier New';")
        center_layout.addWidget(self.receive_text)

        # 创建清空按钮的水平布局
        clear_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("清空全部")
        self.clear_button.setToolTip("清空显示内容和日志缓冲区")
        clear_layout.addWidget(self.clear_button)
        
        self.clear_display_only_button = QPushButton("仅清空显示")
        self.clear_display_only_button.setToolTip("仅清空显示内容，保留日志缓冲区")
        clear_layout.addWidget(self.clear_display_only_button)
        
        center_layout.addLayout(clear_layout)
        splitter.addWidget(center_panel)

        # --- Right Panel: Functions ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        filter_label = QLabel("过滤日志")
        right_layout.addWidget(filter_label)
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("输入关键字过滤...")
        right_layout.addWidget(self.filter_input)
        self.filter_output = QTextEdit()
        self.filter_output.setReadOnly(True)
        self.filter_output.setStyleSheet("background-color: #2b2b2b; color: #a9b7c6;")
        right_layout.addWidget(self.filter_output)

        send_label = QLabel("发送区域")
        right_layout.addWidget(send_label)
        self.send_input = QLineEdit()
        self.send_input.setPlaceholderText("输入要发送的命令...")
        right_layout.addWidget(self.send_input)
        
        self.send_button = QPushButton("发送")
        right_layout.addWidget(self.send_button)

        right_layout.addSpacing(20)

        preset_label = QLabel("预设命令")
        right_layout.addWidget(preset_label)
        
        presets = config.load_presets()
        self.setup_preset_buttons(right_layout, presets)

        right_layout.addStretch(1)
        splitter.addWidget(right_panel)

        splitter.setSizes([200, 700, 300])

        self.apply_stylesheet()
        self.populate_ports()
        self.connect_signals()
        self.restore_last_port()

    def populate_ports(self):
        """从SerialService获取并填充可用串口列表"""
        self.port_combo.clear()
        ports = self.serial_service.get_available_ports()
        if not ports:
            self.port_combo.addItem("无可用串口")
        else:
            self.port_combo.addItems([port.device for port in ports])
    
    def restore_last_port(self):
        """尝试选择上次使用的端口。"""
        last_port = self.config.get("last_serial_port")
        if last_port:
            index = self.port_combo.findText(last_port)
            if index != -1:
                self.port_combo.setCurrentIndex(index)

    def connect_signals(self):
        """连接所有UI组件的信号与服务层的信号"""
        # UI component signals
        self.connect_button.clicked.connect(self.toggle_connection)
        self.refresh_button.clicked.connect(self.populate_ports)
        self.clear_button.clicked.connect(self.clear_display)
        self.clear_display_only_button.clicked.connect(self.clear_display_only)
        self.send_button.clicked.connect(self.send_command)
        self.filter_input.textChanged.connect(self.filter_logs)

        # SerialService signals
        self.serial_service.data_received.connect(self.handle_data_received)
        self.serial_service.connection_status_changed.connect(self.handle_connection_status)
        self.serial_service.error_occurred.connect(self.handle_serial_error)

    def toggle_connection(self):
        """切换串口连接状态"""
        if self.serial_service.is_connected():
            self.serial_service.disconnect()
        else:
            port_name = self.port_combo.currentText()
            if port_name == "无可用串口":
                QMessageBox.warning(self, "连接错误", "没有可用的串口。")
                return
            baud_rate = int(self.baudrate_combo.currentText())
            if not self.serial_service.connect(port_name, baud_rate):
                QMessageBox.critical(self, "连接失败", f"无法打开串口 {port_name}")

    @pyqtSlot(bool, str)
    def handle_connection_status(self, is_connected, message):
        """处理来自服务层的连接状态变化"""
        self.append_to_log(f"--- {message} ---")
        if is_connected:
            self.connect_button.setText("断开")
            self.port_combo.setEnabled(False)
            self.baudrate_combo.setEnabled(False)
            self.refresh_button.setEnabled(False)
        else:
            self.connect_button.setText("连接")
            self.port_combo.setEnabled(True)
            self.baudrate_combo.setEnabled(True)
            self.refresh_button.setEnabled(True)

    def send_command(self):
        """发送命令到串口"""
        command_text = self.send_input.text()
        if not command_text:
            return

        is_hex = self.hex_send_checkbox.isChecked()
        add_newline = self.add_newline_checkbox.isChecked()

        if self.serial_service.send(command_text, is_hex, add_newline):
            display_command = command_text.upper() if is_hex else command_text
            self.append_to_log(f"[SENT] {display_command}")
            self.send_input.clear()

    @pyqtSlot(str)
    def handle_data_received(self, hex_data):
        """处理来自服务层的原始HEX数据"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        display_text = ""
        
        if self.hex_receive_checkbox.isChecked():
            # Format hex data with spaces
            display_text = ' '.join(hex_data[i:i+2] for i in range(0, len(hex_data), 2)).upper()
        else:
            try:
                display_text = bytes.fromhex(hex_data).decode('utf-8').strip()
            except (UnicodeDecodeError, ValueError):
                display_text = f"[INVALID UTF-8] {' '.join(hex_data[i:i+2] for i in range(0, len(hex_data), 2)).upper()}"

        self.append_to_log(f"[{timestamp}] {display_text}")

    @pyqtSlot(str)
    def handle_serial_error(self, error_message):
        """处理来自服务层的错误"""
        self.append_to_log(f"--- 错误: {error_message} ---")
        # Optionally show a popup for critical errors
        if "无法打开" in error_message or "发送失败" in error_message:
             QMessageBox.warning(self, "串口错误", error_message)
        
    def setup_preset_buttons(self, layout, presets):
        """根据配置动态创建预设命令按钮"""
        grid_layout = QHBoxLayout()
        current_row_widget = QWidget()
        current_row_layout = QHBoxLayout(current_row_widget)
        
        max_buttons_per_row = 2 

        for preset in presets:
            btn_name = preset.get("name", "No Name")
            command = preset.get("command", "")
            if not command:
                continue

            button = QPushButton(btn_name)
            button.clicked.connect(lambda checked, cmd=command: self.send_preset_command(cmd))
            current_row_layout.addWidget(button)
            if current_row_layout.count() >= max_buttons_per_row:
                layout.addWidget(current_row_widget)
                current_row_widget = QWidget()
                current_row_layout = QHBoxLayout(current_row_widget)

        if current_row_layout.count() > 0:
            layout.addWidget(current_row_widget)
            
    def send_preset_command(self, command):
        """填充并发送预设命令"""
        self.send_input.setText(command)
        self.send_command()

    def append_to_log(self, text):
        """在接收区追加文本并自动滚动"""
        self.receive_text.append(text)
        self.filter_logs()
    
    def clear_display(self):
        """清空接收显示区和底层日志缓冲区"""
        # 询问用户确认
        reply = QMessageBox.question(
            self, 
            '确认清空', 
            '这将清空显示内容和所有日志缓冲区数据，此操作不可撤销。\n\n确定要继续吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 清空GUI显示
            self.receive_text.clear()
            self.filter_output.clear()
            
            # 同时清空串口服务的日志缓冲区
            if self.serial_service:
                buffer_size = len(self.serial_service.get_log_buffer())
                self.serial_service.clear_log_buffer()
                self.append_to_log(f"--- 已清空显示和日志缓冲区 (原有 {buffer_size} 条记录) ---")

    def clear_display_only(self):
        """仅清空显示区域，保留日志缓冲区"""
        self.receive_text.clear()
        self.filter_output.clear()
        self.append_to_log("--- 已清空显示内容 (日志缓冲区保留) ---")

    def filter_logs(self):
        """根据关键字过滤主显示区的内容"""
        keyword = self.filter_input.text()
        self.filter_output.clear()
        if not keyword:
            return
        full_log = self.receive_text.toPlainText()
        matching_lines = [line for line in full_log.splitlines() if keyword in line]
        self.filter_output.setText("\n".join(matching_lines))

    def closeEvent(self, event):
        """保存配置并干净地关闭"""
        # Save current settings
        self.config["last_serial_port"] = self.port_combo.currentText() if self.port_combo.currentText() != "无可用串口" else ""
        self.config["last_baud_rate"] = int(self.baudrate_combo.currentText())
        config.save_config(self.config)

        self.serial_service.disconnect()
        event.accept()

    def apply_stylesheet(self):
        """应用样式表"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #3c3c3c;
            }
            QWidget {
                color: #f0f0f0;
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 5px;
            }
            QComboBox, QLineEdit, QPushButton {
                padding: 5px;
                background-color: #555;
                border: 1px solid #666;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QPushButton:pressed {
                background-color: #777;
            }
            QSplitter::handle {
                background: #555;
            }
            QSplitter::handle:horizontal {
                width: 5px;
            }
            QSplitter::handle:vertical {
                height: 5px;
            }
        """)

def run_mcp_service(mcp_service: McpService):
    """Function to run the MCP service in STDIO mode."""
    try:
        # 启动 STDIO 模式的 MCP 服务
        mcp_service.start()
    except Exception as e:
        print(f"MCP Service thread encountered an error: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    app_config = config.load_config()

    # Create the shared service instance
    serial_service = SerialService()
    
    # Create the GUI window
    window = UartMcpApp(serial_service, app_config)
    window.show()
    
    # Create and start the MCP service in a background daemon thread (STDIO mode)
    mcp_service = McpService(serial_service)
    mcp_thread = threading.Thread(target=run_mcp_service, args=(mcp_service,), daemon=True)
    mcp_thread.start()
    
    sys.exit(app.exec())
