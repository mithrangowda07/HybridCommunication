from PyQt5.QtGui import QColor, QFont

class Theme:
    class Light:
        # Colors
        PRIMARY = "#2196F3"
        SECONDARY = "#03A9F4"
        BACKGROUND = "#FFFFFF"
        SURFACE = "#F5F5F5"
        TEXT_PRIMARY = "#000000"
        TEXT_SECONDARY = "#757575"
        BORDER = "#E0E0E0"
        SENT_MESSAGE = "#E3F2FD"
        RECEIVED_MESSAGE = "#FFFFFF"
        ONLINE = "#4CAF50"
        OFFLINE = "#F44336"
        
    class Dark:
        # Colors
        PRIMARY = "#1976D2"
        SECONDARY = "#0288D1"
        BACKGROUND = "#121212"
        SURFACE = "#1E1E1E"
        TEXT_PRIMARY = "#FFFFFF"
        TEXT_SECONDARY = "#B0B0B0"
        BORDER = "#2D2D2D"
        SENT_MESSAGE = "#064779"
        RECEIVED_MESSAGE = "#1E1E1E"
        ONLINE = "#4CAF50"
        OFFLINE = "#F44336"

    @staticmethod
    def get_theme(is_dark):
        return Theme.Dark if is_dark else Theme.Light

class Fonts:
    APP_TITLE = QFont("Segoe UI", 24, QFont.Bold)
    HEADER = QFont("Segoe UI", 16, QFont.Bold)
    SUBHEADER = QFont("Segoe UI", 14, QFont.Medium)
    BODY = QFont("Segoe UI", 11)
    SMALL = QFont("Segoe UI", 9)
    MESSAGE = QFont("Segoe UI", 12)
    TIMESTAMP = QFont("Segoe UI", 8)

class StyleSheet:
    @staticmethod
    def get_main_style(theme):
        return f"""
        QMainWindow {{
            background-color: {theme.BACKGROUND};
        }}
        
        QWidget {{
            background-color: {theme.BACKGROUND};
            color: {theme.TEXT_PRIMARY};
        }}
        
        QPushButton {{
            background-color: {theme.PRIMARY};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }}
        
        QPushButton:hover {{
            background-color: {theme.SECONDARY};
        }}
        
        QPushButton:pressed {{
            background-color: {theme.PRIMARY};
        }}
        
        QLineEdit {{
            padding: 8px;
            border: 1px solid {theme.BORDER};
            border-radius: 4px;
            background-color: {theme.SURFACE};
            color: {theme.TEXT_PRIMARY};
        }}
        
        QTextEdit {{
            border: 1px solid {theme.BORDER};
            border-radius: 4px;
            background-color: {theme.SURFACE};
            color: {theme.TEXT_PRIMARY};
        }}
        
        QListWidget {{
            border: 1px solid {theme.BORDER};
            border-radius: 4px;
            background-color: {theme.SURFACE};
            color: {theme.TEXT_PRIMARY};
        }}
        
        QLabel {{
            color: {theme.TEXT_PRIMARY};
        }}
        """

class MessageBubble:
    @staticmethod
    def get_sent_style(theme):
        return f"""
        background-color: {theme.SENT_MESSAGE};
        border-radius: 12px;
        padding: 8px 12px;
        margin: 2px 8px;
        """

    @staticmethod
    def get_received_style(theme):
        return f"""
        background-color: {theme.RECEIVED_MESSAGE};
        border-radius: 12px;
        padding: 8px 12px;
        margin: 2px 8px;
        border: 1px solid {theme.BORDER};
        """ 