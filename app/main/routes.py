import os
from datetime import datetime, timedelta
from flask import render_template, flash, redirect, url_for, request, jsonify, current_app, send_from_directory
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db, socketio
from app.main import bp
from app.models import User, Contact, Message
from app.network import get_network_manager
import json
import numpy as np

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('main/index.html', title='Home', contacts=contacts)

@bp.route('/get_contact_details/<phone_number>')
@login_required
def get_contact_details(phone_number):
    contact_user = User.query.filter_by(phone_number=phone_number).first_or_404()
    
    return jsonify({
        'display_name': contact_user.display_name
    })

@bp.route('/add_contact', methods=['POST'])
@login_required
def add_contact():
    phone_number = request.form.get('phone_number')
    contact_user = User.query.filter_by(phone_number=phone_number).first()
    
    if not contact_user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    if contact_user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot add yourself as contact'})
    
    existing_contact = Contact.query.filter_by(
        user_id=current_user.id,
        contact_phone=phone_number
    ).first()
    
    if existing_contact:
        return jsonify({'success': False, 'message': 'Contact already exists'})
    
    contact = Contact(user_id=current_user.id, contact_phone=phone_number)
    db.session.add(contact)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Contact added successfully',
        'contact': {
            'id': contact.id,
            'phone_number': phone_number,
            'display_name': contact_user.display_name
        }
    })

@bp.route('/get_messages/<phone_number>')
@login_required
def get_messages(phone_number):
    contact = User.query.filter_by(phone_number=phone_number).first_or_404()
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == contact.id)) |
        ((Message.sender_id == contact.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()
    
    return jsonify([{
        'id': msg.id,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'is_sender': msg.sender_id == current_user.id,
        'is_file': msg.is_file,
        'file_name': msg.file_name if msg.is_file else None,
        'file_type': msg.file_type if msg.is_file else None
    } for msg in messages])

@bp.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    receiver_phone = request.form.get('receiver_phone')
    
    if not file or not file.filename:
        return jsonify({'success': False, 'message': 'No file selected'})
    
    receiver = User.query.filter_by(phone_number=receiver_phone).first()
    if not receiver:
        return jsonify({'success': False, 'message': 'Receiver not found'})
    
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if file_ext in current_app.config['ALLOWED_IMAGE_EXTENSIONS']:
        file_type = 'image'
    elif file_ext in current_app.config['ALLOWED_FILE_EXTENSIONS']:
        file_type = 'file'
    else:
        return jsonify({'success': False, 'message': 'File type not allowed'})
    
    # Create upload directory if it doesn't exist
    if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
        os.makedirs(current_app.config['UPLOAD_FOLDER'])
    
    # Save file
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Create message
    message = Message(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        content=filename,  # Store just the filename
        is_file=True,
        file_type=file_type,
        file_name=filename
    )
    db.session.add(message)
    db.session.commit()
    
    # Try to send file over network
    network_mgr = get_network_manager()
    if network_mgr:
        network_mgr.send_message(receiver_phone, {
            'type': 'file',
            'filename': filename,
            'file_type': file_type,
            'content': filename  # Send filename instead of content
        }, message.id)
    
    # Emit message event
    socketio.emit('new_message', {
        'message': {
            'id': message.id,
            'content': filename,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'sender_phone': current_user.phone_number,
            'receiver_phone': receiver.phone_number,
            'is_file': True,
            'file_type': file_type,
            'file_name': filename
        }
    })
    
    return jsonify({
        'success': True,
        'message': 'File uploaded successfully',
        'file_info': {
            'id': message.id,
            'filename': filename,
            'file_type': file_type
        }
    })

@bp.route('/refresh_connections', methods=['POST'])
@login_required
def refresh_connections():
    """Refresh connection status for all known peers"""
    network_manager = get_network_manager()
    if network_manager:
        network_manager.refresh_connections()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Network manager not initialized'})

@bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@socketio.on('send_message')
def handle_message(data):
    receiver = User.query.filter_by(phone_number=data['receiver_phone']).first()
    if receiver:
        # Create message
        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver.id,
            content=data['message']
        )
        db.session.add(message)
        db.session.commit()
        
        # Try to send message over network
        network_mgr = get_network_manager()
        if network_mgr:
            network_mgr.send_message(data['receiver_phone'], data['message'], message.id)
        
        # Emit message event
        socketio.emit('new_message', {
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'sender_phone': current_user.phone_number,
                'receiver_phone': receiver.phone_number
            }
        })

