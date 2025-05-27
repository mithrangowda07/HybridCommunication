from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    display_name = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    contacts = db.relationship('Contact', foreign_keys='Contact.user_id', backref='user', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    added_on = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'contact_phone', name='unique_contact'),)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_file = db.Column(db.Boolean, default=False)
    file_type = db.Column(db.String(50))
    file_name = db.Column(db.String(255))
    status = db.Column(db.String(20), default='DELIVERED')  # Message delivery status
    is_encrypted = db.Column(db.Boolean, default=True)  # Whether the message is encrypted
    # Encryption fields
    encrypted_content = db.Column(db.Text)
    message_number = db.Column(db.Integer)
    encryption_metadata = db.Column(db.Text)  # For storing nonce and other encryption data

    def encrypt_content(self, encryption_manager, recipient_id):
        """Encrypt the message content"""
        if not self.encrypted_content:
            encrypted_data = encryption_manager.encrypt_message(self.content, recipient_id)
            self.encrypted_content = encrypted_data
            self.content = None  # Clear plaintext content
            self.is_encrypted = True

    def decrypt_content(self, encryption_manager, sender_id):
        """Decrypt the message content"""
        if self.encrypted_content and not self.content:
            self.content = encryption_manager.decrypt_message(self.encrypted_content, sender_id)
            return self.content
        return None 