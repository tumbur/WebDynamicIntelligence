from flask import session, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from functools import wraps

from app import app
from models import User, Role

def role_required(roles_list):
    """
    Decorator to check if the current user has the required role(s).
    Takes a list of role names as argument.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Silahkan login terlebih dahulu.', 'warning')
                session['next'] = request.url
                return redirect(url_for('login'))
            
            role = Role.query.get(current_user.role_id)
            if role.name not in roles_list:
                flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def authenticate_user(username, password):
    """
    Authenticate a user with username and password.
    Returns the user object if authentication is successful, None otherwise.
    """
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return None
    
    if not user.is_active:
        return None
    
    return user
