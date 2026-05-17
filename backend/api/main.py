from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from core.server_controller import ServerController
from routes.server import router as server_router
from routes.client import router as client_router
from routes.auth import router as auth_router
from utils.logger_config import get_logger
from security.crypto_manager import initialize as init_crypto

logger = get_logger('api')

def main():
    app = FastAPI()
    app.state.server = ServerController()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
    
    init_crypto()
    logger.info('Servidor API iniciado - Crypto RSA inicializado')
    
    app.include_router(auth_router, prefix='/auth', tags=['Auth'])
    app.include_router(server_router, prefix='/server', tags=['Server'])
    app.include_router(client_router, prefix='/client', tags=['Client'])
    
    return app

app = main()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('api.main:app', host='0.0.0.0', port=8000, reload=True)
