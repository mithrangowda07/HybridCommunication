# Hybrid Communication App

A web-based local network communication application that allows users to chat and share files over a local Wi-Fi network.

## Features

- User registration and authentication
- Real-time peer discovery over local network
- Direct messaging between users
- File sharing with image previews
- Contact management
- Light/Dark mode support
- Modern responsive UI

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

4. Run the application:
```bash
python run.py
```

5. Access the application at: http://localhost:5000

## Technology Stack

- Backend: Flask
- Database: SQLite with SQLAlchemy
- Frontend: Bootstrap 5
- Real-time Communication: Flask-SocketIO
- Network: UDP (peer discovery) and TCP (messaging)

## Security Notes

- All passwords are hashed before storage
- File transfers are handled securely
- User authentication required for all operations 