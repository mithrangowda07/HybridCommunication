from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                            QPushButton, QFrame, QSizePolicy, QListWidgetItem)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap
import os
from styles import MessageBubble, Fonts

class ContactItemWidget(QWidget):
    def __init__(self, phone, display_name, is_online=False, parent=None):
        super().__init__(parent)
        self.phone = phone
        self.display_name = display_name
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)
        
        # Header with name and status
        header = QHBoxLayout()
        name_label = QLabel(display_name)
        name_label.setFont(Fonts.BODY)
        header.addWidget(name_label)
        
        self.status_label = QLabel("🟢" if is_online else "🔴")
        header.addWidget(self.status_label, alignment=Qt.AlignRight)
        layout.addLayout(header)
        
        # Phone number
        phone_label = QLabel(phone)
        phone_label.setFont(Fonts.SMALL)
        layout.addWidget(phone_label)
        
        self.setLayout(layout)

    def set_online_status(self, is_online):
        self.status_label.setText("🟢" if is_online else "🔴")

class ContactItem(QListWidgetItem):
    def __init__(self, phone, display_name, is_online=False):
        super().__init__()
        self.phone = phone
        self.display_name = display_name
        self.widget = ContactItemWidget(phone, display_name, is_online)
        self.setSizeHint(self.widget.sizeHint())

    def set_online_status(self, is_online):
        self.widget.set_online_status(is_online)

class MessageWidget(QWidget):
    def __init__(self, message, timestamp, is_sent, has_file=False, file_type=None, parent=None):
        super().__init__(parent)
        self.message = message
        self.timestamp = timestamp
        self.is_sent = is_sent
        self.has_file = has_file
        self.file_type = file_type
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Message bubble
        self.bubble = QFrame()
        bubble_layout = QVBoxLayout()
        bubble_layout.setContentsMargins(8, 8, 8, 8)
        
        if has_file:
            if file_type and file_type.startswith('image/'):
                try:
                    # Image preview
                    img_label = QLabel()
                    pixmap = QPixmap(message)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        img_label.setPixmap(scaled_pixmap)
                        bubble_layout.addWidget(img_label)
                    else:
                        # If image can't be loaded, show file name
                        file_name = os.path.basename(message)
                        file_label = QLabel(f"📷 {file_name}")
                        bubble_layout.addWidget(file_label)
                except Exception:
                    # Fallback to file name if image loading fails
                    file_name = os.path.basename(message)
                    file_label = QLabel(f"📷 {file_name}")
                    bubble_layout.addWidget(file_label)
            else:
                # File attachment
                file_widget = QWidget()
                file_layout = QHBoxLayout()
                file_layout.setContentsMargins(0, 0, 0, 0)
                
                file_name = os.path.basename(message)
                file_label = QLabel(f"📎 {file_name}")
                file_layout.addWidget(file_label)
                
                download_btn = QPushButton("Download")
                download_btn.setFixedSize(80, 25)
                file_layout.addWidget(download_btn)
                
                file_widget.setLayout(file_layout)
                bubble_layout.addWidget(file_widget)
        else:
            # Text message
            message_label = QLabel(message)
            message_label.setFont(Fonts.MESSAGE)
            message_label.setWordWrap(True)
            bubble_layout.addWidget(message_label)
        
        # Timestamp
        time_label = QLabel(timestamp)
        time_label.setFont(Fonts.TIMESTAMP)
        time_label.setAlignment(Qt.AlignRight)
        time_label.setStyleSheet("color: #666666;")
        bubble_layout.addWidget(time_label)
        
        self.bubble.setLayout(bubble_layout)
        layout.addWidget(self.bubble)
        
        # Set alignment based on message type
        layout.setAlignment(Qt.AlignRight if is_sent else Qt.AlignLeft)
        self.setLayout(layout)
        
        # Apply style
        self.bubble.setStyleSheet("""
            QFrame {
                background-color: #E3F2FD;
                border-radius: 12px;
                padding: 8px;
                margin: 2px 8px;
            }
        """ if is_sent else """
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                padding: 8px;
                margin: 2px 8px;
                border: 1px solid #E0E0E0;
            }
        """)

class ChatHeader(QWidget):
    def __init__(self, display_name, is_online, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 8, 16, 8)
        
        # Contact info
        info_layout = QHBoxLayout()
        
        name_label = QLabel(display_name)
        name_label.setFont(Fonts.SUBHEADER)
        info_layout.addWidget(name_label)
        
        self.status_label = QLabel("🟢" if is_online else "🔴")
        self.status_label.setFont(Fonts.BODY)
        info_layout.addWidget(self.status_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setFixedHeight(50)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-bottom: 1px solid #E0E0E0;
            }
        """)
        
    def set_online_status(self, is_online):
        self.status_label.setText("🟢" if is_online else "🔴") 