import sys
import asyncio
import threading
from datetime import datetime

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QPushButton, QComboBox, QCheckBox, QLabel, QLineEdit, QSplitter, QMessageBox, QDialog, QTabWidget, QTextBrowser, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, pyqtSlot

import config
from service import SerialService
from mcp_server import McpService

# 语言文本字典
LANGUAGE_TEXTS = {
    'English': {
        'window_title': 'UART MCP Tool',
        'port_config': 'Port Configuration',
        'connect': 'Connect',
        'disconnect': 'Disconnect',
        'refresh_list': 'Refresh List',
        'receive_config': 'Receive Settings',
        'hex_display': 'HEX Display',
        'show_timestamp': 'Show Timestamp',
        'send_config': 'Send Settings',
        'hex_send': 'HEX Send',
        'send_newline': 'Send \\r\\n',
        'settings': 'Settings',
        'clear_all': 'Clear All',
        'filter_logs': 'Filter Logs',
        'filter_placeholder': 'Enter keywords to filter...',
        'send_area': 'Send Area',
        'send_placeholder': 'Enter command to send...',
        'send': 'Send',
        'preset_commands': 'Preset Commands',
        'connected_to': 'Connected to',
        'connection_closed': 'Connection closed',
        'error': 'Error',
        'sent': 'SENT',
        'no_ports': 'No available ports',
        'no_ports_warning': 'No available ports.',
        'cannot_open_port': 'Cannot open port'
    },
    'Chinese': {
        'window_title': 'UART MCP 工具',
        'port_config': '端口配置',
        'connect': '连接',
        'disconnect': '断开',
        'refresh_list': '刷新列表',
        'receive_config': '接收配置',
        'hex_display': 'HEX显示',
        'show_timestamp': '显示时间戳',
        'send_config': '发送配置',
        'hex_send': 'HEX发送',
        'send_newline': '发送 \\r\\n',
        'settings': '设置',
        'clear_all': '清空全部',
        'filter_logs': '过滤日志',
        'filter_placeholder': '输入关键字过滤...',
        'send_area': '发送区域',
        'send_placeholder': '输入要发送的命令...',
        'send': '发送',
        'preset_commands': '预设命令',
        'connected_to': '已连接到',
        'connection_closed': '连接已断开',
        'error': '错误',
        'sent': '发送',
        'no_ports': '无可用串口',
        'no_ports_warning': '没有可用的串口。',
        'cannot_open_port': '无法打开串口',
        # 设置对话框
        'settings_title': '设置',
        'language_tab': '语言设置',
        'mcp_tab': 'MCP配置',
        'presets_tab': '预设命令',
        'language_label': '界面显示语言:',
        'mcp_config_label': 'Claude Desktop MCP 配置参考:',
        'presets_config_label': '预设命令配置:',
        'preset_name': '名称',
        'preset_command': '命令',
        'add_preset': '添加',
        'remove_preset': '删除',
        'reset_presets': '重置为默认',
        'new_command': '新命令',
        'confirm_reset': '确认重置',
        'reset_message': '确定要重置为默认预设命令吗？这将删除所有自定义预设。',
        'ok': '确定',
        'cancel': '取消'
    }
}

# 设置对话框语言文本
SETTINGS_LANGUAGE_TEXTS = {
    'English': {
        'settings_title': 'Settings',
        'language_tab': 'Language',
        'mcp_tab': 'MCP Config',
        'presets_tab': 'Preset Commands',
        'language_label': 'Interface Language:',
        'mcp_config_label': 'Claude Desktop MCP Configuration Reference:',
        'presets_config_label': 'Preset Command Configuration (Max 4):',
        'preset_name': 'Name',
        'preset_command': 'Command',
        'reset_presets': 'Reset to Default',
        'confirm_reset': 'Confirm Reset',
        'reset_message': 'Are you sure you want to reset to default preset commands? This will delete all custom presets.',
        'ok': 'OK',
        'cancel': 'Cancel'
    },
    'Chinese': {
        'settings_title': '设置',
        'language_tab': '语言设置',
        'mcp_tab': 'MCP配置',
        'presets_tab': '预设命令',
        'language_label': '界面显示语言:',
        'mcp_config_label': 'Claude Desktop MCP 配置参考:',
        'presets_config_label': '预设命令配置 (最多4条):',
        'preset_name': '名称',
        'preset_command': '命令',
        'reset_presets': '重置为默认',
        'confirm_reset': '确认重置',
        'reset_message': '确定要重置为默认预设命令吗？这将删除所有自定义预设。',
        'ok': '确定',
        'cancel': '取消'
    }
}

