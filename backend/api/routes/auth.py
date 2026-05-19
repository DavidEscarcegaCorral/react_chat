"""Endpoints de autenticación: registro, login (JWT + clave pública), logout y verify."""

from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from security import register_user, login_user, verify_token, logout_user, get_server_public_key

router = APIRouter()


class RegisterData(BaseModel):
    username: str
    password: str


class LoginData(BaseModel):
    username: str
    password: str


@router.post('/register')
def register(data: RegisterData):
    success, message = register_user(data.username, data.password)
    if success:
        return {'status': 'ok', 'message': message}
    raise HTTPException(status_code=400, detail=message)


@router.post('/login')
def login(data: LoginData):
    """Retorna token JWT y clave pública RSA para cifrado de mensajes."""
    success, message, token = login_user(data.username, data.password)
    if success:
        return {
            'status': 'ok', 'message': message, 'token': token,
            'username': data.username, 'public_key': get_server_public_key()
        }
    raise HTTPException(status_code=401, detail=message)


@router.post('/logout')
def logout(authorization: Optional[str] = Header(None)):
    """Invalida el token JWT (lo agrega a blacklist)."""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Token requerido')
    token = authorization.replace('Bearer ', '')
    if logout_user(token):
        return {'status': 'ok', 'message': 'Logout exitoso'}
    raise HTTPException(status_code=400, detail='Token inválido')


@router.get('/verify')
def verify(authorization: Optional[str] = Header(None)):
    """Verifica que el token sea válido y no esté expirado."""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Token requerido')
    token = authorization.replace('Bearer ', '')
    valid, username = verify_token(token)
    if valid:
        return {'status': 'ok', 'username': username}
    raise HTTPException(status_code=401, detail='Token inválido o expirado')
