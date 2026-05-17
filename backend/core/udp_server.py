import socket
import threading

class UDPServer(threading.Thread):
    def __init__(self, ip, port, controller):
        from utils.logger_config import get_logger
        self.logger = get_logger('udp_server')
        
        super().__init__(daemon=True)
        self.ip = ip
        self.port = port
        self.controller = controller
        self.server = None
        self.running = False
        self.clients = {}
        self.username_to_addr = {}
        self.init_error = None
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((ip, port))
            self.running = True
            self.logger.info(f'UDP Server escuchando en {ip}:{port}')
        except Exception as e:
            self.init_error = str(e)
            self.running = False
            self.logger.error(f'Error al iniciar UDP Server: {e}')
            if self.server:
                try:
                    self.server.close()
                except:
                    pass
                self.server = None

    def run(self):
        if not self.running or not self.server:
            return
        try:
            self.server.settimeout(1.0)
        except Exception as e:
            self.running = False
            return
        
        self.logger.info('UDP Server started')
        
        while self.running:
            try:
                data, addr = self.server.recvfrom(1024)
                try:
                    decoded = data.decode()
                    
                    if decoded.startswith('Conectado:'):
                        username = decoded.split(':', 1)[1]
                        self.clients[addr] = username
                        self.username_to_addr[username] = addr
                        self.logger.info(f'Usuario {username} conectado desde {addr}')
                        continue
                    
                    if addr not in self.clients:
                        self.clients[addr] = f'unknown_{addr[1]}'
                        self.username_to_addr[self.clients[addr]] = addr
                    
                    if decoded.startswith('ALL:'):
                        msg_content = decoded[4:]
                        self.logger.info(f'Broadcast: {msg_content}')
                        
                        self.controller.history.append(msg_content)
                        
                        for client_addr in list(self.clients.keys()):
                            if client_addr != addr:
                                try:
                                    self.server.sendto(data, client_addr)
                                except Exception as e:
                                    self._remove_client(client_addr)
                    
                    elif decoded.startswith('DM:'):
                        parts = decoded.split(':', 3)
                        
                        if len(parts) >= 4:
                            recipient = parts[1]
                            sender_and_msg = ':'.join(parts[2:])
                            
                            sender_username = self.clients.get(addr, 'unknown')
                            self.logger.info(f'DM de {sender_username} para {recipient}')
                            
                            dm_key = f'dm_{recipient}'
                            if dm_key not in self.controller.user_dms:
                                self.controller.user_dms[dm_key] = []
                            self.controller.user_dms[dm_key].append(sender_and_msg)
                            
                            recipient_addr = self.username_to_addr.get(recipient)
                            
                            if recipient_addr:
                                try:
                                    dm_msg = f'DM:{sender_and_msg}'.encode()
                                    self.server.sendto(dm_msg, recipient_addr)
                                except Exception as e:
                                    self.logger.error(f'Error enviando DM: {e}')
                                    self._remove_client(recipient_addr)
                            
                            try:
                                confirm_msg = f'DM_SENT:{sender_and_msg}'.encode()
                                self.server.sendto(confirm_msg, addr)
                            except Exception as e:
                                self.logger.error(f'Error enviando confirmación: {e}')
                
                except Exception as e:
                    self.logger.error(f'Error decodificando: {e}')
                    continue
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f'Error: {e}')
                break

    def _remove_client(self, addr):
        try:
            if addr in self.clients:
                username = self.clients[addr]
                del self.clients[addr]
                if username in self.username_to_addr:
                    del self.username_to_addr[username]
                self.logger.info(f'Cliente removido: {username}')
        except:
            pass

    def stop(self):
        self.logger.info('Deteniendo UDP Server')
        self.running = False
        self.clients.clear()
        self.username_to_addr.clear()
        if self.server:
            try:
                self.server.close()
            except Exception as e:
                pass
        self.logger.info('UDP Server detenido')