class UartMcpApp(QMainWindow):
    def __init__(self, serial_service, app_config):
        super().__init__()
        
        self.serial_service = serial_service
        self.config = app_config
        
        # 获取当前语言设置
        self.current_language = self.config.get('language', 'English')
        self.texts = LANGUAGE_TEXTS[self.current_language]
        
        self.setWindowTitle(self.texts['window_title'])
        self.setGeometry(100, 100, 1200, 800)

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
        
        self.port_config_label = QLabel(self.texts['port_config'])
        left_layout.addWidget(self.port_config_label)
        
        self.port_combo = QComboBox()
        left_layout.addWidget(self.port_combo)

        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "115200", "500000", "1000000", "2000000"])
        self.baudrate_combo.setCurrentText(str(self.config.get("last_baud_rate", 115200)))
        left_layout.addWidget(self.baudrate_combo)

        self.connect_button = QPushButton(self.texts['connect'])
        left_layout.addWidget(self.connect_button)
        
        self.refresh_button = QPushButton(self.texts['refresh_list'])
        left_layout.addWidget(self.refresh_button)

        left_layout.addSpacing(20)

        self.receive_config_label = QLabel(self.texts['receive_config'])
        left_layout.addWidget(self.receive_config_label)
        self.hex_receive_checkbox = QCheckBox(self.texts['hex_display'])
        left_layout.addWidget(self.hex_receive_checkbox)
        self.show_timestamp_checkbox = QCheckBox(self.texts['show_timestamp'])
        self.show_timestamp_checkbox.setChecked(self.config.get("show_timestamp", True))
        left_layout.addWidget(self.show_timestamp_checkbox)

        left_layout.addSpacing(20)

        self.send_config_label = QLabel(self.texts['send_config'])
        left_layout.addWidget(self.send_config_label)
        self.hex_send_checkbox = QCheckBox(self.texts['hex_send'])
        left_layout.addWidget(self.hex_send_checkbox)
        self.add_newline_checkbox = QCheckBox(self.texts['send_newline'])
        self.add_newline_checkbox.setChecked(True)
        left_layout.addWidget(self.add_newline_checkbox)

        left_layout.addStretch(1)
        
        # 设置按钮
        self.settings_button = QPushButton(self.texts['settings'])
        self.settings_button.setToolTip("Open settings dialog")
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
        self.clear_button = QPushButton(self.texts['clear_all'])
        self.clear_button.setToolTip("Clear display and log buffer")
        center_layout.addWidget(self.clear_button)
        splitter.addWidget(center_panel)

        # --- Right Panel: Functions ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 过滤日志区域（占2/3空间）
        self.filter_label = QLabel(self.texts['filter_logs'])
        right_layout.addWidget(self.filter_label)
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(self.texts['filter_placeholder'])
        right_layout.addWidget(self.filter_input)
        self.filter_output = QTextEdit()
        self.filter_output.setReadOnly(True)
        self.filter_output.setStyleSheet("background-color: #2b2b2b; color: #a9b7c6;")
        right_layout.addWidget(self.filter_output, 2)  # 设置stretch因子为2，占2/3空间

        # 发送区域（占1/3空间）  
        send_widget = QWidget()
        send_layout = QVBoxLayout(send_widget)
        send_layout.setContentsMargins(0, 10, 0, 0)
        
        self.send_label = QLabel(self.texts['send_area'])
        send_layout.addWidget(self.send_label)
        self.send_input = QLineEdit()
        self.send_input.setPlaceholderText(self.texts['send_placeholder'])
        send_layout.addWidget(self.send_input)
        
        self.send_button = QPushButton(self.texts['send'])
        send_layout.addWidget(self.send_button)

        send_layout.addSpacing(10)

        self.preset_label = QLabel(self.texts['preset_commands'])
        send_layout.addWidget(self.preset_label)
        
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

    def set_messagebox_black_font_style(self, msgbox):
        """为消息框设置黑色字体样式"""
        msgbox.setStyleSheet("""
            QMessageBox {
                background-color: #f0f0f0;
                color: #000000;
                font-size: 14px;
            }
            QMessageBox QLabel {
                color: #000000;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #ccc;
                padding: 5px 15px;
                border-radius: 3px;
                font-size: 14px;
            }
            QMessageBox QPushButton:hover {
                background-color: #d0d0d0;
            }
            QMessageBox QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)

    def populate_ports(self):
        """从SerialService获取并填充可用串口列表"""
        self.port_combo.clear()
        ports = self.serial_service.get_available_ports()
        if not ports:
            self.port_combo.addItem(self.texts['no_ports'])
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
            if port_name == self.texts['no_ports']:
                msgbox = QMessageBox()
                msgbox.setIcon(QMessageBox.Icon.Warning)
                msgbox.setWindowTitle(self.texts['error'])
                msgbox.setText(self.texts['no_ports_warning'])
                self.set_messagebox_black_font_style(msgbox)
                msgbox.exec()
                return
            baud_rate = int(self.baudrate_combo.currentText())
            if not self.serial_service.connect(port_name, baud_rate):
                msgbox = QMessageBox()
                msgbox.setIcon(QMessageBox.Icon.Critical)
                msgbox.setWindowTitle(self.texts['error'])
                msgbox.setText(f"{self.texts['cannot_open_port']} {port_name}")
                self.set_messagebox_black_font_style(msgbox)
                msgbox.exec()

    @pyqtSlot(bool, str)
    def handle_connection_status(self, is_connected, message):
        """处理来自服务层的连接状态变化"""
        self.append_to_log(f"--- {message} ---")
        if is_connected:
            self.connect_button.setText(self.texts['disconnect'])
            self.port_combo.setEnabled(False)
            self.baudrate_combo.setEnabled(False)
            self.refresh_button.setEnabled(False)
        else:
            self.connect_button.setText(self.texts['connect'])
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
            self.append_to_log(f"[{self.texts['sent']}] {display_command}")
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
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Icon.Warning)
            msgbox.setWindowTitle("串口错误")
            msgbox.setText(error_message)
            self.set_messagebox_black_font_style(msgbox)
            msgbox.exec()
        
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
            old_language = self.config.get('language', 'English')
            self.config['language'] = settings['language']
            config.save_config(self.config)
            # 如果语言发生变化，更新界面
            if old_language != settings['language']:
                self.update_language(settings['language'])
            
        # 保存预设命令变更
        if 'presets' in settings:
            config.save_presets(settings['presets'])
            # 重新加载预设按钮
            self.reload_preset_buttons()
    
    def update_language(self, language):
        """更新界面语言"""
        self.current_language = language
        self.texts = LANGUAGE_TEXTS[language]
        
        # 更新窗口标题
        self.setWindowTitle(self.texts['window_title'])
        
        # 更新左侧面板
        self.port_config_label.setText(self.texts['port_config'])
        self.connect_button.setText(self.texts['connect'])
        self.refresh_button.setText(self.texts['refresh_list'])
        self.receive_config_label.setText(self.texts['receive_config'])
        self.hex_receive_checkbox.setText(self.texts['hex_display'])
        self.show_timestamp_checkbox.setText(self.texts['show_timestamp'])
        self.send_config_label.setText(self.texts['send_config'])
        self.hex_send_checkbox.setText(self.texts['hex_send'])
        self.add_newline_checkbox.setText(self.texts['send_newline'])
        self.settings_button.setText(self.texts['settings'])
        
        # 更新中间面板
        self.clear_button.setText(self.texts['clear_all'])
        
        # 更新右侧面板
        self.filter_label.setText(self.texts['filter_logs'])
        self.filter_input.setPlaceholderText(self.texts['filter_placeholder'])
        self.send_label.setText(self.texts['send_area'])
        self.send_input.setPlaceholderText(self.texts['send_placeholder'])
        self.send_button.setText(self.texts['send'])
        self.preset_label.setText(self.texts['preset_commands'])
        
        # 更新端口列表
        self.populate_ports()
    
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
        # 获取当前语言设置
        self.current_language = config_data.get('language', 'English')
        self.texts = SETTINGS_LANGUAGE_TEXTS[self.current_language]
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(self.texts['settings_title'])
        self.setFixedSize(600, 500)
    
    def set_messagebox_black_font_style(self, msgbox):
        """为消息框设置黑色字体样式"""
        msgbox.setStyleSheet("""
            QMessageBox {
                background-color: #f0f0f0;
                color: #000000;
                font-size: 14px;
            }
            QMessageBox QLabel {
                color: #000000;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #ccc;
                padding: 5px 15px;
                border-radius: 3px;
                font-size: 14px;
            }
            QMessageBox QPushButton:hover {
                background-color: #d0d0d0;
            }
            QMessageBox QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)
        
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

        """)
        
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 标签1：语言切换
        self.language_tab = self.create_language_tab()
        tab_widget.addTab(self.language_tab, self.texts['language_tab'])
        
        # 标签2：MCP配置参考
        self.mcp_tab = self.create_mcp_config_tab()
        tab_widget.addTab(self.mcp_tab, self.texts['mcp_tab'])
        
        # 标签3：预设命令配置
        self.presets_tab = self.create_presets_tab()
        tab_widget.addTab(self.presets_tab, self.texts['presets_tab'])
        
        # 底部按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        
        self.ok_button = QPushButton(self.texts['ok'])
        self.cancel_button = QPushButton(self.texts['cancel'])
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)
    
    def create_language_tab(self):
        """创建语言设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(self.texts['language_label'])
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
        
        label = QLabel(self.texts['mcp_config_label'])
        layout.addWidget(label)
        
        # 创建文本浏览器显示配置
        text_browser = QTextBrowser()
        mcp_config_text = """{
  "mcpServers": {
    "Alan_zhang_uart": {
      "name": "uart-mcp",
      "type": "stdio",
      "description": "",
      "isActive": false,
      "registryUrl": "",
      "command": "uv",
      "args": [
        "--directory",
        "D:\\workspace\\pythonTools\\uart-mcp",
        "run",
        "main.py"
      ]
    }
  }
}
Cusor or VScode config file location
"""
        
        text_browser.setText(mcp_config_text)
        layout.addWidget(text_browser)
        
        return widget
    
    def create_presets_tab(self):
        """创建预设命令配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(self.texts['presets_config_label'])
        layout.addWidget(label)
        
        # 创建自定义的预设编辑区域，替代表格
        presets_container = QWidget()
        presets_container.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 1px solid #555;
            }
        """)
        presets_layout = QVBoxLayout(presets_container)
        presets_layout.setContentsMargins(10, 10, 10, 10)
        presets_layout.setSpacing(5)
        
        # 创建表头
        header_layout = QHBoxLayout()
        name_header = QLabel(self.texts['preset_name'])
        command_header = QLabel(self.texts['preset_command'])
        name_header.setStyleSheet("""
            QLabel {
                color: #f0f0f0;
                font-weight: bold;
                padding: 8px;
                background-color: #444;
                border-bottom: 1px solid #555;
            }
        """)
        command_header.setStyleSheet("""
            QLabel {
                color: #f0f0f0;
                font-weight: bold;
                padding: 8px;
                background-color: #444;
                border-bottom: 1px solid #555;
            }
        """)
        name_header.setFixedWidth(120)
        header_layout.addWidget(name_header)
        header_layout.addWidget(command_header)
        presets_layout.addLayout(header_layout)
        
        # 创建4行预设输入框
        self.preset_inputs = []
        for i in range(4):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(0)
            
            # 名称输入框
            name_input = QLineEdit()
            name_input.setFixedWidth(120)
            name_input.setStyleSheet("""
                QLineEdit {
                    color: #f0f0f0;
                    background-color: #2b2b2b;
                    border: 1px solid #555;
                    border-right: none;
                    padding: 8px;
                }
                QLineEdit:focus {
                    border: 2px solid #0078d4;
                    border-right: 1px solid #0078d4;
                }
            """)
            
            # 命令输入框
            command_input = QLineEdit()
            command_input.setStyleSheet("""
                QLineEdit {
                    color: #f0f0f0;
                    background-color: #2b2b2b;
                    border: 1px solid #555;
                    padding: 8px;
                }
                QLineEdit:focus {
                    border: 2px solid #0078d4;
                }
            """)
            
            row_layout.addWidget(name_input)
            row_layout.addWidget(command_input)
            presets_layout.addLayout(row_layout)
            
            # 保存输入框引用
            self.preset_inputs.append({
                'name': name_input,
                'command': command_input
            })
        
        # 加载现有预设到输入框
        self.load_presets_to_inputs()
        
        layout.addWidget(presets_container)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        self.reset_presets_button = QPushButton(self.texts['reset_presets'])
        
        self.reset_presets_button.clicked.connect(self.reset_presets)
        
        buttons_layout.addWidget(self.reset_presets_button)
        buttons_layout.addStretch(1)
        
        layout.addLayout(buttons_layout)
        
        return widget
    
    def load_presets_to_inputs(self):
        """加载预设命令到输入框（固定4行）"""
        presets = config.load_presets()
        
        # 填充前4条预设，不足的用空白填充
        for i in range(4):
            if i < len(presets):
                preset = presets[i]
                name = preset.get('name', '')
                command = preset.get('command', '')
            else:
                name = ''
                command = ''
            
            self.preset_inputs[i]['name'].setText(name)
            self.preset_inputs[i]['command'].setText(command)
    

    
    def reset_presets(self):
        """重置为默认预设命令"""
        msgbox = QMessageBox()
        msgbox.setIcon(QMessageBox.Icon.Question)
        msgbox.setWindowTitle(self.texts['confirm_reset'])
        msgbox.setText(self.texts['reset_message'])
        msgbox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msgbox.setDefaultButton(QMessageBox.StandardButton.No)
        self.set_messagebox_black_font_style(msgbox)
        reply = msgbox.exec()
        if reply == QMessageBox.StandardButton.Yes:
            # 使用配置文件中的默认预设（4条）
            default_presets = config.DEFAULT_PRESETS
            
            # 固定为4行，填充默认预设
            for i in range(4):
                if i < len(default_presets):
                    preset = default_presets[i]
                    self.preset_inputs[i]['name'].setText(preset['name'])
                    self.preset_inputs[i]['command'].setText(preset['command'])
                else:
                    self.preset_inputs[i]['name'].setText('')
                    self.preset_inputs[i]['command'].setText('')
    
    def get_settings(self):
        """获取设置数据"""
        settings = {}
        
        # 语言设置
        language_text = self.language_combo.currentText()
        settings['language'] = 'Chinese' if language_text == '中文' else 'English'
        
        # 预设命令设置（固定4行）
        presets = []
        for i in range(4):  # 固定读取4行
            name = self.preset_inputs[i]['name'].text().strip()
            command = self.preset_inputs[i]['command'].text().strip()
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
