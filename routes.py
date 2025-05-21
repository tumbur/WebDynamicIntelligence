import os
import csv
import io
from datetime import datetime, date, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, send_file, make_response, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import extract, func, and_, or_

from app import app, db, role_required
from models import User, Role, DutySchedule, Attendance, Notification
from utils import generate_report_pdf, get_dashboard_stats, create_notification

# Login route
@app.route('/')
def public_dashboard():
    today = date.today()
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        next_month = 1
        next_year = today.year + 1
    else:
        next_month = today.month + 1
        next_year = today.year
    month_end = date(next_year, next_month, 1) - timedelta(days=1)

    # Get schedules for current month
    schedules = DutySchedule.query.filter(
        DutySchedule.date.between(month_start, month_end)
    ).join(User, DutySchedule.user_id == User.id).order_by(DutySchedule.date).all()

    return render_template('public_dashboard.html', schedules=schedules)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username dan password harus diisi', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Username tidak ditemukan', 'danger')
            return redirect(url_for('login'))
        
        if not check_password_hash(user.password_hash, password):
            flash('Password salah', 'danger')
            return redirect(url_for('login'))
        
        if not user.is_active:
            flash('Akun anda dinonaktifkan, silahkan hubungi admin', 'warning')
            return redirect(url_for('login'))
        
        login_user(user)
        flash(f'Selamat datang, {user.name}!', 'success')
        
        # Get user role
        user_role = Role.query.get(user.role_id)
        
        # Redirect based on role
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah berhasil logout', 'info')
    return redirect(url_for('login'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    user_role = Role.query.get(current_user.role_id).name
    
    stats = get_dashboard_stats(current_user)
    today = date.today()
    
    # Get user's schedule for today
    today_schedule = DutySchedule.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    # Get today's attendance
    today_attendance = Attendance.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    # Get notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Render template based on role
    if user_role == 'super_admin':
        return render_template('dashboard_super_admin.html', 
                               stats=stats, 
                               today_schedule=today_schedule,
                               today_attendance=today_attendance,
                               notifications=notifications)
    
    elif user_role == 'admin':
        return render_template('dashboard_admin.html', 
                               stats=stats, 
                               today_schedule=today_schedule,
                               today_attendance=today_attendance,
                               notifications=notifications)
    
    else:  # personel
        return render_template('dashboard_personel.html', 
                               stats=stats, 
                               today_schedule=today_schedule,
                               today_attendance=today_attendance,
                               notifications=notifications)

# Profile route
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if name:
            current_user.name = name
        
        if email and email != current_user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Email sudah digunakan', 'danger')
                return redirect(url_for('profile'))
            current_user.email = email
        
        if phone:
            current_user.phone = phone
        
        if current_password and new_password:
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Password lama salah', 'danger')
                return redirect(url_for('profile'))
            
            if new_password != confirm_password:
                flash('Password baru dan konfirmasi tidak cocok', 'danger')
                return redirect(url_for('profile'))
            
            current_user.password_hash = generate_password_hash(new_password)
        
        db.session.commit()
        flash('Profil berhasil diperbarui', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

# Schedule routes
@app.route('/jadwal')
@login_required
def schedule():
    user_role = Role.query.get(current_user.role_id).name
    today = date.today()
    
    # Get all personel for admin/super_admin
    if user_role in ['admin', 'super_admin']:
        personel_list = User.query.join(Role).filter(Role.name == 'personel').all()
    else:
        personel_list = None
    
    # Get current month schedules
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        next_month = 1
        next_year = today.year + 1
    else:
        next_month = today.month + 1
        next_year = today.year
    month_end = date(next_year, next_month, 1) - timedelta(days=1)
    
    if user_role in ['admin', 'super_admin']:
        schedules = DutySchedule.query.filter(
            DutySchedule.date.between(month_start, month_end)
        ).join(User, DutySchedule.user_id == User.id).all()
    else:
        schedules = DutySchedule.query.filter(
            DutySchedule.date.between(month_start, month_end),
            DutySchedule.user_id == current_user.id
        ).all()
    
    return render_template('schedule.html', 
                           schedules=schedules,
                           personel_list=personel_list)

@app.route('/jadwal/tambah', methods=['POST'])
@login_required
@role_required(['admin', 'super_admin'])
def add_schedule():
    user_id = request.form.get('user_id')
    shift_type = request.form.get('shift_type')
    date_str = request.form.get('date')
    notes = request.form.get('notes')
    
    if not user_id or not shift_type or not date_str:
        flash('Data jadwal tidak lengkap', 'danger')
        return redirect(url_for('schedule'))
    
    try:
        schedule_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Set standard times based on shift type
        if shift_type == 'daily':  # 24-hour shift
            start_time = datetime.strptime('08:00', '%H:%M').time()
            end_time = datetime.strptime('08:00', '%H:%M').time()
        else:  # regular shift
            start_time = datetime.strptime('08:00', '%H:%M').time()
            end_time = datetime.strptime('16:00', '%H:%M').time()
        
        # Check if schedule already exists
        existing_schedule = DutySchedule.query.filter_by(
            user_id=user_id,
            date=schedule_date
        ).first()
        
        if existing_schedule:
            flash('Jadwal untuk tanggal ini sudah ada', 'warning')
            return redirect(url_for('schedule'))
        
        # Create new schedule
        new_schedule = DutySchedule(
            user_id=user_id,
            shift_type=shift_type,
            date=schedule_date,
            start_time=start_time,
            end_time=end_time,
            notes=notes,
            created_by=current_user.id
        )
        
        db.session.add(new_schedule)
        db.session.commit()
        
        # Create notification for the user
        user = User.query.get(user_id)
        create_notification(
            user_id=user_id,
            title="Jadwal Baru",
            message=f"Anda mendapatkan jadwal {shift_type} pada tanggal {schedule_date.strftime('%d-%m-%Y')}",
            type="info"
        )
        
        flash(f'Jadwal untuk {user.name} berhasil ditambahkan', 'success')
        return redirect(url_for('schedule'))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('schedule'))

@app.route('/jadwal/edit/<int:schedule_id>', methods=['POST'])
@login_required
@role_required(['admin', 'super_admin'])
def edit_schedule(schedule_id):
    schedule = DutySchedule.query.get_or_404(schedule_id)
    
    shift_type = request.form.get('shift_type')
    notes = request.form.get('notes')
    
    if shift_type:
        schedule.shift_type = shift_type
        
        # Update times based on shift type
        if shift_type == 'daily':  # 24-hour shift
            schedule.start_time = datetime.strptime('08:00', '%H:%M').time()
            schedule.end_time = datetime.strptime('08:00', '%H:%M').time()
        else:  # regular shift
            schedule.start_time = datetime.strptime('08:00', '%H:%M').time()
            schedule.end_time = datetime.strptime('16:00', '%H:%M').time()
    
    schedule.notes = notes
    db.session.commit()
    
    # Create notification for the user
    create_notification(
        user_id=schedule.user_id,
        title="Jadwal Diperbarui",
        message=f"Jadwal anda pada tanggal {schedule.date.strftime('%d-%m-%Y')} telah diperbarui",
        type="info"
    )
    
    flash('Jadwal berhasil diperbarui', 'success')
    return redirect(url_for('schedule'))

@app.route('/jadwal/hapus/<int:schedule_id>', methods=['POST'])
@login_required
@role_required(['admin', 'super_admin'])
def delete_schedule(schedule_id):
    schedule = DutySchedule.query.get_or_404(schedule_id)
    
    # Store user_id and date before deleting
    user_id = schedule.user_id
    schedule_date = schedule.date
    
    db.session.delete(schedule)
    db.session.commit()
    
    # Create notification for the user
    create_notification(
        user_id=user_id,
        title="Jadwal Dihapus",
        message=f"Jadwal anda pada tanggal {schedule_date.strftime('%d-%m-%Y')} telah dihapus",
        type="warning"
    )
    
    flash('Jadwal berhasil dihapus', 'success')
    return redirect(url_for('schedule'))

# Attendance routes
@app.route('/presensi')
@login_required
def attendance():
    user_role = Role.query.get(current_user.role_id).name
    today = date.today()
    
    # Get all personel for admin/super_admin
    if user_role in ['admin', 'super_admin']:
        personel_list = User.query.join(Role).filter(Role.name == 'personel').all()
    else:
        personel_list = None
    
    # Get today's schedule for current user
    today_schedule = DutySchedule.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    # Get today's attendance for current user
    today_attendance = Attendance.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    # Get recent attendances
    if user_role in ['admin', 'super_admin']:
        recent_attendances = Attendance.query.order_by(
            Attendance.date.desc(),
            Attendance.created_at.desc()
        ).limit(20).all()
    else:
        recent_attendances = Attendance.query.filter_by(
            user_id=current_user.id
        ).order_by(
            Attendance.date.desc(),
            Attendance.created_at.desc()
        ).limit(10).all()
    
    return render_template('attendance.html',
                           today_schedule=today_schedule,
                           today_attendance=today_attendance,
                           recent_attendances=recent_attendances,
                           personel_list=personel_list)

@app.route('/presensi/check-in', methods=['POST'])
@login_required
def check_in():
    notes = request.form.get('notes')
    location = request.form.get('location', 'Kantor')
    check_in_time = datetime.now()
    today = date.today()
    
    # Check if already checked in today
    existing_attendance = Attendance.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    if existing_attendance and existing_attendance.check_in_time:
        flash('Anda sudah melakukan check-in hari ini', 'warning')
        return redirect(url_for('attendance'))
    
    # Get today's schedule
    today_schedule = DutySchedule.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    attendance_type = today_schedule.shift_type if today_schedule else 'regular'
    duty_schedule_id = today_schedule.id if today_schedule else None
    
    # Determine status (on time or late)
    status = 'present'
    if today_schedule:
        schedule_start = datetime.combine(today, today_schedule.start_time)
        # If more than 15 minutes late
        if check_in_time > (schedule_start + timedelta(minutes=15)):
            status = 'late'
    
    if existing_attendance:
        # Update existing record
        existing_attendance.check_in_time = check_in_time
        existing_attendance.status = status
        existing_attendance.notes = notes
        existing_attendance.location = location
        db.session.commit()
        attendance_id = existing_attendance.id
    else:
        # Create new attendance record
        new_attendance = Attendance(
            user_id=current_user.id,
            duty_schedule_id=duty_schedule_id,
            attendance_type=attendance_type,
            date=today,
            check_in_time=check_in_time,
            status=status,
            notes=notes,
            location=location
        )
        db.session.add(new_attendance)
        db.session.commit()
        attendance_id = new_attendance.id
    
    # Create notification
    create_notification(
        user_id=current_user.id,
        title="Check-in Berhasil",
        message=f"Anda berhasil check-in pada {check_in_time.strftime('%H:%M')}",
        type="success"
    )
    
    flash(f'Check-in berhasil pada {check_in_time.strftime("%H:%M")}', 'success')
    return redirect(url_for('attendance'))

@app.route('/presensi/check-out', methods=['POST'])
@login_required
def check_out():
    notes = request.form.get('notes')
    check_out_time = datetime.now()
    today = date.today()
    
    # Find today's attendance
    attendance = Attendance.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    if not attendance:
        flash('Anda belum melakukan check-in hari ini', 'warning')
        return redirect(url_for('attendance'))
    
    if attendance.check_out_time:
        flash('Anda sudah melakukan check-out hari ini', 'warning')
        return redirect(url_for('attendance'))
    
    # Update attendance record
    attendance.check_out_time = check_out_time
    if notes:
        attendance.notes = f"{attendance.notes or ''}\nCheck-out: {notes}"
    db.session.commit()
    
    # Create notification
    create_notification(
        user_id=current_user.id,
        title="Check-out Berhasil",
        message=f"Anda berhasil check-out pada {check_out_time.strftime('%H:%M')}",
        type="success"
    )
    
    flash(f'Check-out berhasil pada {check_out_time.strftime("%H:%M")}', 'success')
    return redirect(url_for('attendance'))

@app.route('/presensi/update/<int:attendance_id>', methods=['POST'])
@login_required
@role_required(['admin', 'super_admin'])
def update_attendance(attendance_id):
    attendance = Attendance.query.get_or_404(attendance_id)
    
    status = request.form.get('status')
    notes = request.form.get('notes')
    
    if status:
        attendance.status = status
    
    if notes:
        attendance.notes = notes
    
    db.session.commit()
    
    # Create notification for the user
    create_notification(
        user_id=attendance.user_id,
        title="Presensi Diperbarui",
        message=f"Presensi anda pada tanggal {attendance.date.strftime('%d-%m-%Y')} telah diperbarui oleh admin",
        type="info"
    )
    
    flash('Data presensi berhasil diperbarui', 'success')
    return redirect(url_for('attendance'))

# Report routes
@app.route('/laporan')
@login_required
def reports():
    user_role = Role.query.get(current_user.role_id).name
    
    # Get all personel for admin/super_admin
    if user_role in ['admin', 'super_admin']:
        personel_list = User.query.join(Role).filter(Role.name == 'personel').all()
    else:
        personel_list = None
    
    return render_template('reports.html', personel_list=personel_list)

@app.route('/laporan/generate', methods=['POST'])
@login_required
def generate_report():
    report_type = request.form.get('report_type')
    output_format = request.form.get('output_format')
    user_id = request.form.get('user_id')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    
    if not report_type or not output_format or not start_date_str or not end_date_str:
        flash('Parameter laporan tidak lengkap', 'danger')
        return redirect(url_for('reports'))
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Validate date range
        if start_date > end_date:
            flash('Tanggal awal harus sebelum tanggal akhir', 'danger')
            return redirect(url_for('reports'))
        
        # For personel, can only see their own reports
        user_role = Role.query.get(current_user.role_id).name
        if user_role == 'personel':
            user_id = current_user.id
        
        # For admin/super_admin with no user selected, show all personel
        if user_role in ['admin', 'super_admin'] and not user_id:
            query = Attendance.query.join(User).join(Role).filter(
                Role.name == 'personel',
                Attendance.date.between(start_date, end_date)
            )
        else:
            query = Attendance.query.filter(
                Attendance.user_id == (user_id or current_user.id),
                Attendance.date.between(start_date, end_date)
            )
        
        # Order by date and check-in time
        attendances = query.order_by(Attendance.date, Attendance.check_in_time).all()
        
        if not attendances:
            flash('Tidak ada data presensi untuk periode yang dipilih', 'warning')
            return redirect(url_for('reports'))
        
        # Generate report based on format
        if output_format == 'pdf':
            report_buffer = generate_report_pdf(attendances, start_date, end_date, report_type)
            
            # Create response
            response = make_response(report_buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=laporan_presensi_{start_date_str}_to_{end_date_str}.pdf'
            
            return response
            
        elif output_format == 'csv':
            # Create a memory file
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Tanggal', 'Nama', 'Shift', 'Check-in', 'Check-out', 'Status', 'Lokasi', 'Catatan'])
            
            # Write data
            for attendance in attendances:
                check_in = attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time else '-'
                check_out = attendance.check_out_time.strftime('%H:%M') if attendance.check_out_time else '-'
                
                writer.writerow([
                    attendance.date.strftime('%d-%m-%Y'),
                    attendance.user.name,
                    attendance.attendance_type,
                    check_in,
                    check_out,
                    attendance.status,
                    attendance.location or '-',
                    attendance.notes or '-'
                ])
            
            # Create response
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                as_attachment=True,
                download_name=f'laporan_presensi_{start_date_str}_to_{end_date_str}.csv',
                mimetype='text/csv'
            )
        
        else:
            flash('Format output tidak valid', 'danger')
            return redirect(url_for('reports'))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('reports'))

# User management routes (admin and super_admin only)
@app.route('/users')
@login_required
@role_required(['admin', 'super_admin'])
def users():
    users = User.query.all()
    roles = Role.query.all()
    return render_template('users.html', users=users, roles=roles)

@app.route('/users/add', methods=['POST'])
@login_required
@role_required(['super_admin'])
def add_user():
    username = request.form.get('username')
    name = request.form.get('name')
    email = request.form.get('email')
    role_id = request.form.get('role_id')
    password = request.form.get('password', 'Tik123')  # Default password
    
    # Validate input
    if not username or not name or not email or not role_id:
        flash('Semua field harus diisi', 'danger')
        return redirect(url_for('users'))
    
    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        flash('Username sudah digunakan', 'danger')
        return redirect(url_for('users'))
    
    if User.query.filter_by(email=email).first():
        flash('Email sudah digunakan', 'danger')
        return redirect(url_for('users'))
    
    # Create new user
    new_user = User(
        username=username,
        name=name,
        email=email,
        role_id=role_id,
        password_hash=generate_password_hash(password)
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    flash(f'User {name} berhasil ditambahkan', 'success')
    return redirect(url_for('users'))

@app.route('/users/edit/<int:user_id>', methods=['POST'])
@login_required
@role_required(['super_admin'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    name = request.form.get('name')
    email = request.form.get('email')
    role_id = request.form.get('role_id')
    is_active = request.form.get('is_active') == 'on'
    reset_password = request.form.get('reset_password') == 'on'
    
    # Update user data
    if name:
        user.name = name
    
    if email and email != user.email:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            flash('Email sudah digunakan', 'danger')
            return redirect(url_for('users'))
        user.email = email
    
    if role_id:
        user.role_id = role_id
    
    user.is_active = is_active
    
    if reset_password:
        user.password_hash = generate_password_hash('Tik123')
    
    db.session.commit()
    flash(f'User {user.name} berhasil diperbarui', 'success')
    return redirect(url_for('users'))

@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required(['super_admin'])
def delete_user(user_id):
    # Don't allow deleting yourself
    if user_id == current_user.id:
        flash('Anda tidak dapat menghapus akun anda sendiri', 'danger')
        return redirect(url_for('users'))
    
    user = User.query.get_or_404(user_id)
    
    # Delete user's attendance records
    Attendance.query.filter_by(user_id=user_id).delete()
    
    # Delete user's schedules
    DutySchedule.query.filter_by(user_id=user_id).delete()
    
    # Delete user's notifications
    Notification.query.filter_by(user_id=user_id).delete()
    
    # Delete user
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.name} berhasil dihapus', 'success')
    return redirect(url_for('users'))

# API routes for AJAX requests
@app.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    # Only allow marking own notifications
    if notification.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/notifications/unread-count')
@login_required
def unread_notification_count():
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({'count': count})

@app.route('/api/get-month-schedules/<int:year>/<int:month>')
@login_required
def get_month_schedules(year, month):
    try:
        month_start = date(year, month, 1)
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        month_end = date(next_year, next_month, 1) - timedelta(days=1)
        
        user_role = Role.query.get(current_user.role_id).name
        
        if user_role in ['admin', 'super_admin']:
            schedules = DutySchedule.query.filter(
                DutySchedule.date.between(month_start, month_end)
            ).all()
        else:
            schedules = DutySchedule.query.filter(
                DutySchedule.date.between(month_start, month_end),
                DutySchedule.user_id == current_user.id
            ).all()
        
        schedule_data = []
        for schedule in schedules:
            schedule_data.append({
                'id': schedule.id,
                'user_id': schedule.user_id,
                'user_name': schedule.user.name,
                'date': schedule.date.strftime('%Y-%m-%d'),
                'shift_type': schedule.shift_type,
                'start_time': schedule.start_time.strftime('%H:%M'),
                'end_time': schedule.end_time.strftime('%H:%M'),
                'notes': schedule.notes
            })
        
        return jsonify({'success': True, 'schedules': schedule_data})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/get-attendance/<int:year>/<int:month>')
@login_required
def get_month_attendance(year, month):
    try:
        month_start = date(year, month, 1)
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        month_end = date(next_year, next_month, 1) - timedelta(days=1)
        
        user_role = Role.query.get(current_user.role_id).name
        
        if user_role in ['admin', 'super_admin']:
            attendances = Attendance.query.filter(
                Attendance.date.between(month_start, month_end)
            ).all()
        else:
            attendances = Attendance.query.filter(
                Attendance.date.between(month_start, month_end),
                Attendance.user_id == current_user.id
            ).all()
        
        attendance_data = []
        for attendance in attendances:
            attendance_data.append({
                'id': attendance.id,
                'user_id': attendance.user_id,
                'user_name': attendance.user.name,
                'date': attendance.date.strftime('%Y-%m-%d'),
                'check_in': attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time else None,
                'check_out': attendance.check_out_time.strftime('%H:%M') if attendance.check_out_time else None,
                'status': attendance.status,
                'attendance_type': attendance.attendance_type,
                'notes': attendance.notes
            })
        
        return jsonify({'success': True, 'attendances': attendance_data})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
