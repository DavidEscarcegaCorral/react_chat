from core.tcp_server import TCPServer
from core.udp_server import UDPServer
from clients.tcp_client import TCPClient
from clients.udp_client import UDPClient
import threading
import asyncio
import json

MAX_HISTORY = 1000

class ServerController:
    def __init__(self):
        from utils.logger_config import get_logger
        self.logger = get_logger('server_controller')
        
        self.server = None
        self.protocol = None
        self.HOST = '127.0.0.1'
        self.PORT = 1060
        self.clients = set()
        self.client_objs = {}
        self.history = []
        self.user_dms = {}
        self._lock = threading.RLock()
        self._sse_queues = {}
        self._sse_lock = threading.RLock()
        self.logger.info('ServerController inicializado')

    def subscribe_sse(self, queue, loop):
        with self._sse_lock:
            if loop not in self._sse_queues:
                self._sse_queues[loop] = set()
            self._sse_queues[loop].add(queue)

    def unsubscribe_sse(self, queue, loop):
        with self._sse_lock:
            if loop in self._sse_queues:
                self._sse_queues[loop].discard(queue)

    def _notify_all(self, event_type, **data):
        payload = json.dumps({'event': event_type, **data})
        with self._sse_lock:
            for loop, queues in list(self._sse_queues.items()):
                dead = set()
                for q in queues:
                    try:
                        loop.call_soon_threadsafe(q.put_nowait, payload)
                    except:
                        dead.add(q)
                queues -= dead

    def run(self, protocol: str):
        self.logger.info(f'Intentando iniciar servidor: {protocol}')
        with self._lock:
            if self.server is not None:
                self.logger.warning('Servidor ya corriendo')
                return {'error': 'Servidor ya corriendo. Detén el servidor primero.'}
            try:
                if protocol == 'tcp':
                    self.server = TCPServer(self.HOST, self.PORT, self)
                elif protocol == 'udp':
                    self.server = UDPServer(self.HOST, self.PORT, self)
                else:
                    self.logger.error(f'Protocolo inválido: {protocol}')
                    return {'error': 'Protocolo inválido'}
                self.protocol = protocol
                self.server.start()
                
                ready = self.server.ready.wait(timeout=2)
                if not ready or not self.server.running:
                    self.logger.error(f'El servidor {protocol.upper()} no pudo iniciar')
                    self.server = None
                    self.protocol = None
                    return {'error': f'El servidor {protocol.upper()} no pudo iniciar correctamente'}
                self.logger.info(f'Servidor {protocol} iniciado exitosamente')
                self._notify_all('server_status', running=True, protocol=self.protocol, clients=list(self.clients), history_len=len(self.history))
                return {'status': f'Servidor {protocol} iniciado'}
            except Exception as e:
                self.logger.error(f'Error al iniciar servidor: {e}')
                self.server = None
                self.protocol = None
                return {'error': f'Error al iniciar servidor: {str(e)}'}

    def shutdown(self):
        self.logger.info('Solicitud de shutdown del servidor')
        with self._lock:
            if not self.server:
                self.logger.warning('No hay servidor corriendo')
                return {'status': 'No hay servidor corriendo'}
            
            for username, cli in list(self.client_objs.items()):
                try:
                    cli.stop()
                    self.logger.info(f'Cliente desconectado: {username}')
                except Exception as e:
                    self.logger.error(f'Error al desconectar cliente {username}: {e}')
            
            self.client_objs.clear()
            self.clients.clear()
            
            try:
                self.server.stop()
                if hasattr(self.server, 'join'):
                    self.server.join(timeout=2)
            except Exception as e:
                self.logger.error(f'Error al detener servidor: {e}')
            
            self.server = None
            self.protocol = None
            self._notify_all('server_status', running=False, protocol=None, clients=[], history_len=len(self.history))
            self.logger.info('Servidor detenido exitosamente')
            return {'status': 'Servidor detenido'}

    def is_running(self):
        return self.server is not None

    def create_client(self, username: str):
        self.logger.info(f'Creando cliente: {username}')
        with self._lock:
            if username in self.clients:
                self.logger.warning(f'Usuario {username} ya existe')
                return None
            if not self.is_running():
                self.logger.warning('Servidor no corriendo')
                return None
            
            self.clients.add(username)
            
            if self.protocol == 'tcp':
                client = TCPClient(username, self.HOST, self.PORT, self)
            elif self.protocol == 'udp':
                client = UDPClient(username, self.HOST, self.PORT, self)
            else:
                self.logger.error('Protocolo no definido')
                return None
            
            self.client_objs[username] = client
            client.start()
            
            self._notify_all('clients', clients=list(self.clients))
            self.logger.info(f'Cliente {username} creado exitosamente')
            return client

    def remove_client(self, username: str):
        self.logger.info(f'Removiendo cliente: {username}')
        with self._lock:
            if username in self.client_objs:
                try:
                    self.client_objs[username].stop()
                    self.logger.info(f'Cliente {username} desconectado')
                except Exception as e:
                    self.logger.error(f'Error al desconectar {username}: {e}')
                del self.client_objs[username]
            if username in self.clients:
                self.clients.remove(username)
            self._notify_all('clients', clients=list(self.clients))

    def add_history(self, msg: str):
        with self._lock:
            self.history.append(msg)
            if len(self.history) > MAX_HISTORY:
                self.history.pop(0)
        self._notify_all('broadcast', message=msg)

    def notify_dm(self, sender: str, recipient: str, content: str):
        self._notify_all('dm', from_user=sender, to_user=recipient, content=content)

    def get_user_dms(self, username: str):
        dm_key = f'dm_{username}'
        dms = self.user_dms.get(dm_key, []).copy()
        if dm_key in self.user_dms:
            self.user_dms[dm_key].clear()
        return dms
