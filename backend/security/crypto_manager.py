import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from utils.logger_config import get_logger

logger = get_logger('crypto')

_public_key_pem = None
_private_key_pem = None

KEYS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
PUBLIC_KEY_FILE = os.path.join(KEYS_DIR, 'public_key.pem')
PRIVATE_KEY_FILE = os.path.join(KEYS_DIR, 'private_key.pem')

def _load_keys_from_disk() -> bool:
    try:
        if os.path.exists(PUBLIC_KEY_FILE) and os.path.exists(PRIVATE_KEY_FILE):
            global _public_key_pem, _private_key_pem
            with open(PUBLIC_KEY_FILE, 'r') as f:
                _public_key_pem = f.read()
            with open(PRIVATE_KEY_FILE, 'r') as f:
                _private_key_pem = f.read()
            logger.info("Claves RSA cargadas desde disco")
            return True
    except Exception as e:
        logger.error(f"Error cargando claves: {e}")
    return False

def _save_keys_to_disk():
    try:
        os.makedirs(KEYS_DIR, exist_ok=True)
        with open(PUBLIC_KEY_FILE, 'w') as f:
            f.write(_public_key_pem)
        with open(PRIVATE_KEY_FILE, 'w') as f:
            f.write(_private_key_pem)
        logger.info("Claves RSA guardadas en disco")
    except Exception as e:
        logger.error(f"Error guardando claves: {e}")

def generate_rsa_keypair() -> tuple[str, str]:
    global _public_key_pem, _private_key_pem
    
    if _load_keys_from_disk():
        return _public_key_pem, _private_key_pem
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    public_key = private_key.public_key()
    
    _private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    _public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    _save_keys_to_disk()
    
    logger.info("Par de claves RSA-2048 generado")
    return _public_key_pem, _private_key_pem

def get_server_public_key() -> str:
    global _public_key_pem
    if _public_key_pem is None:
        generate_rsa_keypair()
    return _public_key_pem

def get_server_private_key() -> str:
    global _private_key_pem
    if _private_key_pem is None:
        generate_rsa_keypair()
    return _private_key_pem

def load_public_key_from_pem(pem_data: str):
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    return load_pem_public_key(pem_data.encode('utf-8'), default_backend())

def load_private_key_from_pem(pem_data: str):
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    return load_pem_private_key(pem_data.encode('utf-8'), password=None, backend=default_backend())

def initialize():
    generate_rsa_keypair()
