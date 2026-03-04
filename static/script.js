// Form Validation
document.getElementById('jobForm').addEventListener('submit', function(e) {
    let isValid = true;
    
    // Validate Name
    const name = document.getElementById('name');
    const nameError = document.getElementById('nameError');
    if (name.value.trim() === '') {
        nameError.textContent = 'Name is required';
        nameError.classList.add('show');
        name.classList.add('invalid');
        isValid = false;
    } else {
        nameError.classList.remove('show');
        name.classList.remove('invalid');
    }
    
    // Validate Email
    const email = document.getElementById('email');
    const emailError = document.getElementById('emailError');
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email.value)) {
        emailError.textContent = 'Invalid email address';
        emailError.classList.add('show');
        email.classList.add('invalid');
        isValid = false;
    } else {
        emailError.classList.remove('show');
        email.classList.remove('invalid');
    }
    
    // Validate Phone
    const phone = document.getElementById('phone');
    const phoneError = document.getElementById('phoneError');
    const phonePattern = /^[0-9]{10}$/;
    if (!phonePattern.test(phone.value)) {
        phoneError.textContent = 'Phone number must be 10 digits';
        phoneError.classList.add('show');
        phone.classList.add('invalid');
        isValid = false;
    } else {
        phoneError.classList.remove('show');
        phone.classList.remove('invalid');
    }
    
    if (!isValid) {
        e.preventDefault();
    }
});

// Verification Page Countdown Timer
let countdown;
let timeRemaining = 60;

function startCountdown() {
    const countdownElement = document.getElementById('countdown');
    if (!countdownElement) return;
    
    timeRemaining = 60;
    countdownElement.textContent = timeRemaining;
    
    // Clear any existing countdown
    if (countdown) {
        clearInterval(countdown);
    }
    
    countdown = setInterval(function() {
        timeRemaining--;
        countdownElement.textContent = timeRemaining;
        
        if (timeRemaining <= 0) {
            clearInterval(countdown);
            countdownElement.textContent = 'Expired';
            document.getElementById('verifyBtn').disabled = true;
            document.getElementById('resendBtn').disabled = false;
        }
    }, 1000);
}

// Resend Code Function
function resendCode() {
    alert('Verification code has been resent to your email and phone!');
    startCountdown();
}

// Start countdown when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('countdown')) {
        startCountdown();
    }
});

// Admin Functions
function selectAll() {
    document.querySelectorAll('.applicant-checkbox').forEach(cb => cb.checked = true);
}

function deselectAll() {
    document.querySelectorAll('.applicant-checkbox').forEach(cb => cb.checked = false);
}

function printSelected() {
    const checkboxes = document.querySelectorAll('.applicant-checkbox:checked');
    
    if (checkboxes.length === 0) {
        alert('Please select at least one applicant to print.');
        return;
    }
    
    // Check if printer is connected
    if (!isPrinterConnected()) {
        alert('⚠️ PC is not connected to a printer. Please connect a printer to print.\n\nTo connect printer:\n1. Connect printer via USB\n2. Turn on printer\n3. Install printer drivers\n4. Try again');
        return;
    }
    
    // Create print content
    let printContent = '<h1>Meghalaya Job Applications</h1>';
    printContent += '<p>Selected Applications:</p>';
    printContent += '<table border="1" style="width:100%; border-collapse: collapse;">';
    printContent += '<tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Date</th></tr>';
    
    checkboxes.forEach(cb => {
        const row = cb.closest('tr');
        printContent += `<tr>
            <td>${row.cells[1].textContent}</td>
            <td>${row.cells[2].textContent}</td>
            <td>${row.cells[3].textContent}</td>
            <td>${row.cells[4].textContent}</td>
            <td>${row.cells[6].textContent}</td>
        </tr>`;
    });
    
    printContent += '</table>';
    
    // Try to print
    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write('<html><head><title>Print Applications</title>');
    printWindow.document.write('<style>body{font-family:Arial; padding:20px;} table{border-collapse:collapse; width:100%;} th,td{border:1px solid #000; padding:10px;}</style>');
    printWindow.document.write('</head><body>');
    printWindow.document.write(printContent);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    
    // Attempt to print
    printWindow.print().catch(function() {
        alert('⚠️ PC is not connected to a printer. Please connect a printer to print.');
    });
}

function isPrinterConnected() {
    // Check if browser can access printer
    try {
        if (window.print) {
            return true;
        }
        return false;
    } catch (e) {
        return false;
    }
}

function deleteSelected() {
    const checkboxes = document.querySelectorAll('.applicant-checkbox:checked');
    
    if (checkboxes.length === 0) {
        alert('Please select at least one applicant to delete.');
        return;
    }
    
    if (confirm(`Are you sure you want to delete ${checkboxes.length} selected application(s)? This action cannot be undone!`)) {
        const ids = [];
        checkboxes.forEach(cb => {
            ids.push(cb.getAttribute('data-id'));
        });
        
        // Send delete request to server
        fetch('/delete_selected', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ids: ids })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`Successfully deleted ${data.deleted_count} application(s)!`);
                location.reload();
            } else {
                alert('Error deleting applications. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting applications. Please try again.');
        });
    }
}

function deleteSingle(id) {
    if (confirm('Are you sure you want to delete this application? This action cannot be undone!')) {
        fetch('/delete_single', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id: id })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Application deleted successfully!');
                location.reload();
            } else {
                alert('Error deleting application. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting application. Please try again.');
        });
    }
}

function exportToExcel() {
    const checkboxes = document.querySelectorAll('.applicant-checkbox:checked');
    
    if (checkboxes.length === 0) {
        alert('Please select at least one applicant to export.');
        return;
    }
    
    // Create CSV content
    let csvContent = 'ID,Name,Email,Phone,Date Submitted\n';
    
    checkboxes.forEach(cb => {
        const row = cb.closest('tr');
        csvContent += `${row.cells[1].textContent},${row.cells[2].textContent},${row.cells[3].textContent},${row.cells[4].textContent},${row.cells[6].textContent}\n`;
    });
    
    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'applications_export.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}