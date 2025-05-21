document.addEventListener('DOMContentLoaded', function() {
    // Initialize calendar view
    initializeCalendar();
    
    // Setup schedule form handlers
    setupScheduleFormHandlers();
    
    // Initialize schedule data table if it exists
    const scheduleTable = document.getElementById('scheduleTable');
    if (scheduleTable) {
        initializeDataTable(scheduleTable);
    }
});

// Initialize FullCalendar
function initializeCalendar() {
    const calendarEl = document.getElementById('scheduleCalendar');
    if (!calendarEl) return;
    
    // Get current month and year
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth() + 1; // FullCalendar months are 1-based
    
    // Get current user role from data attribute
    const userRole = calendarEl.dataset.role || 'personel';
    
    // Initialize FullCalendar
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek'
        },
        themeSystem: 'bootstrap5',
        events: function(info, successCallback, failureCallback) {
            // Load events from API for the requested month
            const fetchMonth = info.start.getMonth() + 1;
            const fetchYear = info.start.getFullYear();
            
            fetch(`/api/get-month-schedules/${fetchYear}/${fetchMonth}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Transform the data into FullCalendar events
                        const events = data.schedules.map(schedule => {
                            let title = schedule.shift_type === 'daily' ? 'Piket Harian (24 Jam)' : 'Piket Reguler (8 Jam)';
                            
                            // If admin or super_admin, include name in title
                            if (userRole !== 'personel') {
                                title = `${schedule.user_name}: ${title}`;
                            }
                            
                            return {
                                id: schedule.id,
                                title: title,
                                start: schedule.date, // Convert to datetime if necessary
                                allDay: true,
                                color: schedule.shift_type === 'daily' ? '#dc3545' : '#28a745', // Red for daily, green for regular
                                extendedProps: {
                                    user_id: schedule.user_id,
                                    user_name: schedule.user_name,
                                    shift_type: schedule.shift_type,
                                    notes: schedule.notes
                                }
                            };
                        });
                        
                        successCallback(events);
                    } else {
                        failureCallback(new Error(data.message || 'Failed to load schedule data'));
                    }
                })
                .catch(error => {
                    console.error('Error fetching schedule data:', error);
                    failureCallback(error);
                });
        },
        // For admin/super_admin, make the events clickable to edit
        eventClick: function(info) {
            if (userRole === 'admin' || userRole === 'super_admin') {
                showEditScheduleModal(info.event);
            } else {
                // For personel, just show schedule details
                showScheduleDetails(info.event);
            }
        },
        // Allow admin/super_admin to add schedules by clicking on dates
        dateClick: function(info) {
            if (userRole === 'admin' || userRole === 'super_admin') {
                showAddScheduleModal(info.dateStr);
            }
        }
    });
    
    calendar.render();
}

// Display schedule details in a modal
function showScheduleDetails(event) {
    const modal = new bootstrap.Modal(document.getElementById('scheduleDetailsModal'));
    
    // Set modal content
    document.getElementById('scheduleDetailsTitle').textContent = event.title;
    document.getElementById('scheduleDetailsDate').textContent = new Date(event.start).toLocaleDateString('id-ID', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    const scheduleType = event.extendedProps.shift_type === 'daily' ? 'Piket Harian (24 Jam)' : 'Piket Reguler (8 Jam)';
    document.getElementById('scheduleDetailsType').textContent = scheduleType;
    
    const notesElement = document.getElementById('scheduleDetailsNotes');
    if (event.extendedProps.notes) {
        notesElement.textContent = event.extendedProps.notes;
        notesElement.parentElement.style.display = 'block';
    } else {
        notesElement.parentElement.style.display = 'none';
    }
    
    modal.show();
}

// Display edit schedule modal for admin/super_admin
function showEditScheduleModal(event) {
    const modal = new bootstrap.Modal(document.getElementById('editScheduleModal'));
    
    // Set form values
    const form = document.getElementById('editScheduleForm');
    form.action = `/jadwal/edit/${event.id}`;
    
    const shiftTypeSelect = form.querySelector('select[name="shift_type"]');
    shiftTypeSelect.value = event.extendedProps.shift_type;
    
    const notesTextarea = form.querySelector('textarea[name="notes"]');
    notesTextarea.value = event.extendedProps.notes || '';
    
    // Set modal title
    document.getElementById('editScheduleModalTitle').textContent = `Edit Jadwal: ${event.extendedProps.user_name}`;
    
    // Update the date display
    document.getElementById('editScheduleDate').textContent = new Date(event.start).toLocaleDateString('id-ID', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    // Setup delete button
    const deleteButton = document.getElementById('deleteScheduleBtn');
    deleteButton.dataset.id = event.id;
    
    modal.show();
}

// Display add schedule modal for admin/super_admin
function showAddScheduleModal(dateStr) {
    const modal = new bootstrap.Modal(document.getElementById('addScheduleModal'));
    
    // Set the date in the form
    document.getElementById('scheduleDate').value = dateStr;
    
    // Update the date display
    const displayDate = new Date(dateStr);
    document.getElementById('addScheduleDate').textContent = displayDate.toLocaleDateString('id-ID', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    modal.show();
}

// Initialize DataTable for schedule table
function initializeDataTable(table) {
    $(table).DataTable({
        order: [[0, 'desc']], // Order by first column (date) descending
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/id.json'
        },
        responsive: true,
        pageLength: 10
    });
}

// Setup form handlers for add, edit, delete schedule
function setupScheduleFormHandlers() {
    // Setup delete schedule handler
    const deleteScheduleBtn = document.getElementById('deleteScheduleBtn');
    if (deleteScheduleBtn) {
        deleteScheduleBtn.addEventListener('click', function() {
            if (confirm('Anda yakin ingin menghapus jadwal ini?')) {
                const scheduleId = this.dataset.id;
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = `/jadwal/hapus/${scheduleId}`;
                
                // Add CSRF token
                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrf_token';
                csrfInput.value = csrfToken;
                form.appendChild(csrfInput);
                
                document.body.appendChild(form);
                form.submit();
            }
        });
    }
    
    // Setup add schedule form validation
    const addScheduleForm = document.getElementById('addScheduleForm');
    if (addScheduleForm) {
        addScheduleForm.addEventListener('submit', function(e) {
            const userSelect = this.querySelector('select[name="user_id"]');
            const shiftTypeSelect = this.querySelector('select[name="shift_type"]');
            
            if (!userSelect.value) {
                e.preventDefault();
                alert('Silahkan pilih personel');
                return false;
            }
            
            if (!shiftTypeSelect.value) {
                e.preventDefault();
                alert('Silahkan pilih jenis shift');
                return false;
            }
            
            return true;
        });
    }
}
