"""Servidor UDP (SOCK_DGRAM): misma semántica que TCP pero sobre datagramas sin conexión."""

import socket
import threading


class UDPServer(threading.Thread):
    """Thread daemon que recibe datagramas, mantiene mapeo addr↔username y enruta mensajes."""

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
        self.ready = threading.Event()
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((ip, port))
            self.running = True
            self.ready.set()
        except Exception as e:
            self.init_error = str(e)
            self.running = False
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
        except:
            self.running = False
            return

        while self.running:
            try:
                data, addr = self.server.recvfrom(1024)
                try:
                    decoded = data.decode()
                    if decoded.startswith('CONECTADO:'):
                        username = decoded.split(':', 1)[1]
                        self.clients[addr] = username
                        self.username_to_addr[username] = addr
                        continue
                    if addr not in self.clients:
                        self.clients[addr] = f'unknown_{addr[1]}'
                        self.username_to_addr[self.clients[addr]] = addr
                    if decoded.startswith('ALL:'):
                        msg_content = decoded[4:]
                        self.controller.add_history(msg_content)
                        for client_addr in list(self.clients.keys()):
                            if client_addr != addr:
                                try:
                                    self.server.sendto(data, client_addr)
                                except:
                                    self._remove_client(client_addr)
                    elif decoded.startswith('DM:'):
                        parts = decoded.split(':', 3)
                        if len(parts) >= 4:
                            recipient, sender_and_msg = parts[1], ':'.join(parts[2:])
                            dm_key = f'dm_{recipient}'
                            if dm_key not in self.controller.user_dms:
                                self.controller.user_dms[dm_key] = []
                            self.controller.user_dms[dm_key].append(sender_and_msg)
                            recipient_addr = self.username_to_addr.get(recipient)
                            if recipient_addr:
                                try:
                                    self.server.sendto(f'DM:{sender_and_msg}'.encode(), recipient_addr)
                                except:
                                    self._remove_client(recipient_addr)
                            try:
                                self.server.sendto(f'DM_SENT:{sender_and_msg}'.encode(), addr)
                            except:
                                pass
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
                username = self.clients.pop(addr, None)
                self.username_to_addr.pop(username, None)
        except:
            pass

    def stop(self):
        self.running = False
        self.clients.clear()
        self.username_to_addr.clear()
        if self.server:
            try:
                self.server.close()
            except:
                pass
