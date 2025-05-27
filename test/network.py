import socket
import threading
import json
import time
import sys
from queue import Queue
from PyQt5.QtCore import QObject, pyqtSignal

DISCOVERY_PORT = 50000
TCP_PORT = 12345
BROADCAST_ADDR = '<broadcast>'

class NetworkManager(QObject):
    message_received = pyqtSignal(str, str, str)  # sender_phone, message, timestamp
    peer_discovered = pyqtSignal(str)  # peer_phone
    peer_status_changed = pyqtSignal(str, bool)  # peer_phone, is_online

    def __init__(self):
        super().__init__()
        self.peer_map = {}  # Format: {phone_number: ip}
        self.my_phone = ""
        self.stop_discovery = False
        self.message_queue = Queue()

    def start_services(self, phone_number):
        self.my_phone = phone_number
        self.stop_discovery = False
        
        # Start background threads
        threading.Thread(target=self.udp_listener, daemon=True).start()
        threading.Thread(target=self.tcp_server, daemon=True).start()
        threading.Thread(target=self.udp_discover_peers, daemon=True).start()

    def stop_services(self):
        self.stop_discovery = True

    def udp_listener(self):
        """Respond to discovery requests with own ID."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', DISCOVERY_PORT))

        while not self.stop_discovery:
            try:
                msg, addr = sock.recvfrom(1024)
                msg_data = json.loads(msg.decode())
                if msg_data.get("type") == "DISCOVER_PEER":
                    response = json.dumps({
                        "type": "PEER_HERE",
                        "phone": self.my_phone
                    })
                    sock.sendto(response.encode(), addr)
            except Exception:
                continue
        sock.close()

    def udp_discover_peers(self):
        """Continuously discover peers via UDP broadcast."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1)

        while not self.stop_discovery:
            try:
                discover_msg = json.dumps({
                    "type": "DISCOVER_PEER",
                    "phone": self.my_phone
                })
                sock.sendto(discover_msg.encode(), (BROADCAST_ADDR, DISCOVERY_PORT))
                
                while True:
                    try:
                        data, addr = sock.recvfrom(1024)
                        response = json.loads(data.decode())
                        if response.get("type") == "PEER_HERE":
                            peer_phone = response.get("phone")
                            if peer_phone and peer_phone != self.my_phone:
                                old_status = peer_phone in self.peer_map
                                self.peer_map[peer_phone] = addr[0]
                                if not old_status:
                                    self.peer_discovered.emit(peer_phone)
                                self.peer_status_changed.emit(peer_phone, True)
                    except socket.timeout:
                        break
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass
            time.sleep(5)  # Check every 5 seconds
        sock.close()

    def tcp_server(self):
        """Handle incoming TCP connections."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('', TCP_PORT))
        server.listen(5)

        while not self.stop_discovery:
            try:
                client, addr = server.accept()
                threading.Thread(target=self.handle_client,
                              args=(client, addr),
                              daemon=True).start()
            except Exception:
                if not self.stop_discovery:
                    continue
                break
        server.close()

    def handle_client(self, sock, addr):
        """Process received messages."""
        try:
            data = sock.recv(1024)
            if data:
                message_data = json.loads(data.decode())
                sender_phone = message_data.get("sender")
                message = message_data.get("message")
                timestamp = message_data.get("timestamp")
                if sender_phone and message:
                    self.message_received.emit(sender_phone, message, timestamp)
        except Exception:
            pass
        finally:
            sock.close()

    def send_message(self, receiver_phone, message):
        """Send a message to a specific peer."""
        if receiver_phone not in self.peer_map:
            return False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.peer_map[receiver_phone], TCP_PORT))
            
            message_data = {
                "sender": self.my_phone,
                "message": message,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            sock.send(json.dumps(message_data).encode())
            sock.close()
            return True
        except Exception:
            return False

    def is_peer_online(self, phone_number):
        """Check if a peer is currently online."""
        return phone_number in self.peer_map 