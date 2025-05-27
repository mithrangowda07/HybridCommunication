import sys
import os
import mimetypes
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QLineEdit, QPushButton,
                            QStackedWidget, QListWidget, QTextEdit, QFileDialog,
                            QMessageBox, QInputDialog, QScrollArea, QFrame,
                            QToolBar, QAction)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon
from database import Database
from network import NetworkManager
from styles import Theme, Fonts, StyleSheet
from widgets import ContactItem, MessageWidget, ChatHeader
import time


class LoginWindow(QWidget):
    def __init__(self, on_login, on_switch_to_register):
        super().__init__()
        self.on_login = on_login
        self.db = Database()
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)

        # Title
        title = QLabel("Hybrid Communication App")
        title.setFont(Fonts.APP_TITLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Connect Locally, Chat Globally")
        subtitle.setFont(Fonts.SUBHEADER)
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Login form
        form = QFrame()
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # Phone number
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        self.phone_input.setFixedHeight(40)
        form_layout.addWidget(self.phone_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(40)
        form_layout.addWidget(self.password_input)

        # Login button
        login_btn = QPushButton("Login")
        login_btn.setFixedHeight(40)
        login_btn.setFont(Fonts.BODY)
        login_btn.clicked.connect(self.handle_login)
        form_layout.addWidget(login_btn)

        form.setLayout(form_layout)
        layout.addWidget(form)

        # Register link
        register_btn = QPushButton("Don't have an account? Register")
        register_btn.setFlat(True)
        register_btn.clicked.connect(on_switch_to_register)
        layout.addWidget(register_btn, alignment=Qt.AlignCenter)

        layout.addStretch()
        self.setLayout(layout)

    def handle_login(self):
        phone = self.phone_input.text()
        password = self.password_input.text()

        if not all([phone, password]):
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return

        if self.db.login_user(phone, password):
            self.on_login(phone)
        else:
            QMessageBox.warning(self, "Error", "Invalid phone number or password")

class RegisterWindow(QWidget):
    def __init__(self, on_switch_to_login):
        super().__init__()
        self.db = Database()
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)

        # Title
        title = QLabel("Create Account")
        title.setFont(Fonts.APP_TITLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Registration form
        form = QFrame()
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # Phone number
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        self.phone_input.setFixedHeight(40)
        form_layout.addWidget(self.phone_input)

        # Display name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Display Name")
        self.name_input.setFixedHeight(40)
        form_layout.addWidget(self.name_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(40)
        form_layout.addWidget(self.password_input)

        # Register button
        register_btn = QPushButton("Create Account")
        register_btn.setFixedHeight(40)
        register_btn.setFont(Fonts.BODY)
        register_btn.clicked.connect(self.handle_register)
        form_layout.addWidget(register_btn)

        form.setLayout(form_layout)
        layout.addWidget(form)

        # Login link
        login_btn = QPushButton("Already have an account? Login")
        login_btn.setFlat(True)
        login_btn.clicked.connect(on_switch_to_login)
        layout.addWidget(login_btn, alignment=Qt.AlignCenter)

        layout.addStretch()
        self.setLayout(layout)

    def handle_register(self):
        phone = self.phone_input.text()
        name = self.name_input.text()
        password = self.password_input.text()

        if not all([phone, name, password]):
            QMessageBox.warning(self, "Error", "All fields are required")
            return

        if self.db.register_user(phone, name, password):
            QMessageBox.information(self, "Success", "Registration successful!")
            self.phone_input.clear()
            self.name_input.clear()
            self.password_input.clear()
        else:
            QMessageBox.warning(self, "Error", "Phone number already registered")

class ChatWindow(QWidget):
    def __init__(self, phone_number):
        super().__init__()
        self.phone_number = phone_number
        self.db = Database()
        self.network = NetworkManager()
        self.current_chat = None
        
        self.init_ui()
        self.setup_network()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Left panel (contacts)
        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_panel.setStyleSheet("""
            QWidget {
                background-color: white;
                border-right: 1px solid #E0E0E0;
            }
        """)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Header with user info
        header = QWidget()
        header.setStyleSheet("background-color: #F5F5F5; padding: 10px;")
        header_layout = QHBoxLayout()
        
        user_info = QLabel(f"Your phone: {self.phone_number}")
        user_info.setFont(Fonts.BODY)
        header_layout.addWidget(user_info)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(30, 30)
        refresh_btn.clicked.connect(self.refresh_contacts)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
                border-radius: 15px;
            }
        """)
        header_layout.addWidget(refresh_btn)
        
        header.setLayout(header_layout)
        left_layout.addWidget(header)
        
        # Add contact button
        add_contact_btn = QPushButton("Add Contact")
        add_contact_btn.setFixedHeight(40)
        add_contact_btn.clicked.connect(self.add_contact)
        add_contact_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                margin: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        left_layout.addWidget(add_contact_btn)
        
        # Contacts list
        self.contacts_list = QListWidget()
        self.contacts_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: white;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
            }
        """)
        self.contacts_list.itemClicked.connect(self.on_contact_selected)
        left_layout.addWidget(self.contacts_list)
        
        left_panel.setLayout(left_layout)
        layout.addWidget(left_panel)
        
        # Right panel (chat)
        chat_panel = QWidget()
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Chat header
        self.chat_header = QWidget()
        self.chat_header.setVisible(False)
        chat_layout.addWidget(self.chat_header)
        
        # Messages area
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messages_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F5F5F5;
            }
        """)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.addStretch()
        self.messages_container.setLayout(self.messages_layout)
        
        self.messages_scroll.setWidget(self.messages_container)
        chat_layout.addWidget(self.messages_scroll)
        
        # Input area
        input_widget = QWidget()
        input_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-top: 1px solid #E0E0E0;
            }
        """)
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setFixedHeight(36)
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E0E0E0;
                border-radius: 18px;
                padding: 0 15px;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        send_btn = QPushButton("Send")
        send_btn.setFixedSize(70, 36)
        send_btn.clicked.connect(self.send_message)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 18px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        input_layout.addWidget(send_btn)
        
        file_btn = QPushButton("📎")
        file_btn.setFixedSize(36, 36)
        file_btn.clicked.connect(self.send_file)
        file_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 18px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)
        input_layout.addWidget(file_btn)
        
        input_widget.setLayout(input_layout)
        chat_layout.addWidget(input_widget)
        
        chat_panel.setLayout(chat_layout)
        layout.addWidget(chat_panel)
        
        self.setLayout(layout)
        self.load_contacts()

    def setup_network(self):
        self.network.message_received.connect(self.handle_message_received)
        self.network.peer_discovered.connect(self.handle_peer_discovered)
        self.network.peer_status_changed.connect(self.handle_peer_status_changed)
        self.network.start_services(self.phone_number)

    def load_contacts(self):
        self.contacts_list.clear()
        contacts = self.db.get_contacts(self.phone_number)
        for contact in contacts:
            phone, name, last_seen = contact
            item = ContactItem(phone, name, self.network.is_peer_online(phone))
            self.contacts_list.addItem(item)
            self.contacts_list.setItemWidget(item, item.widget)

    def refresh_contacts(self):
        # Stop current network services
        self.network.stop_services()
        
        # Clear current online status
        for i in range(self.contacts_list.count()):
            item = self.contacts_list.item(i)
            if isinstance(item, ContactItem):
                item.set_online_status(False)
        
        # Restart network services
        QTimer.singleShot(1000, lambda: self.network.start_services(self.phone_number))
        
        # Reload contacts after a short delay to allow network discovery
        QTimer.singleShot(2000, self.load_contacts)
        
        # Update current chat header if exists
        if self.current_chat:
            QTimer.singleShot(2000, self.update_chat_header)

    def add_contact(self):
        phone = QInputDialog.getText(self, "Add Contact", "Enter phone number:")[0]
        if phone and phone != self.phone_number:
            display_name = self.db.get_user_display_name(phone)
            if display_name:
                if self.db.add_contact(self.phone_number, phone):
                    self.load_contacts()
                else:
                    QMessageBox.warning(self, "Error", "Contact already exists")
            else:
                QMessageBox.warning(self, "Error", "User not found")

    def handle_message_received(self, sender_phone, message, timestamp):
        if sender_phone == self.current_chat:
            self.add_message(message, timestamp, False)
        self.db.save_message(sender_phone, self.phone_number, message)

    def handle_peer_discovered(self, peer_phone):
        self.refresh_contacts()

    def handle_peer_status_changed(self, peer_phone, is_online):
        # Update contact list
        for i in range(self.contacts_list.count()):
            item = self.contacts_list.item(i)
            if isinstance(item, ContactItem) and item.phone == peer_phone:
                item.set_online_status(is_online)
                break
        
        # Update chat header if this is the current chat
        if peer_phone == self.current_chat:
            self.update_chat_header()

    def on_contact_selected(self, item):
        if isinstance(item, ContactItem):
            self.current_chat = item.phone
            self.clear_messages()
            self.update_chat_header(item.display_name)
            self.load_chat_history()

    def update_chat_header(self, display_name=None):
        if not display_name and self.current_chat:
            display_name = self.db.get_user_display_name(self.current_chat)
        
        if display_name and self.current_chat:
            is_online = self.network.is_peer_online(self.current_chat)
            
            # Remove old header if exists
            if self.chat_header and self.chat_header.parent():
                try:
                    chat_layout = self.layout().itemAt(1).layout()
                    if chat_layout and chat_layout.count() > 0:
                        old_header = chat_layout.takeAt(0)
                        if old_header and old_header.widget():
                            old_header.widget().deleteLater()
                except Exception:
                    pass  # Ignore any errors during header removal
            
            # Create and add new header
            self.chat_header = ChatHeader(display_name, is_online)
            self.chat_header.setVisible(True)
            
            # Add new header safely
            try:
                chat_layout = self.layout().itemAt(1).layout()
                if chat_layout:
                    chat_layout.insertWidget(0, self.chat_header)
            except Exception:
                print("Warning: Could not add chat header")

    def clear_messages(self):
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def load_chat_history(self):
        messages = self.db.get_chat_history(self.phone_number, self.current_chat)
        for msg in messages:
            sender = msg[1]
            message = msg[3]
            timestamp = msg[6]
            file_path = msg[4]
            file_type = msg[5]
            
            is_sent = sender == self.phone_number
            if file_path:
                self.add_file_message(file_path, timestamp, is_sent, file_type)
            else:
                self.add_message(message, timestamp, is_sent)

    def add_message(self, message, timestamp, is_sent):
        widget = MessageWidget(message, timestamp, is_sent)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, widget)
        self.scroll_to_bottom()

    def add_file_message(self, file_path, timestamp, is_sent, file_type):
        widget = MessageWidget(file_path, timestamp, is_sent, True, file_type)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, widget)
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        QTimer.singleShot(0, lambda: self.messages_scroll.verticalScrollBar().setValue(
            self.messages_scroll.verticalScrollBar().maximum()))

    def send_message(self):
        if not self.current_chat:
            return
            
        message = self.message_input.text()
        if not message:
            return
            
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if self.network.send_message(self.current_chat, message):
            self.add_message(message, timestamp, True)
            self.db.save_message(self.phone_number, self.current_chat, message)
            self.message_input.clear()
        else:
            QMessageBox.warning(self, "Error", 
                              "User is not currently on the same network.\nSwitch to internet to message.")

    def send_file(self):
        if not self.current_chat:
            return
            
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            file_name = os.path.basename(file_path)
            file_type = mimetypes.guess_type(file_path)[0]
            
            if self.network.send_message(self.current_chat, file_path):
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                self.add_file_message(file_path, timestamp, True, file_type)
                self.db.save_message(
                    self.phone_number, self.current_chat, file_path, 
                    file_path, file_name, file_type
                )
            else:
                QMessageBox.warning(self, "Error", 
                                  "User is not currently on the same network.\nSwitch to internet to send files.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hybrid Communication App")
        self.setMinimumSize(1000, 600)
        
        # Menu bar
        self.create_menu_bar()
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.login_window = LoginWindow(self.on_login, self.show_register)
        self.register_window = RegisterWindow(self.show_login)
        
        self.stacked_widget.addWidget(self.login_window)
        self.stacked_widget.addWidget(self.register_window)

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # Account menu
        account_menu = menubar.addMenu('Account')
        
        logout_action = QAction('Logout', self)
        logout_action.triggered.connect(self.logout)
        account_menu.addAction(logout_action)
        
        delete_account_action = QAction('Delete Account', self)
        delete_account_action.triggered.connect(self.delete_account)
        account_menu.addAction(delete_account_action)

    def show_login(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_register(self):
        self.stacked_widget.setCurrentIndex(1)

    def on_login(self, phone_number):
        self.current_user = phone_number
        self.chat_window = ChatWindow(phone_number)
        self.stacked_widget.addWidget(self.chat_window)
        self.stacked_widget.setCurrentWidget(self.chat_window)

    def logout(self):
        if hasattr(self, 'chat_window'):
            self.chat_window.network.stop_services()
            self.stacked_widget.removeWidget(self.chat_window)
            delattr(self, 'chat_window')
        self.show_login()

    def delete_account(self):
        if hasattr(self, 'current_user'):
            reply = QMessageBox.question(
                self, 'Delete Account',
                'Are you sure you want to delete your account? This cannot be undone.',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.db.delete_account(self.current_user)
                self.logout()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 