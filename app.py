import os
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, session, redirect, url_for, flash, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user, UserMixin
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "presensi_tik_aceh_tamiang_secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///presensi.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize extensions
db = SQLAlchemy(app, model_class=Base)
csrf = CSRFProtect(app)
migrate = Migrate(app, db)

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silahkan login untuk mengakses halaman ini.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Create tables and initial data
with app.app_context():
    from models import User, Role
    db.create_all()
    logging.info("Database tables created")
    
    try:
        # Create default roles if they don't exist
        default_roles = ['personel', 'admin', 'super_admin']
        existing_roles = Role.query.all()
        existing_role_names = [role.name for role in existing_roles]
        
        for role_name in default_roles:
            if role_name not in existing_role_names:
                new_role = Role()
                new_role.name = role_name
                db.session.add(new_role)
        
        db.session.commit()
        logging.info("Default roles created")
        
        # Create default users if no users exist
        if not User.query.first():
            from werkzeug.security import generate_password_hash
            super_admin_role = Role.query.filter_by(name='super_admin').first()
            admin_role = Role.query.filter_by(name='admin').first()
            personel_role = Role.query.filter_by(name='personel').first()
            
            # Create super admin
            super_admin = User()
            super_admin.username = 'super_admin'
            super_admin.name = 'Super Admin'
            super_admin.email = 'super_admin@example.com'
            super_admin.password_hash = generate_password_hash('Tik123')
            super_admin.role_id = super_admin_role.id
            
            # Create admin
            admin = User()
            admin.username = 'admin'
            admin.name = 'Admin'
            admin.email = 'admin@example.com'
            admin.password_hash = generate_password_hash('Tik123')
            admin.role_id = admin_role.id
            
            # Create personel
            personel = User()
            personel.username = 'personel'
            personel.name = 'Personel'
            personel.email = 'personel@example.com'
            personel.password_hash = generate_password_hash('Tik123')
            personel.role_id = personel_role.id
            
            db.session.add(super_admin)
            db.session.add(admin)
            db.session.add(personel)
            db.session.commit()
            logging.info("Default users created")
        
        logging.info("Database setup completed successfully")
    except Exception as e:
        logging.error(f"Error during database setup: {str(e)}")
        db.session.rollback()

# Role-based access control
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            
            from models import Role
            user_role = Role.query.get(current_user.role_id)
            if user_role.name not in roles:
                flash('Anda tidak memiliki izin untuk mengakses halaman ini.', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=1)
