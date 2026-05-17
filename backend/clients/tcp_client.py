import socket
import threading
import time

class TCPClient:
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
        self.logger.info(f'Cliente TCP creado para {username}')

    def start(self):
        threading.Thread(target=self._connect_loop, daemon=True).start()

    def _connect_loop(self):
        while self.running:
            if self.sock is None:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(5)
                    s.connect((self.host, self.port))
                    s.settimeout(None)
                    
                    register_msg = f'CONECTADO:{self.username}'.encode()
                    s.sendall(register_msg)
                    
                    self.sock = s
                    self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
                    self.recv_thread.start()
                    self.logger.info(f'{self.username} conectado al servidor TCP')
                except Exception as e:
                    self.logger.error(f'Error de conexión para {self.username}: {e}')
                    self.sock = None
            time.sleep(1)

    def _recv_loop(self):
        while self.running and self.sock:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                
                decoded = data.decode()
                self.logger.debug(f'Mensaje recibido: {decoded}')
                
                if decoded.startswith('DM:') or decoded.startswith('DM_SENT:'):
                    self.logger.debug(f'DM procesado para {self.username}')
            
            except Exception as e:
                self.logger.error(f'Error recibiendo para {self.username}: {e}')
                break
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        self.sock = None

    def send(self, message: str, recipient: str = 'all'):
        if not self.sock:
            self.logger.error('Socket no disponible')
            return False
        
        try:
            if recipient == 'all':
                payload = f'ALL:{self.username}: {message}|{time.time()}'.encode()
            else:
                payload = f'DM:{recipient}:{self.username}: {message}|{time.time()}'.encode()
            
            self.sock.sendall(payload)
            self.logger.info(f'Mensaje enviado a {recipient}')
            return True
        except Exception as e:
            self.logger.error(f'Error enviando mensaje: {e}')
            self.sock = None
            return False

    def stop(self):
        self.logger.info(f'Deteniendo cliente {self.username}')
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
