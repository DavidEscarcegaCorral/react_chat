import socket
import threading

class TCPServer(threading.Thread):
    def __init__(self, ip, port, controller):
        from utils.logger_config import get_logger
        self.logger = get_logger('tcp_server')
        
        super().__init__(daemon=True)
        self.ip = ip
        self.port = port
        self.controller = controller
        self.clients = {}
        self.running = True
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((ip, port))
        self.server.listen()
        self.logger.info(f'TCP Server escuchando en {ip}:{port}')

    def run(self):
        self.logger.info('TCP Server started')
        while self.running:
            try:
                conn, addr = self.server.accept()
            except:
                break
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def broadcast(self, message, source_sock):
        try:
            decoded = message.decode()
            self.logger.debug(f'Mensaje recibido: {decoded}')
            
            if decoded.startswith('ALL:'):
                msg_content = decoded[4:]
                self.logger.info(f'Broadcast: {msg_content}')
                
                self.controller.add_history(msg_content)
                
                for c in list(self.clients.keys()):
                    if c != source_sock:
                        try:
                            c.sendall(message)
                        except:
                            self._remove_client(c)
            
            elif decoded.startswith('DM:'):
                parts = decoded.split(':', 3)
                
                if len(parts) >= 4:
                    recipient = parts[1]
                    sender_and_msg = ':'.join(parts[2:])
                    
                    sender_username = self.clients.get(source_sock, 'unknown')
                    self.logger.info(f'DM de {sender_username} para {recipient}')
                    
                    dm_key = f'dm_{recipient}'
                    if dm_key not in self.controller.user_dms:
                        self.controller.user_dms[dm_key] = []
                    self.controller.user_dms[dm_key].append(sender_and_msg)
                    
                    recipient_sock = None
                    for sock, username in self.clients.items():
                        if username == recipient:
                            recipient_sock = sock
                            break
                    
                    if recipient_sock:
                        try:
                            dm_msg = f'DM:{sender_and_msg}'.encode()
                            recipient_sock.sendall(dm_msg)
                        except Exception as e:
                            self.logger.error(f'Error enviando DM: {e}')
                            self._remove_client(recipient_sock)
                    
                    try:
                        confirm_msg = f'DM_SENT:{sender_and_msg}'.encode()
                        source_sock.sendall(confirm_msg)
                    except Exception as e:
                        self.logger.error(f'Error enviando confirmación: {e}')
        except Exception as e:
            self.logger.error(f'Error en broadcast: {e}')

    def _remove_client(self, conn):
        try:
            if conn in self.clients:
                username = self.clients[conn]
                del self.clients[conn]
                self.logger.info(f'Cliente desconectado: {username}')
            conn.close()
        except Exception as e:
            self.logger.error(f'Error al remover cliente: {e}')

    def handle_client(self, conn, addr):
        username = None
        self.logger.info(f'Nueva conexión desde {addr}')
        
        while self.running:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                
                decoded = data.decode()
                
                if decoded.startswith('CONECTADO:'):
                    username = decoded.split(':', 1)[1]
                    self.clients[conn] = username
                    self.logger.info(f'Usuario {username} conectado')
                    continue
                
                self.broadcast(data, conn)
            
            except Exception as e:
                self.logger.error(f'Error manejando cliente: {e}')
                break
        
        self._remove_client(conn)
        if username:
            self.logger.info(f'Usuario {username} desconectado')

    def stop(self):
        self.logger.info('Deteniendo TCP Server')
        self.running = False
        try:
            self.server.close()
        except Exception as e:
            self.logger.error(f'Error cerrando server socket: {e}')
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.ip, self.port))
            s.close()
        except Exception as e:
            self.logger.error(f'Error cerrando conexión dummy: {e}')
        for c in list(self.clients.keys()):
            try:
                c.close()
            except Exception as e:
                self.logger.error(f'Error cerrando socket cliente: {e}')
        self.clients.clear()
        self.logger.info('TCP Server detenido')
