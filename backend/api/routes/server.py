from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ProtocolData(BaseModel):
    protocol: str

def verify_token(authorization: Optional[str]):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Token requerido')
    from security.auth_manager import verify_token
    token = authorization.replace('Bearer ', '')
    valid, username = verify_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail='Token inválido o expirado')
    return username

@router.post('/run')
def run(req: Request, data: ProtocolData, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    server = req.app.state.server
    return server.run(data.protocol)

@router.post('/shutdown')
def shutdown(req: Request, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    server = req.app.state.server
    server.shutdown()
    server.clients.clear()
    return {'status': 'Servidor detenido'}

@router.delete('/clear')
def clear(req: Request, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
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
