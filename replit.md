# Presensi TIK Polres Aceh Tamiang - System Overview

## Overview

This application is an attendance system ("Presensi") for IT personnel at Polres Aceh Tamiang (police department). It's built with Flask and SQLAlchemy, featuring role-based access (Personel, Admin, Super Admin), attendance tracking, duty scheduling, and reporting capabilities. The system allows users to check in/out, view their schedules, generate reports, and for administrators to manage users and monitor attendance data.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture

The application follows a typical Flask MVC-like architecture:

1. **Application Core**: Centralized in `app.py`, which initializes the Flask app, configures middleware, sets up database connections, and integrates extensions.

2. **Routes & Controllers**: Defined in `routes.py`, handling HTTP requests, implementing business logic, and rendering views.

3. **Data Layer**: Uses SQLAlchemy ORM with models defined in `models.py`.

4. **Authentication & Authorization**: Implemented in `auth.py` using Flask-Login for session management and custom role-based access control.

5. **Configuration**: Maintained in `config.py` with various system parameters.

### Frontend Architecture

The frontend uses a server-side rendering approach with Jinja2 templates:

1. **Base Template**: `base.html` provides the layout structure and common elements.

2. **Role-Specific Views**: Separate dashboard templates for each user role.

3. **Component Organization**: Templates for specific features (attendance, reports, schedule, etc.).

4. **Client-Side Enhancements**: JavaScript files enhance user experience for specific features.

### Database Design

The application uses SQLAlchemy with SQLite by default, but can be configured to use PostgreSQL:

1. **Users & Authentication**: User model with role relationships and authentication attributes.

2. **Attendance Tracking**: Models for recording check-ins/outs and attendance status.

3. **Scheduling**: Models for duty schedules with different shift types.

4. **Notifications**: System for alerting users about relevant events.

## Key Components

### Authentication System

- Uses Flask-Login for session management
- Password hashing using Werkzeug's security utilities
- Role-based access control with custom decorators
- Session persistence and CSRF protection

### Attendance Management

- Check-in and check-out functionality
- Attendance status tracking (present, late, absent, sick, permission)
- Late arrival detection based on configured thresholds
- Historical attendance records

### Duty Scheduling

- Schedule management for regular (8-hour) and daily (24-hour) shifts
- Calendar view for visualizing schedules
- Assignment of personnel to specific shifts
- Schedule conflict prevention

### Reporting System

- Generation of daily, weekly, and monthly reports
- Export capabilities (PDF format)
- Filtering and customization options
- Role-specific report access

### User Management

- User creation and profile management
- Role assignment and permission control
- Account activation/deactivation
- Profile information updates

### Notification System

- In-app notifications for important events
- Real-time updates on attendance status
- Administrative notifications for exceptions

## Data Flow

1. **Authentication Flow**:
   - User submits credentials → Validation → Session creation → Redirect to role-appropriate dashboard
   - Role-based middleware checks permissions for protected routes

2. **Attendance Flow**:
   - User requests check-in → System validates time against schedule → Records attendance → Updates statistics
   - Automated status assignment based on time (present, late, etc.)

3. **Reporting Flow**:
   - User sets report parameters → System queries relevant data → Formats according to report type → Renders or generates downloadable file
   - Cached calculations for frequently accessed metrics

4. **Admin Operations Flow**:
   - Admin creates/modifies users or schedules → System validates input → Updates database → Notifies affected users
   - Super admin has additional system-wide configuration capabilities

## External Dependencies

### Core Flask Dependencies
- `flask`: Web framework
- `flask-sqlalchemy`: ORM for database operations
- `flask-login`: User session management
- `flask-wtf`: Form handling with CSRF protection
- `flask-migrate`: Database migration support

### Database
- `sqlalchemy`: ORM framework
- `psycopg2-binary`: PostgreSQL adapter

### Authentication
- `werkzeug`: Security utilities for password hashing
- `pyjwt`: JSON Web Token implementation

### Reporting
- `reportlab`: PDF generation

### Frontend Enhancement
- Bootstrap (via CDN): UI framework
- Font Awesome (via CDN): Icons
- FullCalendar (via CDN): Calendar visualization
- DataTables (via CDN): Enhanced table displays

## Deployment Strategy

The application is configured for deployment on Replit:

1. **Runtime Environment**:
   - Python 3.11
   - Dependency management via pyproject.toml

2. **Database**:
   - Default: SQLite for development
   - Production: Can use PostgreSQL (included in Nix packages)

3. **Server Configuration**:
   - Gunicorn as the WSGI server
   - Port 5000 for HTTP traffic
   - ProxyFix middleware to handle proxy headers

4. **Scaling**:
   - Configured for autoscaling with the `deploymentTarget` set to "autoscale"
   - Connection pool recycling for database stability

5. **Development Workflow**:
   - Replit workflows for running the application
   - Hot reloading enabled for development

The system is designed to be easily deployed on Replit's infrastructure with minimal configuration, leveraging environment variables for customization in different environments.