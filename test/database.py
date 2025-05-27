import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.db_file = "chat_app.db"
        self.init_database()

    def init_database(self):
        """Initialize database and handle schema migrations."""
        new_db = not os.path.exists(self.db_file)
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        if new_db:
            self.create_tables(cursor)
        else:
            # Check and add missing columns
            try:
                # Check users table
                cursor.execute("PRAGMA table_info(users)")
                columns = {col[1] for col in cursor.fetchall()}
                
                if "theme_preference" not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN theme_preference TEXT DEFAULT 'light'")
                if "is_deleted" not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT 0")

                # Create contacts table if it doesn't exist
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    user_phone TEXT,
                    contact_phone TEXT,
                    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_phone, contact_phone),
                    FOREIGN KEY (user_phone) REFERENCES users (phone_number),
                    FOREIGN KEY (contact_phone) REFERENCES users (phone_number)
                )
                ''')

                # Check messages table
                cursor.execute("PRAGMA table_info(messages)")
                msg_columns = {col[1] for col in cursor.fetchall()}

                if "file_type" not in msg_columns:
                    cursor.execute("ALTER TABLE messages ADD COLUMN file_type TEXT")
                if "is_read" not in msg_columns:
                    cursor.execute("ALTER TABLE messages ADD COLUMN is_read BOOLEAN DEFAULT 0")

                conn.commit()
            except sqlite3.Error as e:
                print(f"Migration error: {e}")
                conn.rollback()

        conn.close()

    def create_tables(self, cursor):
        """Create all tables for a new database."""
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            phone_number TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            password TEXT NOT NULL,
            last_seen TIMESTAMP,
            theme_preference TEXT DEFAULT 'light',
            is_deleted BOOLEAN DEFAULT 0
        )
        ''')

        # Contacts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            user_phone TEXT,
            contact_phone TEXT,
            added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_phone, contact_phone),
            FOREIGN KEY (user_phone) REFERENCES users (phone_number),
            FOREIGN KEY (contact_phone) REFERENCES users (phone_number)
        )
        ''')

        # Messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_phone TEXT NOT NULL,
            receiver_phone TEXT NOT NULL,
            message_text TEXT,
            file_path TEXT,
            file_name TEXT,
            file_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            FOREIGN KEY (sender_phone) REFERENCES users (phone_number),
            FOREIGN KEY (receiver_phone) REFERENCES users (phone_number)
        )
        ''')

    def register_user(self, phone_number, display_name, password):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (phone_number, display_name, password) VALUES (?, ?, ?)",
                (phone_number, display_name, password)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def login_user(self, phone_number, password):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE phone_number = ? AND password = ? AND is_deleted = 0",
            (phone_number, password)
        )
        user = cursor.fetchone()
        if user:
            cursor.execute(
                "UPDATE users SET last_seen = ? WHERE phone_number = ?",
                (datetime.now(), phone_number)
            )
            conn.commit()
        conn.close()
        return user is not None

    def delete_account(self, phone_number):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_deleted = 1 WHERE phone_number = ?",
            (phone_number,)
        )
        conn.commit()
        conn.close()

    def add_contact(self, user_phone, contact_phone):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO contacts (user_phone, contact_phone) VALUES (?, ?)",
                (user_phone, contact_phone)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_contacts(self, user_phone):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.phone_number, u.display_name, u.last_seen 
            FROM users u 
            JOIN contacts c ON u.phone_number = c.contact_phone 
            WHERE c.user_phone = ? AND u.is_deleted = 0
            ORDER BY u.display_name
        """, (user_phone,))
        contacts = cursor.fetchall()
        conn.close()
        return contacts

    def get_user_display_name(self, phone_number):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT display_name FROM users WHERE phone_number = ? AND is_deleted = 0",
            (phone_number,)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def save_message(self, sender_phone, receiver_phone, message_text, file_path=None, file_name=None, file_type=None):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO messages 
            (sender_phone, receiver_phone, message_text, file_path, file_name, file_type) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            (sender_phone, receiver_phone, message_text, file_path, file_name, file_type)
        )
        conn.commit()
        conn.close()

    def get_chat_history(self, user1_phone, user2_phone):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM messages 
            WHERE (sender_phone = ? AND receiver_phone = ?) 
            OR (sender_phone = ? AND receiver_phone = ?)
            ORDER BY timestamp""",
            (user1_phone, user2_phone, user2_phone, user1_phone)
        )
        messages = cursor.fetchall()
        conn.close()
        return messages

    def update_theme_preference(self, phone_number, theme):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET theme_preference = ? WHERE phone_number = ?",
            (theme, phone_number)
        )
        conn.commit()
        conn.close()

    def get_theme_preference(self, phone_number):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT theme_preference FROM users WHERE phone_number = ?",
            (phone_number,)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 'light'

    def mark_messages_as_read(self, sender_phone, receiver_phone):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE messages SET is_read = 1 
            WHERE sender_phone = ? AND receiver_phone = ?""",
            (sender_phone, receiver_phone)
        )
        conn.commit()
        conn.close() 