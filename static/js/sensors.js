// Toggle between Table and Graph views using the switch
document.getElementById('toggleViewSwitch').addEventListener('change', function () {
    const tableContainer = document.getElementById('history-table-container');
    const graphContainer = document.getElementById('graph-view-container');
    if (this.checked) {
        tableContainer.style.display = 'none';
        graphContainer.style.display = 'block';
    } else {
        graphContainer.style.display = 'none';
        tableContainer.style.display = 'block';
    }
});

// Listen for changes in the filter dropdown to show custom modal if needed
document.getElementById('filter').addEventListener('change', function () {
    if (this.value === 'custom') {
        document.getElementById('customModal').style.display = 'flex';
    }
});

// Close the modal when the X is clicked
document.getElementById('closeModal').addEventListener('click', function () {
    document.getElementById('customModal').style.display = 'none';
    document.getElementById('filter').value = 'today';
});

// Global variables for chart instances and current data
let phChart;
let waterChart;
let currentData = [];

// Function to build the table view
function buildTable(data) {
    let html = '<table>';
    html += '<thead><tr><th>Date</th><th>Time</th><th>pH</th><th>Water</th></tr></thead>';
    html += '<tbody>';
    data.forEach(row => {
        html += `<tr>
                <td>${row.date}</td>
                <td>${row.time}</td>
                <td>${row.ph}</td>
                <td>${row.water}%</td>
              </tr>`;
    });
    html += '</tbody></table>';
    document.getElementById('history-table-container').innerHTML = html;
}

// Function to update the graphs using Chart.js
function updateGraphs(data) {
    // Assume each data row contains 'date', 'time', 'ph', and 'water'
    const labels = data.map(row => `${row.date} ${row.time}`);
    const phValues = data.map(row => parseFloat(row.ph));
    const waterValues = data.map(row => parseFloat(row.water));

    // pH chart
    if (phChart) {
        phChart.data.labels = labels;
        phChart.data.datasets[0].data = phValues;
        phChart.update();
    } else {
        const ctxPh = document.getElementById('phChart').getContext('2d');
        phChart = new Chart(ctxPh, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'pH Level',
                    data: phValues,
                    borderColor: 'green',
                    backgroundColor: 'rgba(0, 255, 0, 0.1)',
                }]
            },
            options: {
                responsive: true,
            }
        });
    }

    // Water Level chart
    if (waterChart) {
        waterChart.data.labels = labels;
        waterChart.data.datasets[0].data = waterValues;
        waterChart.update();
    } else {
        const ctxWater = document.getElementById('waterChart').getContext('2d');
        waterChart = new Chart(ctxWater, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Water Level',
                    data: waterValues,
                    borderColor: 'blue',
                    backgroundColor: 'rgba(0, 0, 255, 0.1)',
                }]
            },
            options: {
                responsive: true,
            }
        });
    }
}

// Function to fetch data from the backend based on filter parameters
function fetchHistoryData(filter, startDate = '', endDate = '') {
    let url = `/get_csv_data?filter=${filter}`;
    if (filter === 'custom' && startDate && endDate) {
        url += `&start=${startDate}&end=${endDate}`;
    }
    fetch(url)
        .then(response => response.json())
        .then(data => {
            currentData = data;
            buildTable(data);
            updateGraphs(data);
        })
        .catch(err => console.error('Error fetching data:', err));
}

// Default fetch on page load (for "today")
window.addEventListener('load', () => {
    fetchHistoryData('today');
});

// Listen for changes on the filter dropdown to fetch data
document.getElementById('filter').addEventListener('change', function () {
    if (this.value === 'custom') {
        document.getElementById('customModal').style.display = 'flex';
    } else {
        fetchHistoryData(this.value);
    }
});

// Handle Apply button in the modal for custom date filtering
document.getElementById('applyDates').addEventListener('click', function () {
    const startDateInput = document.getElementById('startDate').value;
    const endDateInput = document.getElementById('endDate').value;
    if (!startDateInput || !endDateInput) {
        alert('Please select both start and end dates.');
        return;
    }
    document.getElementById('customModal').style.display = 'none';
    fetchHistoryData('custom', startDateInput, endDateInput);
    updateDownloadLink();
});

// Update download link based on filter and dates
function updateDownloadLink() {
    const filter = document.getElementById('filter').value;
    let url = `/download?filter=${filter}`;
    if (filter === 'custom') {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        if (startDate && endDate) {
            url += `&start=${startDate}&end=${endDate}`;
        }
    }
    document.getElementById('downloadBtn').href = url;
}

// Update download link when filter changes and on page load
document.getElementById('filter').addEventListener('change', updateDownloadLink);
window.addEventListener('load', updateDownloadLink);

// Initialize Flatpickr for date inputs
window.addEventListener('load', () => {
    flatpickr('#startDate', {
        dateFormat: 'd-m-Y',
        disableMobile: true,
        maxDate: 'today',
        onOpen: (selectedDates, dateStr, instance) => {
            instance.calendarContainer.classList.add('centered-popup');
        },
        onClose: (selectedDates, dateStr, instance) => {
            instance.calendarContainer.classList.remove('centered-popup');
        }
    });

    flatpickr('#endDate', {
        dateFormat: 'd-m-Y',
        disableMobile: true,
        maxDate: 'today',
        onOpen: (selectedDates, dateStr, instance) => {
            instance.calendarContainer.classList.add('centered-popup');
        },
        onClose: (selectedDates, dateStr, instance) => {
            instance.calendarContainer.classList.remove('centered-popup');
        }
    });
});