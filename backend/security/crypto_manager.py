import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from utils.logger_config import get_logger

logger = get_logger('crypto')

_public_key_pem = None
_private_key_pem = None

def generate_rsa_keypair() -> tuple[str, str]:
    global _public_key_pem, _private_key_pem
    
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
