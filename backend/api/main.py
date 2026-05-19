"""Punto de entrada FastAPI: configura CORS, inicializa RSA y monta routers /auth, /server, /client."""

import os
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from core.server_controller import ServerController
from api.routes.server import router as server_router
from api.routes.client import router as client_router
from api.routes.auth import router as auth_router
from utils.logger_config import get_logger
from security.crypto_manager import initialize as init_crypto

load_dotenv()
logger = get_logger('api')


def get_cors_origins():
    return [o.strip() for o in os.environ.get('CORS_ORIGINS', '').split(',') if o.strip()]


def main():
    app = FastAPI()
    app.state.server = ServerController()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_origin_regex=r'https?://localhost(:\d+)?',
        allow_credentials=True, allow_methods=['*'], allow_headers=['*']
    )
    init_crypto()
    app.include_router(auth_router, prefix='/auth', tags=['Auth'])
    app.include_router(server_router, prefix='/server', tags=['Server'])
    app.include_router(client_router, prefix='/client', tags=['Client'])
    return app


app = main()

if __name__ == '__main__':
    import uvicorn
    host = os.environ.get('API_HOST', '0.0.0.0')
    port = int(os.environ.get('API_PORT', '8000'))
    uvicorn.run('api.main:app', host=host, port=port, reload=True)
