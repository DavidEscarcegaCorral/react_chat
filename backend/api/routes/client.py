from fastapi import APIRouter, Request, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import asyncio
import json

router = APIRouter()

class LoginData(BaseModel):
    username: str

class MessageData(BaseModel):
    message: str
    username: str
    recipient: str = 'all'

def _extract_token(authorization: Optional[str] = None, token_param: Optional[str] = None):
    if authorization and authorization.startswith('Bearer '):
        return authorization.replace('Bearer ', '')
    if token_param:
        return token_param
    return None

def _verify_token_raw(token: str):
    from security.auth_manager import verify_token
    valid, username = verify_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail='Token inválido o expirado')
    return username

def verify_token(authorization: Optional[str]):
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail='Token requerido')
    return _verify_token_raw(token)

def decrypt_payload(encrypted: str) -> str:
    if '|' not in encrypted:
        return encrypted
    from security.message_encryptor import decrypt_message
    from security.crypto_manager import get_server_private_key
    try:
        return decrypt_message(encrypted, get_server_private_key())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error al descifrar mensaje: {str(e)}')

@router.post('/login')
def login(req: Request, data: LoginData, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    server = req.app.state.server
    
    if not server.is_running():
        raise HTTPException(status_code=503, detail='No hay servidor corriendo. Inicia el servidor primero.')
    
    if data.username in server.clients:
        raise HTTPException(status_code=409, detail='El usuario ya existe')
    
    client = server.create_client(data.username)
    if client is None:
        raise HTTPException(status_code=500, detail='No se pudo crear el cliente')
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
    
    plaintext = decrypt_payload(data.message)
    if len(plaintext) > 500:
        return {'error': 'El mensaje no puede tener más de 500 caracteres'}
    client = server.client_objs[data.username]
    
    try:
        success = client.send(plaintext, data.recipient)
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

@router.get('/events')
async def event_stream(
    req: Request,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    raw = _extract_token(authorization, token)
    if not raw:
        raise HTTPException(status_code=401, detail='Token requerido')
    current_user = _verify_token_raw(raw)
    server = req.app.state.server

    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    server.subscribe_sse(queue, loop)

    async def generate():
        try:
            while True:
                if await req.is_disconnected():
                    break
                try:
                    raw_data = await asyncio.wait_for(queue.get(), timeout=30)
                    parsed = json.loads(raw_data)
                    event_type = parsed.pop('event', None)

                    if event_type == 'dm':
                        if parsed.get('to_user') != current_user:
                            continue

                    yield f"event: {event_type}\ndata: {json.dumps(parsed)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        finally:
            server.unsubscribe_sse(queue, loop)

    return StreamingResponse(generate(), media_type='text/event-stream')
