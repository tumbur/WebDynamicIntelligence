document.addEventListener('DOMContentLoaded', function() {
    // Setup date picker functionality
    setupDatePickers();
    
    // Initialize form validation
    setupFormValidation();
    
    // Listen for report type changes
    setupReportTypeChange();
});

// Setup date picker elements
function setupDatePickers() {
    // Set default dates (current month)
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    
    // Format dates as yyyy-mm-dd
    const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    // Set default values in date inputs
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput && endDateInput) {
        startDateInput.value = formatDate(firstDay);
        endDateInput.value = formatDate(lastDay);
        
        // Set min/max dates
        startDateInput.addEventListener('change', function() {
            endDateInput.min = this.value;
        });
        
        endDateInput.addEventListener('change', function() {
            startDateInput.max = this.value;
        });
    }
    
    // Setup quick date selectors
    setupQuickDateSelectors(formatDate);
}

// Setup quick date selector buttons
function setupQuickDateSelectors(formatDate) {
    const today = new Date();
    
    // Get date range selector buttons
    const thisWeekBtn = document.getElementById('this-week-btn');
    const thisMonthBtn = document.getElementById('this-month-btn');
    const lastMonthBtn = document.getElementById('last-month-btn');
    
    // Get date inputs
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (thisWeekBtn && startDateInput && endDateInput) {
        thisWeekBtn.addEventListener('click', function() {
            // Calculate this week's start (Monday) and end (Sunday)
            const currentDay = today.getDay(); // 0 = Sunday, 1 = Monday
            const startOffset = currentDay === 0 ? -6 : 1 - currentDay; // If today is Sunday, get last Monday
            const startDate = new Date(today);
            startDate.setDate(today.getDate() + startOffset);
            
            const endDate = new Date(startDate);
            endDate.setDate(startDate.getDate() + 6);
            
            startDateInput.value = formatDate(startDate);
            endDateInput.value = formatDate(endDate);
        });
    }
    
    if (thisMonthBtn && startDateInput && endDateInput) {
        thisMonthBtn.addEventListener('click', function() {
            // Calculate this month's start and end
            const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
            const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            
            startDateInput.value = formatDate(firstDay);
            endDateInput.value = formatDate(lastDay);
        });
    }
    
    if (lastMonthBtn && startDateInput && endDateInput) {
        lastMonthBtn.addEventListener('click', function() {
            // Calculate last month's start and end
            const firstDay = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            const lastDay = new Date(today.getFullYear(), today.getMonth(), 0);
            
            startDateInput.value = formatDate(firstDay);
            endDateInput.value = formatDate(lastDay);
        });
    }
}

// Setup form validation
function setupFormValidation() {
    const reportForm = document.getElementById('report-form');
    
    if (reportForm) {
        reportForm.addEventListener('submit', function(e) {
            const reportType = document.querySelector('input[name="report_type"]:checked');
            const outputFormat = document.querySelector('input[name="output_format"]:checked');
            const startDate = document.getElementById('start_date');
            const endDate = document.getElementById('end_date');
            
            // Validate required fields
            if (!reportType) {
                e.preventDefault();
                alert('Silahkan pilih jenis laporan');
                return false;
            }
            
            if (!outputFormat) {
                e.preventDefault();
                alert('Silahkan pilih format output');
                return false;
            }
            
            if (!startDate.value) {
                e.preventDefault();
                alert('Silahkan pilih tanggal mulai');
                return false;
            }
            
            if (!endDate.value) {
                e.preventDefault();
                alert('Silahkan pilih tanggal akhir');
                return false;
            }
            
            // Validate date range
            if (new Date(startDate.value) > new Date(endDate.value)) {
                e.preventDefault();
                alert('Tanggal mulai harus sebelum tanggal akhir');
                return false;
            }
            
            // Show loading indicator
            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
            submitBtn.disabled = true;
            
            return true;
        });
    }
}

// Setup report type change handler
function setupReportTypeChange() {
    const reportTypeInputs = document.querySelectorAll('input[name="report_type"]');
    const userSelectContainer = document.getElementById('user-select-container');
    
    if (reportTypeInputs && userSelectContainer) {
        reportTypeInputs.forEach(input => {
            input.addEventListener('change', function() {
                // If summary is selected and user is admin/super_admin, show user selector
                if (this.value === 'summary' && userSelectContainer.dataset.role !== 'personel') {
                    userSelectContainer.style.display = 'block';
                } else {
                    userSelectContainer.style.display = 'none';
                }
            });
        });
    }
}
