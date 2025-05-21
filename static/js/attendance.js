document.addEventListener('DOMContentLoaded', function() {
    // Set current date and time for check-in/check-out
    updateCurrentDateTime();
    
    // Initialize attendance data table if it exists
    const attendanceTable = document.getElementById('attendanceTable');
    if (attendanceTable) {
        initializeDataTable(attendanceTable);
    }
    
    // Setup check-in form handler
    const checkInForm = document.getElementById('checkInForm');
    if (checkInForm) {
        checkInForm.addEventListener('submit', function(e) {
            if (!confirmAction('Anda yakin ingin melakukan check-in sekarang?')) {
                e.preventDefault();
            }
        });
    }
    
    // Setup check-out form handler
    const checkOutForm = document.getElementById('checkOutForm');
    if (checkOutForm) {
        checkOutForm.addEventListener('submit', function(e) {
            if (!confirmAction('Anda yakin ingin melakukan check-out sekarang?')) {
                e.preventDefault();
            }
        });
    }
    
    // Setup edit attendance form
    setupEditAttendanceForm();
});

// Update current date and time
function updateCurrentDateTime() {
    const currentDateElement = document.getElementById('current-date');
    const currentTimeElement = document.getElementById('current-time');
    
    if (currentDateElement || currentTimeElement) {
        const now = new Date();
        
        if (currentDateElement) {
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            currentDateElement.textContent = now.toLocaleDateString('id-ID', options);
        }
        
        if (currentTimeElement) {
            const timeOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit' };
            const updateTime = () => {
                const newTime = new Date().toLocaleTimeString('id-ID', timeOptions);
                if (currentTimeElement.textContent !== newTime) {
                    currentTimeElement.style.opacity = '1';
                    currentTimeElement.textContent = newTime;
                }
            };
            updateTime();
            setInterval(updateTime, 1000);
        }
    }
}

// Initialize DataTable for attendance records
function initializeDataTable(table) {
    // Initialize DataTable with options
    $(table).DataTable({
        order: [[0, 'desc']], // Order by first column (date) descending
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/id.json'
        },
        responsive: true,
        pageLength: 10,
        dom: 'Bfrtip',
        buttons: [
            'copyHtml5',
            'excelHtml5',
            'csvHtml5',
            'pdfHtml5'
        ]
    });
}

// Confirm action with user
function confirmAction(message) {
    return confirm(message);
}

// Setup edit attendance form
function setupEditAttendanceForm() {
    // Get all edit attendance buttons
    const editButtons = document.querySelectorAll('.edit-attendance-btn');
    
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const attendanceId = this.dataset.id;
            const status = this.dataset.status;
            const notes = this.dataset.notes || '';
            
            // Set values in edit form
            const form = document.getElementById('editAttendanceForm');
            if (form) {
                form.action = `/presensi/update/${attendanceId}`;
                
                // Set status in select element
                const statusSelect = form.querySelector('select[name="status"]');
                if (statusSelect) {
                    statusSelect.value = status;
                }
                
                // Set notes in textarea
                const notesTextarea = form.querySelector('textarea[name="notes"]');
                if (notesTextarea) {
                    notesTextarea.value = notes;
                }
            }
        });
    });
}

// Get current location for attendance
function getCurrentLocation() {
    const locationInput = document.getElementById('locationInput');
    
    if (locationInput && navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                locationInput.value = `Lat: ${latitude}, Long: ${longitude}`;
            },
            function(error) {
                console.error('Error getting location:', error);
                locationInput.value = 'Lokasi tidak diketahui';
            }
        );
    }
}

// Call location function when check-in form is displayed
document.addEventListener('shown.bs.modal', function(event) {
    if (event.target.id === 'checkInModal') {
        getCurrentLocation();
    }
});

// Export mutation to PDF
function exportToPDF() {
    const attendanceId = document.querySelector('input[name="attendance_id"]').value;
    window.location.href = `/presensi/mutation/${attendanceId}/pdf`;
}
