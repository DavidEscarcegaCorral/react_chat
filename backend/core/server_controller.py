"""Orquestador: servidores TCP/UDP, clientes proxy, historial (max 1000), DMs y notificaciones SSE."""

from core.tcp_server import TCPServer
from core.udp_server import UDPServer
from clients.tcp_client import TCPClient
from clients.udp_client import UDPClient
import threading
import asyncio
import json

MAX_HISTORY = 1000


class ServerController:
    """Gestiona servidores de socket, clientes proxy, historial, cola de DMs y suscripciones SSE."""

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

    # ── SSE suscripciones ──

    def subscribe_sse(self, queue, loop):
        """Registra una cola asyncio para recibir eventos SSE."""
        with self._sse_lock:
            if loop not in self._sse_queues:
                self._sse_queues[loop] = set()
            self._sse_queues[loop].add(queue)

    def unsubscribe_sse(self, queue, loop):
        """Elimina una cola asyncio de las suscripciones SSE."""
        with self._sse_lock:
            if loop in self._sse_queues:
                self._sse_queues[loop].discard(queue)

    def _notify_all(self, event_type, **data):
        """Envía un evento JSON a todas las colas SSE suscritas."""
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

    # ── Ciclo de vida del servidor ──

    def run(self, protocol: str):
        """Inicia servidor TCP o UDP. Espera hasta 2s por señal de listo."""
        with self._lock:
            if self.server is not None:
                return {'error': 'Servidor ya corriendo'}
            try:
                if protocol == 'tcp':
                    self.server = TCPServer(self.HOST, self.PORT, self)
                elif protocol == 'udp':
                    self.server = UDPServer(self.HOST, self.PORT, self)
                else:
                    return {'error': 'Protocolo inválido'}
                self.protocol = protocol
                self.server.start()
                ready = self.server.ready.wait(timeout=2)
                if not ready or not self.server.running:
                    self.server = None
                    self.protocol = None
                    return {'error': f'Servidor {protocol.upper()} no pudo iniciar'}
                self._notify_all('server_status', running=True, protocol=self.protocol, clients=list(self.clients), history_len=len(self.history))
                return {'status': f'Servidor {protocol} iniciado'}
            except Exception as e:
                self.server = None
                self.protocol = None
                return {'error': str(e)}

    def shutdown(self):
        """Detiene clientes proxy y servidor de socket, notifica SSE."""
        with self._lock:
            if not self.server:
                return {'status': 'No hay servidor corriendo'}
            for username, cli in list(self.client_objs.items()):
                try:
                    cli.stop()
                except Exception as e:
                    self.logger.error(f'Error desconectando {username}: {e}')
            self.client_objs.clear()
            self.clients.clear()
            try:
                self.server.stop()
                if hasattr(self.server, 'join'):
                    self.server.join(timeout=2)
            except Exception as e:
                self.logger.error(f'Error deteniendo servidor: {e}')
            self.server = None
            self.protocol = None
            self._notify_all('server_status', running=False, protocol=None, clients=[], history_len=len(self.history))
            return {'status': 'Servidor detenido'}

    def is_running(self):
        return self.server is not None

    # ── Gestión de clientes proxy ──

    def create_client(self, username: str):
        """Crea TCPClient o UDPClient según protocolo activo."""
        with self._lock:
            if username in self.clients:
                return None
            if not self.is_running():
                return None
            self.clients.add(username)
            if self.protocol == 'tcp':
                client = TCPClient(username, self.HOST, self.PORT, self)
            elif self.protocol == 'udp':
                client = UDPClient(username, self.HOST, self.PORT, self)
            else:
                return None
            self.client_objs[username] = client
            client.start()
            self._notify_all('clients', clients=list(self.clients))
            return client

    def remove_client(self, username: str):
        """Detiene y elimina un cliente proxy, notifica SSE."""
        with self._lock:
            if username in self.client_objs:
                try:
                    self.client_objs[username].stop()
                except:
                    pass
                del self.client_objs[username]
            if username in self.clients:
                self.clients.remove(username)
            self._notify_all('clients', clients=list(self.clients))

    # ── Historial y DMs ──

    def add_history(self, msg: str):
        with self._lock:
            self.history.append(msg)
            if len(self.history) > MAX_HISTORY:
                self.history.pop(0)
        self._notify_all('broadcast', message=msg)

    def notify_dm(self, sender: str, recipient: str, content: str):
        self._notify_all('dm', from_user=sender, to_user=recipient, content=content)

    def get_user_dms(self, username: str):
        """Recupera y limpia los DMs pendientes del usuario."""
        dm_key = f'dm_{username}'
        dms = self.user_dms.get(dm_key, []).copy()
        if dm_key in self.user_dms:
            self.user_dms[dm_key].clear()
        return dms
