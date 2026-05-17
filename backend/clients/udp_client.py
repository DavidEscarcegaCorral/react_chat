import socket
import threading
import time

class UDPClient:
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
        self.logger.info(f'Cliente UDP creado para {username}')

    def start(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(('', 0))
            local_port = self.sock.getsockname()[1]
            self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.recv_thread.start()
            self.logger.info(f'Cliente UDP {username} iniciado en puerto {local_port}')
        except Exception as e:
            self.logger.error(f'Error al iniciar cliente UDP: {e}')

    def _recv_loop(self):
        if not self.sock:
            return
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                decoded = data.decode()
                self.logger.debug(f'Mensaje recibido: {decoded}')
                
                if decoded.startswith('DM:'):
                    msg_content = decoded[3:]
                    self.dm_queue.append(msg_content)
                    self.logger.debug(f'DM agregado a cola: {msg_content}')
                elif decoded.startswith('DM_SENT:'):
                    self.logger.debug('Confirmación de DM enviado')
            
            except Exception as e:
                self.logger.error(f'Error recibiendo para {self.username}: {e}')
                break

    def get_dms(self):
        dms = self.dm_queue.copy()
        self.dm_queue.clear()
        return dms

    def send(self, message: str, recipient: str = 'all'):
        if not self.sock:
            self.logger.error('Socket no disponible')
            return False
        
        try:
            if recipient == 'all':
                payload = f'ALL:{self.username}: {message}|{time.time()}'.encode()
            else:
                payload = f'DM:{recipient}:{self.username}: {message}|{time.time()}'.encode()
            
            self.sock.sendto(payload, (self.host, self.port))
            self.logger.info(f'Mensaje enviado a {recipient}')
            return True
        except Exception as e:
            self.logger.error(f'Error enviando mensaje: {e}')
            return False

    def stop(self):
        self.logger.info(f'Deteniendo cliente {self.username}')
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
