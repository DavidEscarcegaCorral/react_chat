import os
import base64
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
from security.crypto_manager import load_public_key_from_pem, load_private_key_from_pem, get_server_public_key
from utils.logger_config import get_logger

logger = get_logger('encryption')

def generate_aes_key() -> bytes:
    return os.urandom(16)

def generate_aes_iv() -> bytes:
    return os.urandom(16)

def aes_encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    
    return encryptor.update(padded_data) + encryptor.finalize()

def aes_decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded_plaintext) + unpadder.finalize()

def rsa_encrypt(data: bytes, public_key_pem: str) -> bytes:
    public_key = load_public_key_from_pem(public_key_pem)
    return public_key.encrypt(
        data,
        rsa_padding.OAEP(
            mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256()
        )
    )

def rsa_decrypt(encrypted_data: bytes, private_key_pem: str) -> bytes:
    private_key = load_private_key_from_pem(private_key_pem)
    return private_key.decrypt(
        encrypted_data,
        rsa_padding.OAEP(
            mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256()
        )
    )

def encrypt_message(message: str, public_key_pem: str = None) -> str:
    if public_key_pem is None:
        public_key_pem = get_server_public_key()
    
    aes_key = generate_aes_key()
    aes_iv = generate_aes_iv()
    
    message_bytes = message.encode('utf-8')
    encrypted_message = aes_encrypt(message_bytes, aes_key, aes_iv)
    
    encrypted_key = rsa_encrypt(aes_key + aes_iv, public_key_pem)
    
    result = base64.b64encode(encrypted_key).decode('utf-8') + '|' + base64.b64encode(encrypted_message).decode('utf-8')
    
    return result

def decrypt_message(encrypted_data: str, private_key_pem: str) -> str:
    encrypted_key_b64, encrypted_message_b64 = encrypted_data.split('|')
    
    encrypted_key = base64.b64decode(encrypted_key_b64)
    encrypted_message = base64.b64decode(encrypted_message_b64)
    
    key_iv = rsa_decrypt(encrypted_key, private_key_pem)
    aes_key = key_iv[:16]
    aes_iv = key_iv[16:]
    
    decrypted_message = aes_decrypt(encrypted_message, aes_key, aes_iv)
    
    return decrypted_message.decode('utf-8')
