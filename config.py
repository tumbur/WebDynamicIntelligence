import os

# Flask configuration
class Config:
    # Debug mode
    DEBUG = True
    
    # Secret key for session
    SECRET_KEY = os.environ.get("SESSION_SECRET", "presensi_tik_aceh_tamiang_secret")
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///presensi.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        "pool_recycle": 300,
    }
    
    # Attendance settings
    REGULAR_SHIFT_START = "08:00"
    REGULAR_SHIFT_END = "16:00"
    DAILY_SHIFT_HOURS = 24
    LATE_THRESHOLD_MINUTES = 15
    
    # Presensi types
    ATTENDANCE_STATUS_OPTIONS = [
        ('present', 'Hadir'),
        ('late', 'Terlambat'),
        ('absent', 'Tidak Hadir'),
        ('sick', 'Sakit'),
        ('permission', 'Izin')
    ]
    
    # Shift types
    SHIFT_TYPE_OPTIONS = [
        ('daily', 'Piket Harian (24 Jam)'),
        ('regular', 'Piket Reguler (8 Jam)')
    ]
