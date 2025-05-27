import os
import time
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from base64 import b64encode, b64decode
import json

class DoubleRatchet:
    def __init__(self):
        self.dh_pair = x25519.X25519PrivateKey.generate()
        self.root_key = None
        self.send_chain_key = None
        self.recv_chain_key = None
        self.prev_sending_keys = []
        self.message_numbers = {'send': 0, 'recv': 0}
    
    def dh(self, their_public):
        return self.dh_pair.exchange(their_public)

class E2EEncryption:
    def __init__(self, user_id):
        self.user_id = user_id
        self.identity_key = ed25519.Ed25519PrivateKey.generate()
        self.signed_pre_key = x25519.X25519PrivateKey.generate()
        self.one_time_pre_keys = [x25519.X25519PrivateKey.generate() for _ in range(20)]
        self.sessions = {}
        self.performance_metrics = {
            'encryption_times': [],
            'decryption_times': [],
            'key_generation_times': []
        }
    
    def get_public_bundle(self):
        """Get public key bundle for initial key exchange"""
        start_time = time.time()
        bundle = {
            'identity_key': b64encode(self.identity_key.public_key().public_bytes()).decode(),
            'signed_pre_key': b64encode(self.signed_pre_key.public_key().public_bytes()).decode(),
            'one_time_pre_keys': [
                b64encode(key.public_key().public_bytes()).decode()
                for key in self.one_time_pre_keys
            ]
        }
        self.performance_metrics['key_generation_times'].append(time.time() - start_time)
        return bundle
    
    def initialize_session(self, their_bundle, their_id):
        """Initialize a new session with another user"""
        if their_id in self.sessions:
            return
        
        start_time = time.time()
        
        # Decode their bundle
        their_identity = ed25519.Ed25519PublicKey.from_public_bytes(
            b64decode(their_bundle['identity_key'])
        )
        their_signed_pre_key = x25519.X25519PublicKey.from_public_bytes(
            b64decode(their_bundle['signed_pre_key'])
        )
        
        # Initialize Double Ratchet
        ratchet = DoubleRatchet()
        
        # Generate initial root key
        dh_result = ratchet.dh(their_signed_pre_key)
        ratchet.root_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'E2EE-Chat-Initial-Root-Key'
        ).derive(dh_result)
        
        self.sessions[their_id] = {
            'ratchet': ratchet,
            'their_identity': their_identity
        }
        
        self.performance_metrics['key_generation_times'].append(time.time() - start_time)
    
    def encrypt_message(self, message, recipient_id):
        """Encrypt a message for a specific recipient"""
        if recipient_id not in self.sessions:
            raise ValueError("No session established with this recipient")
        
        start_time = time.time()
        
        session = self.sessions[recipient_id]
        ratchet = session['ratchet']
        
        # Generate message key
        message_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'E2EE-Chat-Message-Key'
        ).derive(ratchet.root_key + str(ratchet.message_numbers['send']).encode())
        
        # Encrypt message
        aesgcm = AESGCM(message_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, message.encode(), None)
        
        # Create encrypted message package
        encrypted_message = {
            'ciphertext': b64encode(ciphertext).decode(),
            'nonce': b64encode(nonce).decode(),
            'message_number': ratchet.message_numbers['send']
        }
        
        # Update ratchet state
        ratchet.message_numbers['send'] += 1
        
        self.performance_metrics['encryption_times'].append(time.time() - start_time)
        
        return json.dumps(encrypted_message)
    
    def decrypt_message(self, encrypted_message, sender_id):
        """Decrypt a message from a specific sender"""
        if sender_id not in self.sessions:
            raise ValueError("No session established with this sender")
        
        start_time = time.time()
        
        session = self.sessions[sender_id]
        ratchet = session['ratchet']
        
        # Parse encrypted message
        message_data = json.loads(encrypted_message)
        ciphertext = b64decode(message_data['ciphertext'])
        nonce = b64decode(message_data['nonce'])
        message_number = message_data['message_number']
        
        # Generate message key
        message_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'E2EE-Chat-Message-Key'
        ).derive(ratchet.root_key + str(message_number).encode())
        
        # Decrypt message
        aesgcm = AESGCM(message_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        self.performance_metrics['decryption_times'].append(time.time() - start_time)
        
        return plaintext.decode()
    
    def get_performance_metrics(self):
        """Get average performance metrics"""
        metrics = {
            'avg_encryption_time': sum(self.performance_metrics['encryption_times']) / len(self.performance_metrics['encryption_times'])
            if self.performance_metrics['encryption_times'] else 0,
            'avg_decryption_time': sum(self.performance_metrics['decryption_times']) / len(self.performance_metrics['decryption_times'])
            if self.performance_metrics['decryption_times'] else 0,
            'key_generation_time': sum(self.performance_metrics['key_generation_times']) / len(self.performance_metrics['key_generation_times'])
            if self.performance_metrics['key_generation_times'] else 0
        }
        return metrics 