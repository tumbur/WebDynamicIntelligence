document.addEventListener('DOMContentLoaded', function() {
    // Check for chart elements
    const attendanceChartEl = document.getElementById('attendanceChart');
    const monthlyStatusChartEl = document.getElementById('monthlyStatusChart');
    
    // Initialize charts if elements exist
    if (attendanceChartEl) {
        initAttendanceChart(attendanceChartEl);
    }
    
    if (monthlyStatusChartEl) {
        initMonthlyStatusChart(monthlyStatusChartEl);
    }
    
    // Check unread notifications
    checkUnreadNotifications();
    
    // Setup notification read event handlers
    setupNotificationHandlers();
});

// Initialize monthly attendance chart
function initAttendanceChart(canvas) {
    // Get data from the data attributes
    const present = parseInt(canvas.dataset.present || 0);
    const absent = parseInt(canvas.dataset.absent || 0);
    
    const attendanceChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: ['Hadir', 'Tidak Hadir'],
            datasets: [{
                data: [present, absent],
                backgroundColor: [
                    '#28a745', // Green for present
                    '#dc3545'  // Red for absent
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e9ecef'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = present + absent;
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Initialize monthly status chart
function initMonthlyStatusChart(canvas) {
    // Get data from the data attributes
    const present = parseInt(canvas.dataset.present || 0);
    const late = parseInt(canvas.dataset.late || 0);
    const absent = parseInt(canvas.dataset.absent || 0);
    
    const monthlyStatusChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: ['Hadir', 'Terlambat', 'Tidak Hadir'],
            datasets: [{
                label: 'Bulan Ini',
                data: [present, late, absent],
                backgroundColor: [
                    '#28a745', // Green for present
                    '#ffc107', // Yellow for late
                    '#dc3545'  // Red for absent
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        color: '#e9ecef'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#e9ecef'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Check unread notifications count
function checkUnreadNotifications() {
    fetch('/api/notifications/unread-count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notification-badge');
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error fetching notifications:', error));
}

// Setup notification read event handlers
function setupNotificationHandlers() {
    document.querySelectorAll('.mark-notification-read').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const notificationId = this.dataset.id;
            
            fetch(`/api/notifications/mark-read/${notificationId}`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remove notification from list or mark as read
                    const item = this.closest('.notification-item');
                    if (item) {
                        item.classList.add('read');
                        this.remove(); // Remove the mark as read button
                    }
                    
                    // Update badge count
                    checkUnreadNotifications();
                }
            })
            .catch(error => console.error('Error marking notification as read:', error));
        });
    });
}

// Display current time in real-time
function updateCurrentTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };
        timeElement.textContent = now.toLocaleString('id-ID', options);
    }
}

// Update time every second
setInterval(updateCurrentTime, 1000);
updateCurrentTime(); // Initialize
function exportMutationLog() {
    window.location.href = '/mutation/export-pdf';
}
