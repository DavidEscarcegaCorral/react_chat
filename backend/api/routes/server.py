from fastapi import APIRouter, Request, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os
import asyncio
import json

router = APIRouter()

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')

class ProtocolData(BaseModel):
    protocol: str

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

def verify_admin(authorization: Optional[str]):
    username = verify_token(authorization)
    if username != ADMIN_USERNAME:
        raise HTTPException(status_code=403, detail='Acceso denegado: se requieren permisos de administrador')
    return username

@router.post('/run')
def run(req: Request, data: ProtocolData, authorization: Optional[str] = Header(None)):
    verify_admin(authorization)
    server = req.app.state.server
    return server.run(data.protocol)

@router.post('/shutdown')
def shutdown(req: Request, authorization: Optional[str] = Header(None)):
    verify_admin(authorization)
    server = req.app.state.server
    server.shutdown()
    return {'status': 'Servidor detenido'}

@router.delete('/clear')
def clear(req: Request, authorization: Optional[str] = Header(None)):
    verify_admin(authorization)
    server = req.app.state.server
    server.history.clear()
    return {'status': 'Historial borrado'}

@router.get('/status')
def status(req: Request, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    server = req.app.state.server
    return {
        'running': server.is_running(),
        'protocol': server.protocol,
        'host': server.HOST,
        'port': server.PORT,
        'clients': list(server.clients),
        'history_len': len(server.history)
    }

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
    if current_user != ADMIN_USERNAME:
        raise HTTPException(status_code=403, detail='Acceso denegado: se requieren permisos de administrador')

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

                    if event_type not in ('server_status', 'clients', 'broadcast'):
                        continue

                    yield f"event: {event_type}\ndata: {json.dumps(parsed)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        finally:
            server.unsubscribe_sse(queue, loop)

    return StreamingResponse(generate(), media_type='text/event-stream')
