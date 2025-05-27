import socket
import threading
import json
import time
from queue import Queue
from flask import current_app
from app import socketio, db
from app.models import User, Message
import socket
import ipaddress
from datetime import datetime
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser

class NetworkManager:
    def __init__(self, user_phone):
        self.user_phone = user_phone  # This will be our unique ID
        self.tcp_port = 12345
        self.peers = {}  # Format: {phone_number: {'ip': ip}}
        self.message_queue = Queue()
        self.running = False
        
        # Initialize Zeroconf
        self.zeroconf = Zeroconf()
        self.service_type = "_chatapp._tcp.local."
        self.service_name = f"{self.user_phone}.{self.service_type}"
        
        # Get local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't need to be reachable
            s.connect(('10.255.255.255', 1))
            self.local_ip = s.getsockname()[0]
        except Exception:
            self.local_ip = '127.0.0.1'
        finally:
            s.close()
        
        # Create TCP socket for messaging
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind(('', self.tcp_port))
        self.tcp_socket.listen(5)

    def start(self):
        self.running = True
        
        # Register our service
        self._register_service()
        
        # Start service browser
        self.browser = ServiceBrowser(self.zeroconf, self.service_type, self)
        
        # Start TCP messaging threads
        threading.Thread(target=self._tcp_server, daemon=True).start()
        threading.Thread(target=self._process_message_queue, daemon=True).start()

    def stop(self):
        self.running = False
        try:
            self.zeroconf.unregister_service(self.info)
            self.zeroconf.close()
            self.tcp_socket.close()
        except:
            pass

    def _register_service(self):
        """Register our service with Zeroconf"""
        self.info = ServiceInfo(
            self.service_type,
            self.service_name,
            addresses=[socket.inet_aton(self.local_ip)],
            port=self.tcp_port,
            properties={
                'phone': self.user_phone.encode('utf-8')
            }
        )
        self.zeroconf.register_service(self.info)

    def send_message(self, receiver_phone, content, message_id):
        """Send a message to a peer"""
        try:
            peer_info = self.peers.get(receiver_phone)
            if not peer_info:
                return False
                
            message_data = {
                'type': 'message',
                'message_id': message_id,
                'sender_phone': self.user_phone,
                'content': content
            }
            
            return self.send_tcp_message(peer_info['ip'], json.dumps(message_data))
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

    # Zeroconf callback methods
    def add_service(self, zc, type_, name):
        """Called when a new service is discovered"""
        info = zc.get_service_info(type_, name)
        if info and info.properties:
            try:
                peer_phone = info.properties[b'phone'].decode('utf-8')
                if peer_phone != self.user_phone:
                    peer_ip = str(ipaddress.IPv4Address(info.addresses[0]))
                    self.peers[peer_phone] = {
                        'ip': peer_ip
                    }
            except Exception as e:
                print(f"Error adding service: {e}")

    def remove_service(self, zc, type_, name):
        """Called when a service is removed"""
        try:
            peer_phone = name.replace(f".{self.service_type}", "")
            if peer_phone in self.peers:
                del self.peers[peer_phone]
        except Exception as e:
            print(f"Error removing service: {e}")

    def update_service(self, zc, type_, name):
        """Called when a service is updated"""
        self.add_service(zc, type_, name)

    def _tcp_server(self):
        """Handle incoming TCP connections"""
        while self.running:
            try:
                client_socket, addr = self.tcp_socket.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                ).start()
            except:
                if self.running:
                    time.sleep(1)

    def _process_message_queue(self):
        """Process received messages"""
        while self.running:
            try:
                message = self.message_queue.get()
                if message.get('type') == 'chat':
                    # Save and emit message
                    with current_app.app_context():
                        sender = User.query.filter_by(phone_number=message['sender']).first()
                        receiver = User.query.filter_by(phone_number=message['receiver']).first()
                        
                        if sender and receiver:
                            # Create new message
                            new_message = Message(
                                sender_id=sender.id,
                                receiver_id=receiver.id,
                                content=message['content']
                            )
                            db.session.add(new_message)
                            db.session.commit()
                            
                            # Emit new message event
                            socketio.emit('new_message', {
                                'message': {
                                    'id': new_message.id,
                                    'content': new_message.content,
                                    'timestamp': new_message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                    'sender_phone': message['sender'],
                                    'receiver_phone': message['receiver']
                                }
                            })
            except Exception as e:
                print(f"Error processing message: {e}")

    def _handle_client(self, client_socket, addr):
        """Handle incoming TCP messages"""
        try:
            data = client_socket.recv(4096)
            if data:
                message = json.loads(data.decode())
                
                if message.get('type') == 'message':
                    # Process the message
                    self.message_queue.put({
                        'type': 'chat',
                        'sender': message['sender_phone'],
                        'receiver': self.user_phone,
                        'content': message['content']
                    })
                    
                    # Send acknowledgment
                    ack = {
                        'type': 'ack',
                        'message_id': message.get('message_id')
                    }
                    client_socket.send(json.dumps(ack).encode())
        except Exception as e:
            print(f"Error handling client message: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

# Global network manager instance
network_manager = None

def init_network(user_phone):
    """Initialize the network manager for a user"""
    global network_manager
    if network_manager:
        network_manager.stop()
    network_manager = NetworkManager(user_phone)
    network_manager.start()

def get_network_manager():
    """Get the current network manager instance"""
    return network_manager 