@bp.route('/security-analysis')
@login_required
def security_analysis():
    # Get real-time security metrics
    message_stats = get_message_statistics()
    encryption_metrics = get_encryption_metrics()
    security_score = calculate_security_score()
    
    return render_template('main/security_analysis.html', 
                         title='Security Analysis',
                         current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         message_stats=message_stats,
                         encryption_metrics=encryption_metrics,
                         security_score=security_score)

def get_encryption_metrics():
    """Calculate real encryption metrics"""
    total_messages = Message.query.filter(
        (Message.sender_id == current_user.id) | 
        (Message.receiver_id == current_user.id)
    ).count()
    
    # Get messages from last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_messages = Message.query.filter(
        ((Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)) &
        (Message.timestamp >= thirty_days_ago)
    ).all()
    
    # Calculate encryption success rate
    encrypted_count = sum(1 for msg in recent_messages if msg.is_encrypted)
    encryption_rate = (encrypted_count / len(recent_messages) * 100) if recent_messages else 100
    
    return {
        'total_messages': total_messages,
        'recent_messages': len(recent_messages),
        'encryption_rate': round(encryption_rate, 2)
    }

def calculate_security_score():
    """Calculate overall security score based on multiple factors"""
    # Get base metrics
    encryption_metrics = get_encryption_metrics()
    
    # Calculate component scores
    encryption_score = encryption_metrics['encryption_rate']
    
    # Network security score based on successful message delivery
    thirty_days_ago = datetime.now() - timedelta(days=30)
    delivered_messages = Message.query.filter(
        ((Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)) &
        (Message.timestamp >= thirty_days_ago) &
        (Message.status == 'DELIVERED')
    ).count()
    
    total_recent = Message.query.filter(
        ((Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)) &
        (Message.timestamp >= thirty_days_ago)
    ).count()
    
    network_score = (delivered_messages / total_recent * 100) if total_recent > 0 else 100
    
    # Access control score based on failed login attempts and session security
    access_score = 85  # Base score, can be adjusted based on additional metrics
    
    return {
        'encryption': round(encryption_score, 1),
        'network': round(network_score, 1),
        'access_control': round(access_score, 1),
        'overall': round((encryption_score + network_score + access_score) / 3, 1)
    }

def get_message_statistics():
    """Get detailed message statistics for the last 7 days"""
    stats = []
    today = datetime.now().date()
    
    for i in range(7):
        date = today - timedelta(days=i)
        next_date = date + timedelta(days=1)
        
        # Get messages for this day
        days_messages = Message.query.filter(
            ((Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)) &
            (Message.timestamp >= date) &
            (Message.timestamp < next_date)
        ).all()
        
        sent_count = sum(1 for msg in days_messages if msg.sender_id == current_user.id)
        delivered_count = sum(1 for msg in days_messages if msg.status == 'DELIVERED')
        
        stats.append({
            'date': date.strftime('%a'),
            'sent': sent_count,
            'delivered': delivered_count
        })
    
    # Reverse to show oldest to newest
    stats.reverse()
    
    # Calculate 30-day totals
    thirty_days_ago = today - timedelta(days=30)
    thirty_day_messages = Message.query.filter(
        ((Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)) &
        (Message.timestamp >= thirty_days_ago)
    ).all()
    
    thirty_day_stats = {
        'total_sent': sum(1 for msg in thirty_day_messages if msg.sender_id == current_user.id),
        'total_delivered': sum(1 for msg in thirty_day_messages if msg.status == 'DELIVERED'),
        'total_encrypted': sum(1 for msg in thirty_day_messages if msg.is_encrypted)
    }
    
    return {
        'weekly': stats,
        'monthly': thirty_day_stats
    } 