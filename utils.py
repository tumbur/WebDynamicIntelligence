import io
from datetime import datetime, date, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import func, desc, extract, and_

from app import db
from models import Attendance, DutySchedule, Notification, User, Role

def create_notification(user_id, title, message, type='info'):
    """
    Create a new notification for a user.
    """
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type
    )
    db.session.add(notification)
    db.session.commit()
    return notification

def get_dashboard_stats(user):
    """
    Get attendance statistics for the dashboard.
    """
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)
    
    # Get user role
    role = Role.query.get(user.role_id).name
    
    # Stats for all users if admin/super_admin, otherwise just for the current user
    if role in ['admin', 'super_admin']:
        # Get all personel users
        personel_role = Role.query.filter_by(name='personel').first()
        total_users = User.query.filter_by(role_id=personel_role.id, is_active=True).count()
        
        # Get attendance stats
        today_present = Attendance.query.filter(
            Attendance.date == today,
            Attendance.status.in_(['present', 'late'])
        ).count()
        
        today_absent = total_users - today_present
        
        # Get this month's attendance stats
        month_attendances = Attendance.query.filter(
            Attendance.date.between(first_day_of_month, today)
        ).all()
        
        present_count = sum(1 for a in month_attendances if a.status in ['present', 'late'])
        late_count = sum(1 for a in month_attendances if a.status == 'late')
        absent_count = sum(1 for a in month_attendances if a.status == 'absent')
        
        # Get total schedules for this month
        total_schedules = DutySchedule.query.filter(
            DutySchedule.date.between(first_day_of_month, today)
        ).count()
        
        # Recent activity
        recent_attendances = Attendance.query.order_by(
            Attendance.date.desc(), 
            Attendance.check_in_time.desc()
        ).limit(10).all()
        
    else:  # personel
        # Get attendance stats just for this user
        today_present = Attendance.query.filter(
            Attendance.user_id == user.id,
            Attendance.date == today,
            Attendance.status.in_(['present', 'late'])
        ).count()
        
        today_absent = 1 - today_present
        
        # Get this month's attendance stats
        month_attendances = Attendance.query.filter(
            Attendance.user_id == user.id,
            Attendance.date.between(first_day_of_month, today)
        ).all()
        
        present_count = sum(1 for a in month_attendances if a.status in ['present', 'late'])
        late_count = sum(1 for a in month_attendances if a.status == 'late')
        absent_count = sum(1 for a in month_attendances if a.status == 'absent')
        
        # Get total schedules for this month
        total_schedules = DutySchedule.query.filter(
            DutySchedule.user_id == user.id,
            DutySchedule.date.between(first_day_of_month, today)
        ).count()
        
        # Recent activity
        recent_attendances = Attendance.query.filter(
            Attendance.user_id == user.id
        ).order_by(
            Attendance.date.desc(), 
            Attendance.check_in_time.desc()
        ).limit(10).all()
    
    return {
        'today_present': today_present,
        'today_absent': today_absent,
        'month_present': present_count,
        'month_late': late_count,
        'month_absent': absent_count,
        'total_schedules': total_schedules,
        'recent_attendances': recent_attendances
    }

def generate_report_pdf(attendances, start_date, end_date, report_type):
    """
    Generate a PDF report of attendance data.
    """
    buffer = io.BytesIO()
    
    # Create the PDF object
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=18
    )
    
    styles = getSampleStyleSheet()
    
    # Build elements for the PDF
    elements = []
    
    # Title
    title_text = f"LAPORAN PRESENSI PERSONEL TIK POLRES ACEH TAMIANG"
    title = Paragraph(title_text, styles['Title'])
    elements.append(title)
    
    # Subtitle with date range
    period_text = f"Periode: {start_date.strftime('%d-%m-%Y')} s/d {end_date.strftime('%d-%m-%Y')}"
    period = Paragraph(period_text, styles['Heading2'])
    elements.append(period)
    elements.append(Spacer(1, 12))
    
    # Table data
    table_data = [
        ['No.', 'Tanggal', 'Nama', 'Shift', 'Check-in', 'Check-out', 'Status', 'Catatan']
    ]
    
    for i, attendance in enumerate(attendances, 1):
        check_in = attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time else '-'
        check_out = attendance.check_out_time.strftime('%H:%M') if attendance.check_out_time else '-'
        
        table_data.append([
            str(i),
            attendance.date.strftime('%d-%m-%Y'),
            attendance.user.name,
            attendance.attendance_type.capitalize(),
            check_in,
            check_out,
            attendance.status.capitalize(),
            attendance.notes or '-'
        ])
    
    # Create table
    table = Table(table_data, colWidths=[30, 70, 120, 60, 60, 60, 70, 180])
    
    # Style the table
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (6, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    
    # Add zebra striping
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
    
    # Apply style to table
    table.setStyle(table_style)
    elements.append(table)
    
    # Add summary if this is a summary report
    if report_type == 'summary':
        elements.append(Spacer(1, 20))
        
        # Calculate statistics
        total_records = len(attendances)
        present_count = sum(1 for a in attendances if a.status == 'present')
        late_count = sum(1 for a in attendances if a.status == 'late')
        absent_count = sum(1 for a in attendances if a.status == 'absent')
        sick_count = sum(1 for a in attendances if a.status == 'sick')
        permission_count = sum(1 for a in attendances if a.status == 'permission')
        
        # Create summary table
        summary_data = [
            ['RINGKASAN', ''],
            ['Total Hari', total_records],
            ['Hadir', present_count],
            ['Terlambat', late_count],
            ['Tidak Hadir', absent_count],
            ['Sakit', sick_count],
            ['Izin', permission_count],
        ]
        
        summary_table = Table(summary_data, colWidths=[120, 80])
        summary_style = TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('SPAN', (0, 0), (1, 0)),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 10),
            ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
            ('BACKGROUND', (1, 1), (1, -1), colors.white),
            ('GRID', (0, 0), (1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ])
        summary_table.setStyle(summary_style)
        elements.append(summary_table)
    
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer
