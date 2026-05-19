"""Proxy UDP entre API REST y servidor UDP. Puerto efímero con cola local de DMs."""

import socket
import threading
import time


class UDPClient:
    """Cliente UDP: bind a puerto efímero, envía CONECTADO:, recibe datagramas en segundo plano."""

    def __init__(self, username, host, port, controller):
        from utils.logger_config import get_logger
        self.logger = get_logger('udp_client')
        self.username = username
        self.host = host
        self.port = port
        self.controller = controller
        self.sock = None
        self.running = True
        self.recv_thread = None
        self.dm_queue = []

    def start(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(('', 0))
            self.sock.sendto(f'CONECTADO:{self.username}'.encode(), (self.host, self.port))
            self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.recv_thread.start()
        except Exception as e:
            self.logger.error(f'Error iniciando UDP {self.username}: {e}')

    def _recv_loop(self):
        if not self.sock:
            return
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                decoded = data.decode()
                if decoded.startswith('DM:'):
                    self.dm_queue.append(decoded[3:])
                elif decoded.startswith('DM_SENT:'):
                    pass
            except:
                break

    def get_dms(self):
        dms = self.dm_queue.copy()
        self.dm_queue.clear()
        return dms

    def send(self, message: str, recipient: str = 'all'):
        """Envía ALL:<user>: <msg>|<ts> o DM:<recip>:<user>: <msg>|<ts> como datagrama."""
        if not self.sock:
            return False
        try:
            if recipient == 'all':
                payload = f'ALL:{self.username}: {message}|{time.time()}'.encode()
            else:
                payload = f'DM:{recipient}:{self.username}: {message}|{time.time()}'.encode()
            self.sock.sendto(payload, (self.host, self.port))
            return True
        except Exception as e:
            self.logger.error(f'Error enviando: {e}')
            return False

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
