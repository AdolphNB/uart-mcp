import json
import os

CONFIG_FILE = 'config.json'
PRESETS_FILE = 'presets.json'

DEFAULT_CONFIG = {
    "mcp_host": "127.0.0.1",
    "mcp_port": 8000,
    "last_serial_port": "",
    "last_baud_rate": 115200
}

DEFAULT_PRESETS = [
    {"name": "Reboot", "command": "dbg reboot"},
    {"name": "LED On", "command": "dbg led on"},
    {"name": "AT", "command": "AT"},
    {"name": "Version", "command": "AT+GMR"}
]

def load_config():
    """加载主配置文件，如果文件不存在则创建。"""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Ensure all default keys exist
            for key, value in DEFAULT_CONFIG.items():
                config.setdefault(key, value)
            return config
    except (json.JSONDecodeError, IOError):
        # In case of corruption, load defaults
        return DEFAULT_CONFIG

def save_config(config_data):
    """保存主配置文件。"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
    except IOError as e:
        print(f"Error saving config file: {e}")

def load_presets():
    """加载预设命令文件，如果文件不存在则创建。"""
    if not os.path.exists(PRESETS_FILE):
        save_presets(DEFAULT_PRESETS)
        return DEFAULT_PRESETS

    try:
        with open(PRESETS_FILE, 'r') as f:
            presets = json.load(f)
            return presets
    except (json.JSONDecodeError, IOError):
        return DEFAULT_PRESETS

def save_presets(presets_data):
    """保存预设命令文件。"""
    try:
        with open(PRESETS_FILE, 'w') as f:
            json.dump(presets_data, f, indent=4)
    except IOError as e:
        print(f"Error saving presets file: {e}")

if __name__ == '__main__':
    # Initialize config files if they don't exist
    print("Loading initial config...")
    config = load_config()
    print(f"Loaded config: {config}")

    print("\nLoading initial presets...")
    presets = load_presets()
    print(f"Loaded presets: {presets}") 