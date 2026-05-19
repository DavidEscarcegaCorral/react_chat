"""Servidor TCP (SOCK_STREAM): maneja conexiones persistentes con protocolo CONECTADO/ALL/DM/DM_SENT."""

import socket
import threading


class TCPServer(threading.Thread):
    """Thread daemon que acepta conexiones, registra usuarios y enruta broadcasts y DMs."""

    def __init__(self, ip, port, controller):
        from utils.logger_config import get_logger
        self.logger = get_logger('tcp_server')
        super().__init__(daemon=True)
        self.ip = ip
        self.port = port
        self.controller = controller
        self.clients = {}
        self.running = True
        self.ready = threading.Event()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((ip, port))
        self.server.listen()
        self.ready.set()

    def run(self):
        while self.running:
            try:
                conn, addr = self.server.accept()
            except:
                break
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def broadcast(self, message, source_sock):
        """Procesa ALL: (reenvío a todos) y DM: (envío directo + confirmación DM_SENT)."""
        try:
            decoded = message.decode()
            if decoded.startswith('ALL:'):
                msg_content = decoded[4:]
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
                    dm_key = f'dm_{recipient}'
                    if dm_key not in self.controller.user_dms:
                        self.controller.user_dms[dm_key] = []
                    self.controller.user_dms[dm_key].append(sender_and_msg)
                    recipient_sock = next((s for s, u in self.clients.items() if u == recipient), None)
                    if recipient_sock:
                        try:
                            recipient_sock.sendall(f'DM:{sender_and_msg}'.encode())
                        except Exception as e:
                            self.logger.error(f'Error DM: {e}')
                            self._remove_client(recipient_sock)
                    try:
                        source_sock.sendall(f'DM_SENT:{sender_and_msg}'.encode())
                    except Exception as e:
                        self.logger.error(f'Error confirmación: {e}')
        except Exception as e:
            self.logger.error(f'Error en broadcast: {e}')

    def _remove_client(self, conn):
        try:
            if conn in self.clients:
                del self.clients[conn]
            conn.close()
        except Exception as e:
            self.logger.error(f'Error removiendo cliente: {e}')

    def handle_client(self, conn, addr):
        """Lee mensajes del socket: CONECTADO: registra, otros van a broadcast()."""
        username = None
        while self.running:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                decoded = data.decode()
                if decoded.startswith('CONECTADO:'):
                    username = decoded.split(':', 1)[1]
                    self.clients[conn] = username
                    continue
                self.broadcast(data, conn)
            except Exception as e:
                self.logger.error(f'Error manejando cliente: {e}')
                break
        self._remove_client(conn)

    def stop(self):
        """Cierra server socket, envía conexión dummy para desbloquear accept(), cierra sockets cliente."""
        self.running = False
        try:
            self.server.close()
        except:
            pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.ip, self.port))
            s.close()
        except:
            pass
        for c in list(self.clients.keys()):
            try:
                c.close()
            except:
                pass
        self.clients.clear()
