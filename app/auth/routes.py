from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from app import db
from app.auth import bp
from app.models import User
from app.auth.forms import LoginForm, RegistrationForm
from app.network import init_network, get_network_manager

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(phone_number=form.phone_number.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid phone number or password', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        
        # Initialize network manager for the user
        init_network(user.phone_number)
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(phone_number=form.phone_number.data, display_name=form.display_name.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now registered!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/logout')
def logout():
    # Stop network manager
    network_mgr = get_network_manager()
    if network_mgr:
        network_mgr.stop()
    
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/delete_account')
def delete_account():
    if current_user.is_authenticated:
        # Stop network manager
        network_mgr = get_network_manager()
        if network_mgr:
            network_mgr.stop()
        
        user = current_user
        logout_user()
        db.session.delete(user)
        db.session.commit()
        flash('Your account has been deleted.', 'info')
    return redirect(url_for('auth.login')) 