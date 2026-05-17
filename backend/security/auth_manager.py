import json
import os
import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from utils.logger_config import get_logger

logger = get_logger('auth')

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
TOKEN_BLACKLIST = set()

SECRET_KEY = secrets.token_hex(32)
TOKEN_EXPIRY_HOURS = 24

def _load_users() -> Dict[str, str]:
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        return {}

def _save_users(users: Dict[str, str]) -> bool:
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving users: {e}")
        return False

def sanitize_input(text: str) -> str:
    return text.strip()[:50]

def validate_username(username: str) -> tuple[bool, str]:
    username = sanitize_input(username)
    if not username:
        return False, "El usuario no puede estar vacío"
    if len(username) < 3:
        return False, "El usuario debe tener al menos 3 caracteres"
    if len(username) > 20:
        return False, "El usuario no puede tener más de 20 caracteres"
    if not username.isalnum():
        return False, "Solo se permiten letras y números"
    return True, username

def validate_password(password: str) -> tuple[bool, str]:
    if not password:
        return False, "La contraseña no puede estar vacía"
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres"
    return True, password

def register_user(username: str, password: str) -> tuple[bool, str]:
    valid, result = validate_username(username)
    if not valid:
        logger.warning(f"Registro fallido - username inválido: {username}")
        return False, result
    
    valid, result = validate_password(password)
    if not valid:
        logger.warning(f"Registro fallido - password inválido para usuario: {username}")
        return False, result
    
    users = _load_users()
    
    if username in users:
        logger.warning(f"Registro fallido - usuario ya existe: {username}")
        return False, "El usuario ya existe"
    
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    users[username] = password_hash
    
    if _save_users(users):
        logger.info(f"Usuario registrado exitosamente: {username}")
        return True, "Usuario registrado exitosamente"
    
    logger.error(f"Error al registrar usuario: {username}")
    return False, "Error al registrar usuario"

def login_user(username: str, password: str) -> tuple[bool, str, Optional[str]]:
    valid, result = validate_username(username)
    if not valid:
        logger.warning(f"Login fallido - username inválido: {username}")
        return False, "Usuario o contraseña incorrectos", None
    
    users = _load_users()
    
    if username not in users:
        logger.warning(f"Login fallido - usuario no existe: {username}")
        return False, "Usuario o contraseña incorrectos", None
    
    stored_hash = users[username].encode('utf-8')
    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
        logger.warning(f"Login fallido - password incorrecto para usuario: {username}")
        return False, "Usuario o contraseña incorrectos", None
    
    token = generate_token(username)
    logger.info(f"Login exitoso: {username}")
    return True, "Login exitoso", token

def generate_token(username: str) -> str:
    payload = {
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token: str) -> tuple[bool, Optional[str]]:
    if token in TOKEN_BLACKLIST:
        return False, None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return True, payload.get('username')
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        return False, None
    except jwt.InvalidTokenError:
        logger.warning("Token inválido")
        return False, None

def logout_user(token: str) -> bool:
    if verify_token(token)[0]:
        TOKEN_BLACKLIST.add(token)
        logger.info("Logout exitoso")
        return True
    return False

def change_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    users = _load_users()
    
    if username not in users:
        return False, "Usuario no encontrado"
    
    stored_hash = users[username].encode('utf-8')
    if not bcrypt.checkpw(old_password.encode('utf-8'), stored_hash):
        logger.warning(f"Cambio de password fallido - password incorrecto: {username}")
        return False, "Contraseña actual incorrecta"
    
    valid, result = validate_password(new_password)
    if not valid:
        return False, result
    
    new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    users[username] = new_hash
    
    if _save_users(users):
        logger.info(f"Password cambiado exitosamente: {username}")
        return True, "Contraseña actualizada"
    
    return False, "Error al cambiar contraseña"

def get_public_key() -> str:
    from security.crypto_manager import get_server_public_key
    return get_server_public_key()
