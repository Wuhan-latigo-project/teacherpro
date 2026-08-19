# config.py
"""
Central configuration for the entire application
All modules should import server addresses from here
"""

import os
import sys

# ============================================
# SERVER CONFIGURATION - LOCALHOST / DNS
# ============================================

# Primary server address - using localhost (or you can change to a custom DNS like "myapp.local")
SERVER_IP = "localhost"   # or "127.0.0.1"

# Alternative/backup server IP (optional, also set to localhost for consistency)
BACKUP_SERVER_IP = "localhost"

# Ports
API_PORT = 8443
STREAM_PORT = 8766
WEBSOCKET_PORT = 8765
WEBSOCKET_SECURE_PORT = 5023
QUIZ_WEBSOCKET_PORT = 5002

# ============================================
# DERIVED URLs (auto-generated from above)
# ============================================

# API URLs
API_BASE_URL = f"https://{SERVER_IP}:{API_PORT}"
API_BASE_URL_BACKUP = f"https://{BACKUP_SERVER_IP}:{API_PORT}"

# Stream URLs
STREAM_BASE_URL = f"https://{SERVER_IP}:{STREAM_PORT}"

# WebSocket URLs
WEBSOCKET_URL = f"ws://{SERVER_IP}:{WEBSOCKET_PORT}"
WEBSOCKET_SECURE_URL = f"wss://{SERVER_IP}:{WEBSOCKET_SECURE_PORT}"
QUIZ_WEBSOCKET_URL = f"wss://{SERVER_IP}:{QUIZ_WEBSOCKET_PORT}"
UPLOAD_WEBSOCKET_URL = f"wss://{SERVER_IP}:{WEBSOCKET_PORT}"

# ============================================
# APPLICATION PATHS
# ============================================

def get_base_dir():
    """Get the base directory of the application"""
    return os.path.dirname(os.path.abspath(__file__))

def get_account_dir():
    """Get the account directory path"""
    return os.path.join(get_base_dir(), "account")

def get_icons_dir():
    """Get the icons directory path"""
    return os.path.join(get_base_dir(), "icons")

def get_teacherselector_dir():
    """Get the teacherselector directory path"""
    return os.path.join(get_base_dir(), "teacherselector")

def get_classroom_dir():
    """Get the classroom directory path"""
    return os.path.join(get_base_dir(), "classroom")

def get_quiz_dir():
    """Get the quiz directory path"""
    return os.path.join(get_base_dir(), "quiz")

def get_aisender_dir():
    """Get the aisender directory path"""
    return os.path.join(get_base_dir(), "aisender")

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_server_ip():
    """Get server IP from environment variable or use default"""
    return os.environ.get('LATIGO_SERVER_IP', SERVER_IP)

def update_server_ip(new_ip):
    """Update all URLs with new IP address"""
    global SERVER_IP, API_BASE_URL, API_BASE_URL_BACKUP
    global STREAM_BASE_URL, WEBSOCKET_URL, WEBSOCKET_SECURE_URL
    global QUIZ_WEBSOCKET_URL, UPLOAD_WEBSOCKET_URL
    
    SERVER_IP = new_ip
    API_BASE_URL = f"https://{SERVER_IP}:{API_PORT}"
    API_BASE_URL_BACKUP = f"https://{BACKUP_SERVER_IP}:{API_PORT}"
    STREAM_BASE_URL = f"https://{SERVER_IP}:{STREAM_PORT}"
    WEBSOCKET_URL = f"ws://{SERVER_IP}:{WEBSOCKET_PORT}"
    WEBSOCKET_SECURE_URL = f"wss://{SERVER_IP}:{WEBSOCKET_SECURE_PORT}"
    QUIZ_WEBSOCKET_URL = f"wss://{SERVER_IP}:{QUIZ_WEBSOCKET_PORT}"
    UPLOAD_WEBSOCKET_URL = f"wss://{SERVER_IP}:{WEBSOCKET_PORT}"

def get_config_info():
    """Return current configuration as a dictionary"""
    return {
        'server_ip': SERVER_IP,
        'backup_server_ip': BACKUP_SERVER_IP,
        'api_base_url': API_BASE_URL,
        'api_base_url_backup': API_BASE_URL_BACKUP,
        'stream_base_url': STREAM_BASE_URL,
        'websocket_url': WEBSOCKET_URL,
        'websocket_secure_url': WEBSOCKET_SECURE_URL,
        'quiz_websocket_url': QUIZ_WEBSOCKET_URL,
        'upload_websocket_url': UPLOAD_WEBSOCKET_URL,
        'api_port': API_PORT,
        'stream_port': STREAM_PORT,
        'websocket_port': WEBSOCKET_PORT,
        'websocket_secure_port': WEBSOCKET_SECURE_PORT,
        'quiz_websocket_port': QUIZ_WEBSOCKET_PORT
    }

def print_config():
    """Print current configuration for debugging"""
    print("\n" + "="*50)
    print("CURRENT CONFIGURATION")
    print("="*50)
    info = get_config_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    print("="*50 + "\n")

# ============================================
# COMMAND LINE ARGUMENT HANDLING
# ============================================

def load_config_from_args():
    """Load server IP from command line arguments if provided"""
    if len(sys.argv) > 1:
        new_ip = sys.argv[1]
        # Validate IP format (basic check) - also accept hostnames like localhost
        parts = new_ip.split('.')
        if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            update_server_ip(new_ip)
            print(f"[Config] Server IP updated from command line: {new_ip}")
            return True
        else:
            # Allow non-IP values (like localhost, mypc, etc.) as valid hostnames
            update_server_ip(new_ip)
            print(f"[Config] Server address updated from command line: {new_ip}")
            return True
    return False

# ============================================
# AUTO-LOAD FROM COMMAND LINE
# ============================================

# Automatically check for command line argument when imported
_loaded = load_config_from_args()

# Print initialization message (no emojis)
print(f"[Config] Initialized: API={API_BASE_URL}, Stream={STREAM_BASE_URL}")

# ============================================
# EXPORTS (what gets imported with "from config import *")
# ============================================

__all__ = [
    'SERVER_IP',
    'BACKUP_SERVER_IP',
    'API_PORT',
    'STREAM_PORT',
    'WEBSOCKET_PORT',
    'WEBSOCKET_SECURE_PORT',
    'QUIZ_WEBSOCKET_PORT',
    'API_BASE_URL',
    'API_BASE_URL_BACKUP',
    'STREAM_BASE_URL',
    'WEBSOCKET_URL',
    'WEBSOCKET_SECURE_URL',
    'QUIZ_WEBSOCKET_URL',
    'UPLOAD_WEBSOCKET_URL',
    'get_base_dir',
    'get_account_dir',
    'get_icons_dir',
    'get_teacherselector_dir',
    'get_classroom_dir',
    'get_quiz_dir',
    'get_aisender_dir',
    'get_server_ip',
    'update_server_ip',
    'get_config_info',
    'print_config',
    'load_config_from_args'
]