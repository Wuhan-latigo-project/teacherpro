# token_manager.py
"""مدير مركزي للتوكن وبيانات المستخدم - جميع الكودات الخارجية تستخدم هذا الملف"""
import os
import json
import time
import shutil
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import requests  # لإرسال طلبات HTTP إلى الخادم

# ==================== Encryption Utilities ====================
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SECRET = b"latigo_platform_secure_key_2024"
SALT = b"latigo_salt_2024"

def _get_cipher():
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(SECRET))
    return Fernet(key)

def encrypt_data(data):
    if data is None:
        return None
    try:
        cipher = _get_cipher()
        encrypted = cipher.encrypt(str(data).encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"⚠️ Encryption error: {e}")
        return data

def decrypt_data(encrypted_data):
    if encrypted_data is None:
        return None
    try:
        cipher = _get_cipher()
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted = cipher.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"⚠️ Decryption error: {e}")
        return encrypted_data

# ==================== File Path Helpers ====================
def get_account_dir():
    """Get the account directory path (creates if not exists)"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    account_dir = os.path.join(base_dir, "account")
    os.makedirs(account_dir, exist_ok=True)
    return account_dir

def get_token_data_path():
    """Path to token_data.json (primary storage)"""
    return os.path.join(get_account_dir(), "token_data.json")

def get_user_data_path():
    """Path to user_data.json (secondary storage for backward compatibility)"""
    return os.path.join(get_account_dir(), "user_data.json")

def get_token_txt_path():
    """Get the path to token.txt in the account folder (legacy)"""
    return os.path.join(get_account_dir(), "token.txt")

def save_token_txt(token):
    """Save token to account/token.txt with encryption"""
    if token is None:
        return False
    try:
        token_txt_path = get_token_txt_path()
        encrypted_token = encrypt_data(token)
        with open(token_txt_path, 'w', encoding='utf-8') as f:
            f.write(encrypted_token)
        print(f"✅ Token saved to account/token.txt (encrypted)")
        return True
    except Exception as e:
        print(f"❌ Failed to write token.txt: {e}")
        return False

def load_token_txt():
    """Load token from account/token.txt with decryption"""
    try:
        token_txt_path = get_token_txt_path()
        if not os.path.exists(token_txt_path):
            return None
        with open(token_txt_path, 'r', encoding='utf-8') as f:
            encrypted_token = f.read().strip()
        if not encrypted_token:
            return None
        decrypted_token = decrypt_data(encrypted_token)
        return decrypted_token
    except Exception as e:
        print(f"❌ Failed to read token.txt: {e}")
        return None

def remove_token_txt():
    """Remove account/token.txt file"""
    try:
        token_txt_path = get_token_txt_path()
        if os.path.exists(token_txt_path):
            os.remove(token_txt_path)
            print(f"✅ account/token.txt removed")
            return True
    except Exception as e:
        print(f"❌ Failed to remove token.txt: {e}")
    return False

def remove_old_token_txt():
    """Remove old token.txt from main directory (cleanup)"""
    try:
        old_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.txt")
        if os.path.exists(old_path):
            os.remove(old_path)
            print(f"✅ Old token.txt removed from main directory")
            return True
    except Exception as e:
        print(f"⚠️ Could not remove old token.txt: {e}")
    return False

def load_tokens_from_json():
    """Load token data from token_data.json (encrypted)"""
    try:
        path = get_token_data_path()
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            encrypted_data = json.load(f)
        # Decrypt fields
        token_data = {
            "user_id": decrypt_data(encrypted_data.get("user_id")),
            "access_token": decrypt_data(encrypted_data.get("access_token")),
            "refresh_token": decrypt_data(encrypted_data.get("refresh_token")),
            "expires_at": encrypted_data.get("expires_at"),  # numeric, not encrypted
            "saved_at": encrypted_data.get("saved_at"),      # numeric, not encrypted
            "user_data": json.loads(decrypt_data(encrypted_data.get("user_data"))) if encrypted_data.get("user_data") else None
        }
        return token_data
    except Exception as e:
        print(f"⚠️ Failed to load token_data.json: {e}")
        return None

def save_tokens_to_json(user_id, access_token, refresh_token, expires_in, user_data=None):
    """Save token data to token_data.json (encrypted)"""
    try:
        expires_at = time.time() + expires_in
        encrypted_data = {
            "user_id": encrypt_data(str(user_id)) if user_id else None,
            "access_token": encrypt_data(access_token) if access_token else None,
            "refresh_token": encrypt_data(refresh_token) if refresh_token else None,
            "expires_at": expires_at,
            "saved_at": time.time(),
            "user_data": encrypt_data(json.dumps(user_data)) if user_data else None
        }
        path = get_token_data_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(encrypted_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved tokens to {path}")
        return True
    except Exception as e:
        print(f"❌ Failed to save tokens: {e}")
        return False
# ==============================================================

class TokenManager:
    """
    مدير مركزي للتوكن وبيانات المستخدم - يعمل كـ Singleton
    جميع أجزاء النظام تحصل على التوكن وبيانات المستخدم من هنا
    """
    _instance = None
    _token: Optional[str] = None
    _user_data: Optional[Dict[str, Any]] = None
    _username: Optional[str] = None
    _user_id: Optional[str] = None
    _current_room: Optional[str] = None
    _available_rooms: List[str] = []
    _token_file: Optional[str] = None
    _user_data_file: Optional[str] = None
    _account_dir: Optional[str] = None
    _token_expiry: Optional[datetime] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # تحديد مسارات الملفات
            cls._account_dir = get_account_dir()
            cls._token_file = get_token_data_path()
            cls._user_data_file = get_user_data_path()
            # Remove old token.txt from main directory on startup
            remove_old_token_txt()
            cls._load_from_files()
            cls._ensure_valid_state()  # ← FIXED: Use renamed method
        return cls._instance
    
    @classmethod
    def _load_from_files(cls):
        """تحميل التوكن وبيانات المستخدم من الملفات مع فك التشفير"""
        print("\n📄 TokenManager: Loading data from files...")
        
        # Try loading from token_data.json (primary)
        token_data = load_tokens_from_json()
        if token_data:
            cls._user_id = token_data.get("user_id")
            cls._token = token_data.get("access_token")
            cls._user_data = token_data.get("user_data")
            
            # Expiry
            expires_at = token_data.get("expires_at")
            if expires_at:
                cls._token_expiry = datetime.fromtimestamp(expires_at)
            
            # Extract username from user_data
            if cls._user_data:
                cls._username = (
                    cls._user_data.get('username') or
                    cls._user_data.get('display_name') or
                    cls._user_data.get('first_name') or
                    None
                )
                # Extract rooms
                if 'joined_rooms' in cls._user_data:
                    joined = cls._user_data.get('joined_rooms', [])
                    if joined and isinstance(joined, list):
                        cls._available_rooms = joined
                        cls._current_room = joined[0] if joined else None
            
            print(f"📄 TokenManager: Loaded token from {cls._token_file}")
            if cls._username:
                print(f"   - Username: {cls._username}")
            print(f"   - Current room: {cls._current_room}")
            print(f"   - Available rooms: {cls._available_rooms}")
            return
        
        # Fallback: try loading from user_data.json (secondary)
        try:
            if cls._user_data_file and os.path.exists(cls._user_data_file):
                with open(cls._user_data_file, 'r', encoding='utf-8') as f:
                    encrypted_data = json.load(f)
                    cls._user_data = json.loads(decrypt_data(encrypted_data.get('user_data'))) if encrypted_data.get('user_data') else None
                    cls._username = decrypt_data(encrypted_data.get('username'))
                    cls._user_id = decrypt_data(encrypted_data.get('user_id'))
                    cls._current_room = decrypt_data(encrypted_data.get('current_room'))
                    rooms = decrypt_data(encrypted_data.get('available_rooms'))
                    cls._available_rooms = json.loads(rooms) if rooms else []
                    expiry_str = decrypt_data(encrypted_data.get('token_expiry'))
                    if expiry_str:
                        try:
                            cls._token_expiry = datetime.fromisoformat(expiry_str)
                        except:
                            cls._token_expiry = None
                    print(f"📄 TokenManager: Loaded user data from {cls._user_data_file}")
                    if cls._username:
                        print(f"   - Username: {cls._username}")
                    print(f"   - Current room: {cls._current_room}")
                    print(f"   - Available rooms: {cls._available_rooms}")
        except Exception as e:
            print(f"⚠️ TokenManager: Could not load user_data: {e}")
        
        # Fallback: try loading from token.txt (legacy)
        cls._token = load_token_txt()
        if cls._token:
            print(f"📄 TokenManager: Loaded token from token.txt (legacy)")
    
    @classmethod
    def _ensure_valid_state(cls):
        """Ensure the token manager has valid state (no default room)"""
        # Only set defaults if both token and user data exist
        if cls._token and cls._user_data:
            # If we have token but no rooms, try to get from user_data
            if not cls._available_rooms and cls._user_data:
                if 'joined_rooms' in cls._user_data:
                    joined = cls._user_data.get('joined_rooms', [])
                    if joined and isinstance(joined, list):
                        cls._available_rooms = joined
                        cls._current_room = joined[0] if joined else None
                        cls._save_to_files()
            # If still no rooms, leave as None (no default)
        else:
            # No token or no user data - clear everything
            if not cls._token:
                cls._user_data = None
                cls._username = None
                cls._user_id = None
                cls._current_room = None
                cls._available_rooms = []
                cls._token_expiry = None
        
        # Print status
        print(f"\n📊 TokenManager Status:")
        print(f"   Token: {'✅ Present' if cls._token else '❌ Missing'}")
        print(f"   Username: {cls._username or '❌ Missing'}")
        print(f"   User ID: {cls._user_id or '❌ Missing'}")
        print(f"   Current room: {cls._current_room or '❌ None'}")
        print(f"   Available rooms: {cls._available_rooms or '[]'}")
        print(f"   Authenticated: {cls.is_authenticated()}")
        print(f"   Room selected: {cls.is_room_selected()}")
        print()
    
    @classmethod
    def _save_to_files(cls):
        """حفظ التوكن وبيانات المستخدم في الملفات مع تشفير البيانات الحساسة"""
        try:
            # إنشاء مجلد account إذا لم يكن موجوداً
            if cls._account_dir:
                os.makedirs(cls._account_dir, exist_ok=True)
            
            # Save to token_data.json (primary)
            if cls._token:
                if cls._token_expiry:
                    expires_in = int((cls._token_expiry - datetime.now()).total_seconds())
                    if expires_in < 0:
                        expires_in = 86400
                else:
                    expires_in = 86400
                
                save_tokens_to_json(
                    user_id=cls._user_id,
                    access_token=cls._token,
                    refresh_token=None,
                    expires_in=expires_in,
                    user_data=cls._user_data
                )
            
            # Save to user_data.json (secondary)
            if cls._user_data_file:
                encrypted_data = {
                    'user_data': encrypt_data(json.dumps(cls._user_data)) if cls._user_data else None,
                    'username': encrypt_data(cls._username) if cls._username else None,
                    'user_id': encrypt_data(cls._user_id) if cls._user_id else None,
                    'current_room': encrypt_data(cls._current_room) if cls._current_room else None,
                    'available_rooms': encrypt_data(json.dumps(cls._available_rooms)) if cls._available_rooms else None,
                    'token_expiry': encrypt_data(cls._token_expiry.isoformat()) if cls._token_expiry else None,
                    'saved_at': datetime.now().isoformat()
                }
                with open(cls._user_data_file, 'w', encoding='utf-8') as f:
                    json.dump(encrypted_data, f, ensure_ascii=False, indent=2)
                print(f"✅ TokenManager: Saved user data to {cls._user_data_file}")
                
        except Exception as e:
            print(f"⚠️ TokenManager: Could not save data: {e}")
    
    @classmethod
    def _delete_old_files(cls, keep_backup: bool = False):
        """حذف الملفات القديمة (يستخدم عند تغيير التوكن)"""
        try:
            backup_dir = None
            if keep_backup and cls._account_dir:
                backup_dir = os.path.join(cls._account_dir, "backups")
                os.makedirs(backup_dir, exist_ok=True)
            
            for file_path in [get_token_data_path(), get_user_data_path(), get_token_txt_path()]:
                if file_path and os.path.exists(file_path):
                    if keep_backup and backup_dir:
                        backup_name = f"backup_{os.path.basename(file_path)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        backup_path = os.path.join(backup_dir, backup_name)
                        shutil.copy2(file_path, backup_path)
                        print(f"✅ TokenManager: Created backup at {backup_path}")
                    
                    os.remove(file_path)
                    print(f"✅ TokenManager: Deleted old file {file_path}")
            # Also remove old token.txt from main directory
            remove_old_token_txt()
        except Exception as e:
            print(f"⚠️ TokenManager: Error deleting old files: {e}")
    
    # ==================== Public API ====================
    
    @classmethod
    def set_token(cls, token: str, user_data: Dict[str, Any] = None, username: str = None):
        """
        تعيين التوكن وبيانات المستخدم
        
        Args:
            token: التوكن الخاص بالمستخدم
            user_data: بيانات المستخدم كاملة (اختياري)
            username: اسم المستخدم (اختياري - يستخرج من user_data إذا لم يُمرر)
        """
        old_token = cls._token
        if old_token and old_token != token:
            print(f"🔄 TokenManager: Token changed from {old_token[:10]}... to {token[:10]}...")
            cls._delete_old_files(keep_backup=True)
        
        cls._token = token
        cls._user_data = user_data
        
        if username:
            cls._username = username
        elif user_data:
            cls._username = (
                user_data.get('username') or 
                user_data.get('display_name') or 
                user_data.get('first_name') or
                user_data.get('email', '').split('@')[0] or
                None
            )
        
        if user_data:
            cls._user_id = user_data.get('id')
        
        # Extract rooms from user_data
        if user_data and 'joined_rooms' in user_data:
            joined_rooms = user_data.get('joined_rooms', [])
            if joined_rooms and isinstance(joined_rooms, list):
                cls._available_rooms = joined_rooms
                cls._current_room = joined_rooms[0] if joined_rooms else None
                print(f"✅ TokenManager: Set rooms from user_data: {joined_rooms}")
            else:
                cls._available_rooms = []
                cls._current_room = None
                print("⚠️ TokenManager: No rooms found in user_data")
        else:
            cls._available_rooms = []
            cls._current_room = None
            print("⚠️ TokenManager: No user_data or no joined_rooms")
        
        cls._token_expiry = datetime.now() + timedelta(hours=24)
        cls._save_to_files()
        print(f"✅ TokenManager: Token set successfully for user {cls._username}")
        print(f"✅ TokenManager: Current room: {cls._current_room}")
        print(f"✅ TokenManager: Available rooms: {cls._available_rooms}")
    
    @classmethod
    def get_token(cls) -> Optional[str]:
        """الحصول على التوكن"""
        if cls._token_expiry and datetime.now() > cls._token_expiry:
            print("⚠️ TokenManager: Token expired")
            return None
        return cls._token
    
    @classmethod
    def get_user_data(cls) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات المستخدم كاملة"""
        return cls._user_data
    
    @classmethod
    def get_user_id(cls) -> Optional[str]:
        """الحصول على معرف المستخدم"""
        return cls._user_id
    
    @classmethod
    def get_username(cls) -> Optional[str]:
        """الحصول على اسم المستخدم"""
        return cls._username
    
    @classmethod
    def get_current_room(cls) -> Optional[str]:
        """
        الحصول على الغرفة الحالية
        
        Returns:
            اسم الغرفة الحالية أو None إذا لم يتم اختيار معلم بعد
        """
        return cls._current_room
    
    @classmethod
    def set_current_room(cls, room: Optional[str]):
        """
        تعيين الغرفة الحالية
        
        Args:
            room: اسم الغرفة الجديدة أو None
        """
        if room is None:
            cls._current_room = None
            cls._save_to_files()
            print(f"✅ TokenManager: Current room cleared")
        elif room in cls._available_rooms:
            cls._current_room = room
            cls._save_to_files()
            print(f"✅ TokenManager: Current room set to {room}")
        else:
            print(f"⚠️ TokenManager: Room {room} not in available rooms")
            cls.add_room(room)
            cls._current_room = room
    
    @classmethod
    def get_available_rooms(cls) -> List[str]:
        """الحصول على قائمة الغرف المتاحة"""
        return cls._available_rooms if cls._available_rooms else []
    
    @classmethod
    def set_available_rooms(cls, rooms: List[str]):
        """تعيين قائمة الغرف المتاحة"""
        cls._available_rooms = rooms
        if cls._current_room and cls._current_room not in rooms:
            cls._current_room = rooms[0] if rooms else None
        cls._save_to_files()
        print(f"✅ TokenManager: Available rooms set to {rooms}")
    
    @classmethod
    def add_room(cls, room: str):
        """إضافة غرفة جديدة للقائمة"""
        if room not in cls._available_rooms:
            cls._available_rooms.append(room)
            cls._save_to_files()
            print(f"✅ TokenManager: Room {room} added")
    
    @classmethod
    def remove_room(cls, room: str):
        """إزالة غرفة من القائمة"""
        if room in cls._available_rooms:
            cls._available_rooms.remove(room)
            if cls._current_room == room:
                cls._current_room = cls._available_rooms[0] if cls._available_rooms else None
            cls._save_to_files()
            print(f"✅ TokenManager: Room {room} removed")
    
    @classmethod
    def is_room_selected(cls) -> bool:
        """
        التحقق مما إذا كان المستخدم قد اختار معلم/غرفة
        
        Returns:
            True إذا كان هناك غرفة حالية صالحة، False خلاف ذلك
        """
        return cls._current_room is not None and cls._current_room in cls._available_rooms
    
    @classmethod
    def get_auth_headers(cls) -> Dict[str, str]:
        """الحصول على headers المصادقة للـ API requests"""
        token = cls.get_token()
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        if cls.get_user_id():
            headers['X-User-ID'] = cls.get_user_id()
        if cls.get_username():
            headers['X-Username'] = cls.get_username()
        if cls.get_current_room():
            headers['X-Room'] = cls.get_current_room()
        return headers
    
    @classmethod
    def clear(cls):
        """مسح جميع البيانات - عند تسجيل الخروج"""
        cls._token = None
        cls._user_data = None
        cls._username = None
        cls._user_id = None
        cls._current_room = None
        cls._available_rooms = []
        cls._token_expiry = None
        # Delete all files
        for path in [get_token_data_path(), get_user_data_path(), get_token_txt_path()]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"✅ TokenManager: Deleted {path}")
                except Exception as e:
                    print(f"⚠️ Could not delete {path}: {e}")
        remove_old_token_txt()
        print("✅ TokenManager: All data cleared")
    
    @classmethod
    def is_authenticated(cls) -> bool:
        """التحقق من وجود توكن صالح"""
        token = cls.get_token()
        return token is not None and (cls._token_expiry is None or datetime.now() <= cls._token_expiry)
    
    @classmethod
    def get_token_info(cls) -> Dict[str, Any]:
        """الحصول على معلومات التوكن"""
        return {
            'has_token': cls._token is not None,
            'username': cls._username,
            'user_id': cls._user_id,
            'current_room': cls._current_room,
            'available_rooms': cls._available_rooms,
            'token_expiry': cls._token_expiry.isoformat() if cls._token_expiry else None,
            'is_valid': cls.is_authenticated(),
            'has_room_selected': cls.is_room_selected()
        }
    
    @classmethod
    def refresh_token(cls, new_token: str, new_expiry: datetime = None):
        """تحديث التوكن"""
        old_token = cls._token
        if old_token and old_token != new_token:
            cls._delete_old_files(keep_backup=True)
        
        cls._token = new_token
        if new_expiry:
            cls._token_expiry = new_expiry
        else:
            cls._token_expiry = datetime.now() + timedelta(hours=24)
        cls._save_to_files()
        print("✅ TokenManager: Token refreshed")
    
    @classmethod
    def update_user_data(cls, user_data: Dict[str, Any]):
        """تحديث بيانات المستخدم"""
        cls._user_data = user_data
        if user_data:
            new_username = (
                user_data.get('username') or 
                user_data.get('display_name') or 
                user_data.get('first_name')
            )
            if new_username:
                cls._username = new_username
            
            if 'id' in user_data:
                cls._user_id = user_data.get('id')
            
            if 'joined_rooms' in user_data:
                joined_rooms = user_data.get('joined_rooms', [])
                if joined_rooms and isinstance(joined_rooms, list):
                    cls._available_rooms = joined_rooms
                    if cls._current_room and cls._current_room not in joined_rooms:
                        cls._current_room = joined_rooms[0] if joined_rooms else None
                    print(f"✅ TokenManager: Updated rooms from user_data: {joined_rooms}")
                else:
                    cls._available_rooms = []
                    cls._current_room = None
                    print("⚠️ TokenManager: No rooms in user_data")
        
        cls._save_to_files()
        print("✅ TokenManager: User data updated")
    
    @classmethod
    def get_user_setting(cls, key: str, default=None):
        """الحصول على إعداد محدد للمستخدم"""
        if cls._user_data:
            return cls._user_data.get(key, default)
        return default
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """تحويل جميع البيانات إلى قاموس"""
        return {
            'token': cls._token,
            'username': cls._username,
            'user_id': cls._user_id,
            'current_room': cls._current_room,
            'available_rooms': cls._available_rooms,
            'token_expiry': cls._token_expiry.isoformat() if cls._token_expiry else None,
            'is_authenticated': cls.is_authenticated(),
            'has_room_selected': cls.is_room_selected(),
            'user_data': cls._user_data
        }
    
    # ==================== Server Sync Methods ====================
    
    @classmethod
    def sync_rooms_from_server(cls, api_base_url: str = "https://localhost:8443") -> bool:
        """
        مزامنة الغرف المتاحة من الخادم
        
        Args:
            api_base_url: عنوان الخادم الأساسي
            
        Returns:
            True إذا نجحت المزامنة، False خلاف ذلك
        """
        if not cls._token:
            print("⚠️ TokenManager: Cannot sync rooms - no token")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {cls._token}"}
            response = requests.get(
                f"{api_base_url}/api/student/rooms",
                headers=headers,
                timeout=5,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    rooms = data.get("data", {}).get("rooms", [])
                    if rooms and isinstance(rooms, list):
                        cls._available_rooms = rooms
                        if cls._current_room and cls._current_room not in rooms:
                            cls._current_room = rooms[0] if rooms else None
                        cls._save_to_files()
                        print(f"✅ TokenManager: Synced rooms from server: {rooms}")
                        return True
                    else:
                        cls._available_rooms = []
                        cls._current_room = None
                        cls._save_to_files()
                        print("⚠️ TokenManager: No rooms from server")
                        return True
            return False
        except Exception as e:
            print(f"⚠️ TokenManager: Error syncing rooms: {e}")
            return False
    
    @classmethod
    def sync_with_server(cls, api_base_url: str = "https://localhost:8443") -> bool:
        """مزامنة التوكن مع الخادم"""
        if not cls._token or not cls._user_id:
            print("⚠️ TokenManager: Cannot sync - no token or user ID")
            return False
        
        try:
            response = requests.post(
                f"{api_base_url}/api/token/update",
                json={"user_id": cls._user_id, "token": cls._token},
                timeout=5,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ TokenManager: Successfully synced token with server")
                    if data.get("data") and data["data"].get("expires_at"):
                        try:
                            expires_str = data["data"]["expires_at"]
                            if '+' in expires_str:
                                expires_str = expires_str.split('+')[0]
                            cls._token_expiry = datetime.fromisoformat(expires_str)
                        except Exception as e:
                            print(f"⚠️ TokenManager: Could not parse expiry: {e}")
                    
                    # After syncing token, also sync rooms
                    cls.sync_rooms_from_server(api_base_url)
                    return True
            return False
        except Exception as e:
            print(f"⚠️ TokenManager: Error syncing: {e}")
            return False
    
    @classmethod
    def sync_if_needed(cls, api_base_url: str = "https://localhost:8443") -> bool:
        """التحقق والمزامنة إذا لزم الأمر"""
        if not cls._token or not cls._user_id:
            return False
        
        try:
            headers = {"Authorization": f"Bearer {cls._token}"}
            response = requests.get(f"{api_base_url}/api/token/validate", headers=headers, timeout=3, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ TokenManager: Token is valid on server")
                    # Still sync rooms to get latest
                    cls.sync_rooms_from_server(api_base_url)
                    return True
            print("⚠️ TokenManager: Token invalid on server, syncing...")
            return cls.sync_with_server(api_base_url)
        except Exception as e:
            print(f"⚠️ TokenManager: Error checking token: {e}")
            return cls.sync_with_server(api_base_url)


# إنشاء instance وحيد
token_manager = TokenManager()

# ==============================
# دوال مساعدة للاستخدام السريع
# ==============================

def get_token() -> Optional[str]:
    return token_manager.get_token()

def get_username() -> Optional[str]:
    return token_manager.get_username()

def get_user_id() -> Optional[str]:
    return token_manager.get_user_id()

def get_current_room() -> Optional[str]:
    return token_manager.get_current_room()

def get_auth_headers() -> Dict[str, str]:
    return token_manager.get_auth_headers()

def is_authenticated() -> bool:
    return token_manager.is_authenticated()

def is_room_selected() -> bool:
    """التحقق مما إذا كان المستخدم قد اختار معلم/غرفة"""
    return token_manager.is_room_selected()

def set_token(token: str, user_data: Dict[str, Any] = None, username: str = None):
    return token_manager.set_token(token, user_data, username)

def clear_token():
    return token_manager.clear()

def update_user_data(user_data: Dict[str, Any]):
    return token_manager.update_user_data(user_data)

def set_current_room(room: Optional[str]):
    return token_manager.set_current_room(room)

def get_available_rooms() -> List[str]:
    return token_manager.get_available_rooms()

def get_user_data() -> Optional[Dict[str, Any]]:
    return token_manager.get_user_data()

def get_token_info() -> Dict[str, Any]:
    return token_manager.get_token_info()

def add_room(room: str):
    """إضافة غرفة جديدة"""
    return token_manager.add_room(room)

def remove_room(room: str):
    """إزالة غرفة"""
    return token_manager.remove_room(room)

def sync_rooms_from_server(api_base_url: str = "https://localhost:8443") -> bool:
    """مزامنة الغرف من الخادم"""
    return token_manager.sync_rooms_from_server(api_base_url)

def sync_token_with_server(api_base_url: str = "https://localhost:8443") -> bool:
    return token_manager.sync_with_server(api_base_url)

def sync_if_needed(api_base_url: str = "https://localhost:8443") -> bool:
    return token_manager.sync_if_needed(api_base_url)


if __name__ == "__main__":
    print("🔧 Token Manager Test")
    print("=" * 50)
    print(f"Is authenticated: {is_authenticated()}")
    print(f"Current room: {get_current_room()}")
    print(f"Available rooms: {get_available_rooms()}")
    print(f"Is room selected: {is_room_selected()}")
    print("=" * 50)
    
    # Test with no room
    print("\n📝 Testing with no room...")
    token_manager.clear()
    print(f"Current room after clear: {get_current_room()}")
    print(f"Available rooms after clear: {get_available_rooms()}")
    print(f"Is room selected: {is_room_selected()}")
    
    # Test with joined_rooms
    print("\n📝 Testing with joined_rooms...")
    test_user_data = {
        'id': '12345',
        'username': 'test_user',
        'display_name': 'Test User',
        'email': 'test@example.com',
        'joined_rooms': ['room1', 'room2', 'room3']
    }
    token_manager.set_token('test_token_12345', test_user_data, 'test_user')
    print(f"Current room: {get_current_room()}")
    print(f"Available rooms: {get_available_rooms()}")
    print(f"Is room selected: {is_room_selected()}")
    
    # Test without joined_rooms
    print("\n📝 Testing without joined_rooms...")
    test_user_data2 = {
        'id': '12345',
        'username': 'test_user2'
    }
    token_manager.set_token('test_token_67890', test_user_data2, 'test_user2')
    print(f"Current room: {get_current_room()}")
    print(f"Available rooms: {get_available_rooms()}")
    print(f"Is room selected: {is_room_selected()}")
    print("=" * 50)