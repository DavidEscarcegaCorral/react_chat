"""Proxy TCP entre API REST y servidor TCP. Reconexión automática en fallo."""

import socket
import threading
import time


class TCPClient:
    """Cliente TCP persistente con reconexión: conecta, envía CONECTADO, recibe en segundo plano."""

    def __init__(self, username, host, port, controller):
        from utils.logger_config import get_logger
        self.logger = get_logger('tcp_client')
        self.username = username
        self.host = host
        self.port = port
        self.controller = controller
        self.sock = None
        self.running = True
        self.recv_thread = None
        self.connect_lock = threading.Lock()
        self.dm_queue = []

    def start(self):
        threading.Thread(target=self._connect_loop, daemon=True).start()

    def _connect_loop(self):
        """Bucle: intenta conectar cada 1s, envía CONECTADO:, inicia recepción."""
        while self.running:
            if self.sock is None:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(5)
                    s.connect((self.host, self.port))
                    s.settimeout(None)
                    s.sendall(f'CONECTADO:{self.username}'.encode())
                    self.sock = s
                    self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
                    self.recv_thread.start()
                except Exception as e:
                    self.logger.error(f'Error conexión {self.username}: {e}')
                    self.sock = None
            time.sleep(1)

    def _recv_loop(self):
        while self.running and self.sock:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
            except:
                break
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        self.sock = None

    def send(self, message: str, recipient: str = 'all'):
        """Envía ALL:<user>: <msg>|<ts> o DM:<recip>:<user>: <msg>|<ts>."""
        if not self.sock:
            return False
        try:
            if recipient == 'all':
                payload = f'ALL:{self.username}: {message}|{time.time()}'.encode()
            else:
                payload = f'DM:{recipient}:{self.username}: {message}|{time.time()}'.encode()
            self.sock.sendall(payload)
            return True
        except Exception as e:
            self.logger.error(f'Error enviando: {e}')
            self.sock = None
            return False

    def stop(self):
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
