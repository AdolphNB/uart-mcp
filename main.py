import sys
import asyncio
import threading
from datetime import datetime

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QPushButton, QComboBox, QCheckBox, QLabel, QLineEdit, QSplitter, QMessageBox, QDialog, QTabWidget, QTextBrowser, QTableWidget, QTableWidgetItem, QHeaderView
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

        # --- UI Setup ---
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
        self.show_timestamp_checkbox = QCheckBox("显示时间戳")
        self.show_timestamp_checkbox.setChecked(self.config.get("show_timestamp", True))
        left_layout.addWidget(self.show_timestamp_checkbox)

        left_layout.addSpacing(20)

        send_config_label = QLabel("发送配置")
        left_layout.addWidget(send_config_label)
        self.hex_send_checkbox = QCheckBox("HEX发送")
        left_layout.addWidget(self.hex_send_checkbox)
        self.add_newline_checkbox = QCheckBox("发送 \\r\\n")
        self.add_newline_checkbox.setChecked(True)
        left_layout.addWidget(self.add_newline_checkbox)

        left_layout.addStretch(1)
        
        # 设置按钮
        self.settings_button = QPushButton("设置")
        self.settings_button.setToolTip("打开设置对话框")
        left_layout.addWidget(self.settings_button)
        
        splitter.addWidget(left_panel)

        # --- Center Panel: Receive Display ---
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        self.receive_text = QTextEdit()
        self.receive_text.setReadOnly(True)
        self.receive_text.setStyleSheet("background-color: #2b2b2b; color: #f0f0f0; font-family: 'Courier New';")
        center_layout.addWidget(self.receive_text)

        # 创建清空按钮
        self.clear_button = QPushButton("清空全部")
        self.clear_button.setToolTip("清空显示内容和日志缓冲区")
        center_layout.addWidget(self.clear_button)
        splitter.addWidget(center_panel)

        # --- Right Panel: Functions ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 过滤日志区域（占2/3空间）
        filter_label = QLabel("过滤日志")
        right_layout.addWidget(filter_label)
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("输入关键字过滤...")
        right_layout.addWidget(self.filter_input)
        self.filter_output = QTextEdit()
        self.filter_output.setReadOnly(True)
        self.filter_output.setStyleSheet("background-color: #2b2b2b; color: #a9b7c6;")
        right_layout.addWidget(self.filter_output, 2)  # 设置stretch因子为2，占2/3空间

        # 发送区域（占1/3空间）  
        send_widget = QWidget()
        send_layout = QVBoxLayout(send_widget)
        send_layout.setContentsMargins(0, 10, 0, 0)
        
        send_label = QLabel("发送区域")
        send_layout.addWidget(send_label)
        self.send_input = QLineEdit()
        self.send_input.setPlaceholderText("输入要发送的命令...")
        send_layout.addWidget(self.send_input)
        
        self.send_button = QPushButton("发送")
        send_layout.addWidget(self.send_button)

        send_layout.addSpacing(10)

        preset_label = QLabel("预设命令")
        send_layout.addWidget(preset_label)
        
        presets = config.load_presets()
        self.preset_layout = send_layout  # 保存引用以便重新加载
        self.setup_preset_buttons(send_layout, presets)

        send_layout.addStretch(1)
        right_layout.addWidget(send_widget, 1)  # 设置stretch因子为1，占1/3空间
        splitter.addWidget(right_panel)

        splitter.setSizes([150, 650, 400])

        self.apply_stylesheet()
        self.populate_ports()
        self.connect_signals()
        self.restore_last_port()
        
        # 初始化SerialService的时间戳设置
        self.serial_service.set_show_timestamp(self.config.get("show_timestamp", True))

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
        self.send_button.clicked.connect(self.send_command)
        self.filter_input.textChanged.connect(self.filter_logs)
        self.show_timestamp_checkbox.toggled.connect(self.toggle_timestamp)
        self.settings_button.clicked.connect(self.show_settings_dialog)

        # SerialService signals
        self.serial_service.data_received.connect(self.handle_data_received)
        self.serial_service.text_data_received.connect(self.handle_text_data_received)
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
    
    def toggle_timestamp(self, checked):
        """切换时间戳显示设置"""
        self.serial_service.set_show_timestamp(checked)
        # 保存设置到配置文件
        self.config["show_timestamp"] = checked
        config.save_config(self.config)

    @pyqtSlot(str)
    def handle_text_data_received(self, text_data):
        """处理来自服务层的文本数据（仅在文本显示模式下使用）"""
        # 只在非HEX显示模式下处理文本数据
        if not self.hex_receive_checkbox.isChecked():
            display_text = text_data
            
            # 根据时间戳设置决定是否添加时间戳
            if self.show_timestamp_checkbox.isChecked():
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                display_text = f"[{timestamp}] {text_data}"
            
            self.append_to_log(display_text)

    @pyqtSlot(str)
    def handle_data_received(self, hex_data):
        """处理来自服务层的原始HEX数据（仅在HEX显示模式下使用）"""
        # 只在HEX显示模式下处理HEX数据
        if self.hex_receive_checkbox.isChecked():
            # Format hex data with spaces
            display_text = ' '.join(hex_data[i:i+2] for i in range(0, len(hex_data), 2)).upper()
            
            # 根据时间戳设置决定是否添加时间戳
            if self.show_timestamp_checkbox.isChecked():
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                display_text = f"[{timestamp}] {display_text}"
            
            self.append_to_log(display_text)

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
            button.setObjectName(f"preset_{btn_name}")  # 设置对象名称以便删除
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
        # 清空GUI显示
        self.receive_text.clear()
        self.filter_output.clear()
        
        # 同时清空串口服务的日志缓冲区
        if self.serial_service:
            buffer_size = len(self.serial_service.get_log_buffer())
            self.serial_service.clear_log_buffer()
            self.append_to_log(f"--- 已清空显示和日志缓冲区 (原有 {buffer_size} 条记录) ---")



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

    def show_settings_dialog(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 处理设置变更
            self.apply_settings_changes(dialog.get_settings())
    
    def apply_settings_changes(self, settings):
        """应用设置变更"""
        # 保存语言设置
        if 'language' in settings:
            self.config['language'] = settings['language']
            config.save_config(self.config)
            # 这里可以添加重新加载界面语言的逻辑
            
        # 保存预设命令变更
        if 'presets' in settings:
            config.save_presets(settings['presets'])
            # 重新加载预设按钮
            self.reload_preset_buttons()
    
    def reload_preset_buttons(self):
        """重新加载预设命令按钮"""
        presets = config.load_presets()
        # 找到预设按钮的容器并清空
        for i in reversed(range(self.preset_layout.count())):
            item = self.preset_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget and hasattr(widget, 'layout') and widget.layout():
                    # 检查是否包含预设按钮
                    for j in reversed(range(widget.layout().count())):
                        button_item = widget.layout().itemAt(j)
                        if button_item:
                            button = button_item.widget()
                            if button and hasattr(button, 'objectName') and button.objectName().startswith('preset_'):
                                widget.setParent(None)
                                break
        # 重新创建预设按钮
        self.setup_preset_buttons(self.preset_layout, presets)


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, config_data, parent=None):
        super().__init__(parent)
        self.config_data = config_data
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("设置")
        self.setFixedSize(600, 500)
        
        # 应用暗色主题样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #f0f0f0;
            }
            QTabWidget {
                background-color: #2b2b2b;
                border: none;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2b2b2b;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #444;
                color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #555;
            }
            QTabBar::tab:hover {
                background-color: #666;
            }
            QLabel {
                color: #f0f0f0;
                font-size: 14px;
                margin-bottom: 5px;
            }
            QComboBox, QLineEdit, QPushButton {
                padding: 5px;
                background-color: #555;
                border: 1px solid #666;
                border-radius: 3px;
                color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QPushButton:pressed {
                background-color: #777;
            }
            QTextBrowser {
                background-color: #333;
                border: 1px solid #555;
                padding: 10px;
                font-family: 'Courier New', monospace;
                color: #f0f0f0;
            }
            QTableWidget {
                background-color: #333;
                border: 1px solid #555;
                gridline-color: #555;
                color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #555;
            }
            QTableWidget::item:selected {
                background-color: #555;
            }
            QHeaderView::section {
                background-color: #444;
                color: #f0f0f0;
                padding: 8px;
                border: 1px solid #555;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 标签1：语言切换
        self.language_tab = self.create_language_tab()
        tab_widget.addTab(self.language_tab, "语言设置")
        
        # 标签2：MCP配置参考
        self.mcp_tab = self.create_mcp_config_tab()
        tab_widget.addTab(self.mcp_tab, "MCP配置")
        
        # 标签3：预设命令配置
        self.presets_tab = self.create_presets_tab()
        tab_widget.addTab(self.presets_tab, "预设命令")
        
        # 底部按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)
    
    def create_language_tab(self):
        """创建语言设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("界面显示语言:")
        layout.addWidget(label)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "中文"])
        current_language = self.config_data.get('language', 'English')
        if current_language == 'Chinese':
            self.language_combo.setCurrentText("中文")
        else:
            self.language_combo.setCurrentText("English")
        
        layout.addWidget(self.language_combo)
        layout.addStretch(1)
        
        return widget
    
    def create_mcp_config_tab(self):
        """创建MCP配置参考标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Claude Desktop MCP 配置参考:")
        layout.addWidget(label)
        
        # 创建文本浏览器显示配置
        text_browser = QTextBrowser()
        mcp_config_text = """{
  "mcpServers": {
    "uart-mcp": {
      "command": "uv",
      "args": ["run", "python", "mcp_only.py"],
      "cwd": "D:\\\\workspace\\\\pythonTools\\\\uart-mcp",
      "env": {
        "PYTHONPATH": "D:\\\\workspace\\\\pythonTools\\\\uart-mcp"
      }
    }
  }
}

配置文件位置:
- Windows: %APPDATA%\\Claude\\claude_desktop_config.json
- macOS: ~/Library/Application Support/Claude/claude_desktop_config.json  
- Linux: ~/.config/Claude/claude_desktop_config.json

注意: 请将 "cwd" 路径修改为您实际的项目目录路径。"""
        
        text_browser.setText(mcp_config_text)
        layout.addWidget(text_browser)
        
        return widget
    
    def create_presets_tab(self):
        """创建预设命令配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("预设命令配置:")
        layout.addWidget(label)
        
        # 创建表格显示预设命令
        self.presets_table = QTableWidget()
        self.presets_table.setColumnCount(2)
        self.presets_table.setHorizontalHeaderLabels(["名称", "命令"])
        
        # 设置表格属性
        header = self.presets_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # 加载现有预设
        self.load_presets_to_table()
        
        layout.addWidget(self.presets_table)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        self.add_preset_button = QPushButton("添加")
        self.remove_preset_button = QPushButton("删除")
        self.reset_presets_button = QPushButton("重置为默认")
        
        self.add_preset_button.clicked.connect(self.add_preset_row)
        self.remove_preset_button.clicked.connect(self.remove_preset_row)
        self.reset_presets_button.clicked.connect(self.reset_presets)
        
        buttons_layout.addWidget(self.add_preset_button)
        buttons_layout.addWidget(self.remove_preset_button)
        buttons_layout.addWidget(self.reset_presets_button)
        buttons_layout.addStretch(1)
        
        layout.addLayout(buttons_layout)
        
        return widget
    
    def load_presets_to_table(self):
        """加载预设命令到表格"""
        presets = config.load_presets()
        self.presets_table.setRowCount(len(presets))
        
        for i, preset in enumerate(presets):
            name_item = QTableWidgetItem(preset.get('name', ''))
            command_item = QTableWidgetItem(preset.get('command', ''))
            self.presets_table.setItem(i, 0, name_item)
            self.presets_table.setItem(i, 1, command_item)
    
    def add_preset_row(self):
        """添加预设命令行"""
        row_count = self.presets_table.rowCount()
        self.presets_table.insertRow(row_count)
        self.presets_table.setItem(row_count, 0, QTableWidgetItem("新命令"))
        self.presets_table.setItem(row_count, 1, QTableWidgetItem(""))
    
    def remove_preset_row(self):
        """删除选中的预设命令行"""
        current_row = self.presets_table.currentRow()
        if current_row >= 0:
            self.presets_table.removeRow(current_row)
    
    def reset_presets(self):
        """重置为默认预设命令"""
        reply = QMessageBox.question(self, "确认重置", "确定要重置为默认预设命令吗？这将删除所有自定义预设。",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # 清空表格并加载默认预设
            self.presets_table.setRowCount(0)
            default_presets = [
                {"name": "Reboot", "command": "dbg reboot"},
                {"name": "ADFU Mode", "command": "dbg reboot adfu"},
                {"name": "AT Command", "command": "AT"},
                {"name": "Version", "command": "AT+GMR"}
            ]
            self.presets_table.setRowCount(len(default_presets))
            for i, preset in enumerate(default_presets):
                self.presets_table.setItem(i, 0, QTableWidgetItem(preset['name']))
                self.presets_table.setItem(i, 1, QTableWidgetItem(preset['command']))
    
    def get_settings(self):
        """获取设置数据"""
        settings = {}
        
        # 语言设置
        language_text = self.language_combo.currentText()
        settings['language'] = 'Chinese' if language_text == '中文' else 'English'
        
        # 预设命令设置
        presets = []
        for i in range(self.presets_table.rowCount()):
            name_item = self.presets_table.item(i, 0)
            command_item = self.presets_table.item(i, 1)
            if name_item and command_item:
                name = name_item.text().strip()
                command = command_item.text().strip()
                if name and command:  # 只保存非空的预设
                    presets.append({"name": name, "command": command})
        settings['presets'] = presets
        
        return settings


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
