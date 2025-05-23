from datetime import datetime
from flask_login import UserMixin
from app import db
from sqlalchemy import Enum, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

# User and Role models
class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    users = relationship('User', backref='role')
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(15))
    role_id = db.Column(db.Integer, ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    @property
    def active(self):
        return self.is_active
    
    def __repr__(self):
        return f'<User {self.username}>'

# DutySchedule model
class DutySchedule(db.Model):
    __tablename__ = 'duty_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    shift_type = db.Column(Enum('daily', 'regular', name='shift_type_enum'), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = relationship('User', foreign_keys=[user_id], backref='duty_schedules')
    creator = relationship('User', foreign_keys=[created_by], backref='created_duties')
    
    __table_args__ = (
        CheckConstraint('date IS NOT NULL', name='date_not_null'),
    )
    
    def __repr__(self):
        return f'<DutySchedule {self.date} - {self.shift_type}>'

# Attendance model
class Attendance(db.Model):
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    duty_schedule_id = db.Column(db.Integer, ForeignKey('duty_schedules.id'))
    attendance_type = db.Column(Enum('daily', 'regular', name='attendance_type_enum'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in_time = db.Column(db.DateTime)
    check_out_time = db.Column(db.DateTime)
    status = db.Column(Enum('present', 'late', 'absent', 'sick', 'permission', name='attendance_status_enum'), default='absent')
    notes = db.Column(db.Text)
    location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = relationship('User', backref='attendances')
    duty_schedule = relationship('DutySchedule', backref='attendances')
    
    __table_args__ = (
        CheckConstraint('date IS NOT NULL', name='attendance_date_not_null'),
    )
    
    def __repr__(self):
        return f'<Attendance {self.date} - {self.status}>'

# Notification model
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    type = db.Column(Enum('info', 'warning', 'success', 'danger', name='notification_type_enum'), default='info')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}>'
