from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class LoginData(BaseModel):
    username: str

class MessageData(BaseModel):
    message: str
    username: str
    recipient: str = 'all'

def verify_token(authorization: Optional[str]):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Token requerido')
    from security.auth_manager import verify_token
    token = authorization.replace('Bearer ', '')
    valid, username = verify_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail='Token inválido o expirado')
    return username

@router.post('/login')
def login(req: Request, data: LoginData, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    server = req.app.state.server
    
    if not server.is_running():
        return {'error': 'No hay servidor corriendo. Inicia el servidor primero.'}
    
    if data.username in server.clients:
        return {'error': 'El usuario ya existe'}
    
    client = server.create_client(data.username)
    if client is None:
        return {'error': 'No se pudo crear el cliente'}
    return {'status': 'OK', 'username': data.username}

@router.post('/logout')
def logout(req: Request, data: LoginData, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    server = req.app.state.server
    server.remove_client(data.username)
    return {'status': 'OK', 'username': data.username}

@router.post('/send')
def send(req: Request, data: MessageData, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    server = req.app.state.server
    
    if data.username not in server.client_objs:
        return {'error': 'Cliente no conectado. Recarga la página e intenta de nuevo.'}
    
    if data.recipient != 'all' and data.recipient not in server.clients:
        return {'error': f'El usuario \'{data.recipient}\' no existe o no está conectado'}
    
    client = server.client_objs[data.username]
    
    try:
        success = client.send(data.message, data.recipient)
        if success:
            return {'status': 'Mensaje enviado', 'recipient': data.recipient}
        else:
            return {'error': 'No se pudo enviar el mensaje. El socket no está disponible.'}
    except Exception as e:
        return {'error': f'Error al enviar: {str(e)}'}

@router.get('/history')
def history(req: Request, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    server = req.app.state.server
    return {'history': server.history}

@router.get('/clients')
def list_clients(req: Request, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    server = req.app.state.server
    return {'clients': list(server.clients)}

@router.get('/dms/{username}')
def get_dms(req: Request, username: str, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    server = req.app.state.server
    dms = server.get_user_dms(username)
    return {'dms': dms}
