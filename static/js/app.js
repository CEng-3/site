// Simple tab switching with dynamic timelapse video loading
document.querySelectorAll('.tabs a').forEach((tab) => {
    tab.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelectorAll('.tabs a, .tab-content')
            .forEach(element => element.classList.remove('active'));
        tab.classList.add('active');
        const tabContent = document.querySelector(tab.getAttribute('href'));
        tabContent.classList.add('active');
        // If Timelapse tab is activated, update video source dynamically
        if (tab.getAttribute('href') === "#timelapse") {
            const video = document.getElementById('timelapse-video');
            const today = new Date();
            const year = today.getFullYear();
            const month = (today.getMonth() + 1).toString().padStart(2, '0');
            const day = today.getDate().toString().padStart(2, '0');
            const dateStr = `${year}-${month}-${day}`;
            const videoPath = `/static/${camera}/${videoName}`;
            const timestamp = new Date().getTime(); // cache busting
            video.innerHTML = `<source src="${videoPath}?t=${timestamp}" type="video/mp4">Your browser does not support the video tag.`;
            video.load();
        }
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const totalArcLength = 160.57; // common arc length for both gauges
    let lowWaterThreshold = 20;  // default threshold
    let minPH = 6.0, maxPH = 7.5;  // default pH range

    // --- Water Level Gauge Elements ---
    const waterGauge = document.querySelector('.arc-gauge:not(.arc-gauge-ph)');
    const waterProgressPath = waterGauge.querySelector('.progress');
    const waterLabel = waterGauge.querySelector('.percentage');

    // --- pH Gauge Elements ---
    const phGauge = document.querySelector('.arc-gauge-ph');
    const phProgressPath = phGauge.querySelector('.progress');
    const phLabel = phGauge.querySelector('.percentage');

    // Load initial readings from the CSV file when page loads
    async function loadInitialReadings() {
        try {
            const response = await fetch('/initial_readings');
            const data = await response.json();

            // Update pH gauge
            const phValue = data.ph;
            const phOffset = totalArcLength - (phValue / 14) * totalArcLength;
            phProgressPath.style.strokeDashoffset = phOffset.toFixed(2);
            phLabel.textContent = phValue.toFixed(1);
            const phColor = getPHColor(phValue);
            phProgressPath.style.stroke = phColor;
            phLabel.style.fill = phColor;

            // Update water gauge
            const sensorPercentage = parseFloat(data.water);
            const waterOffset = totalArcLength - (sensorPercentage / 100) * totalArcLength;
            waterProgressPath.style.strokeDashoffset = waterOffset.toFixed(2);
            waterLabel.textContent = Math.round(sensorPercentage) + '%';

            // Update notification bar with initial values
            updateNotificationBar();
        } catch (error) {
            console.error('Error fetching initial readings:', error);
        }
    }

    // Load initial readings when page loads
    loadInitialReadings();

    // Load thresholds from server
    function loadThresholds() {
        fetch('/get_thresholds')
            .then(response => response.json())
            .then(data => {
                // Update threshold values
                lowWaterThreshold = data.water_level_threshold;
                minPH = data.ph_min_threshold;
                maxPH = data.ph_max_threshold;

                // Update notification bar with new thresholds
                updateNotificationBar();
            })
            .catch(error => console.error('Error loading thresholds:', error));
    }

    // Load thresholds when page loads
    loadThresholds();

    // Check for new thresholds periodically
    setInterval(loadThresholds, 30000); // Check every 30 seconds

    // Function to get a color based on pH value
    function getPHColor(ph) {
        if (ph < 4) return "#FF0000";
        else if (ph < 7) return "#FFA500";
        else if (Math.abs(ph - 7) < 0.1) return "#00FF00";
        else if (ph < 10) return "#0000FF";
        else return "#800080";
    }

    setInterval(updateNotificationBar, 5000);
    updateNotificationBar();

    // Update pH gauge by fetching /ph_data every 5 seconds
    async function updatePH() {
        try {
            const response = await fetch('/ph_data');
            const data = await response.json();
            let phValue = data.ph;

            // Store the last valid pH value
            if (!window.lastValidPH) {
                window.lastValidPH = 7.0; // Default neutral pH
            }

            // Check if pH is negative or above 14, use last valid value if it is
            if (phValue < 0 || phValue > 14) {
                console.warn('Received invalid pH value (' + phValue + '), using last valid value instead');
                phValue = window.lastValidPH;
            } else {
                // Update the last valid pH value
                window.lastValidPH = phValue;
            }

            const phOffset = totalArcLength - (phValue / 14) * totalArcLength;
            phProgressPath.style.strokeDashoffset = phOffset.toFixed(2);
            phLabel.textContent = phValue.toFixed(1);
            const phColor = getPHColor(phValue);
            phProgressPath.style.stroke = phColor;
            phLabel.style.fill = phColor;
        } catch (error) {
            console.error('Error fetching pH data:', error);
        }
    }
    setInterval(updatePH, 5000);
    updatePH();

    // Update water gauge by fetching /water_data every 5 seconds
    async function updateWaterLevel() {
        try {
            const response = await fetch('/water_data');
            const data = await response.json();
            const sensorPercentage = parseFloat(data.water);
            const waterOffset = totalArcLength - (sensorPercentage / 100) * totalArcLength;
            waterProgressPath.style.strokeDashoffset = waterOffset.toFixed(2);
            waterLabel.textContent = Math.round(sensorPercentage) + '%';
        } catch (error) {
            console.error('Error fetching water data:', error);
        }
    }
    setInterval(updateWaterLevel, 5000);
    updateWaterLevel();

    // Update Notification Bar based on live values
    function updateNotificationBar() {
        const waterValue = parseFloat(waterLabel.textContent);
        const pHValue = parseFloat(phLabel.textContent);
        const notificationBar = document.getElementById('notification-bar');

        if (waterValue < lowWaterThreshold || pHValue < minPH || pHValue > maxPH) {
            notificationBar.style.display = 'block';
            let message = '';
            if (waterValue < lowWaterThreshold && (pHValue < minPH || pHValue > maxPH)) {
                message = 'Warning: Low water level and pH out of range!';
            } else if (waterValue < lowWaterThreshold) {
                message = 'Warning: Low water level!';
            } else {
                message = 'Warning: pH out of range!';
            }
            notificationBar.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
        } else {
            notificationBar.style.display = 'none';
        }
    }

    // Function to group videos by date
    function groupVideosByDate(videos) {
        const groupedVideos = {};
        videos.forEach(video => {
            const dateMatch = video.match(/timelapse_(\d{4}-\d{2}-\d{2})/);
            if (dateMatch) {
                const date = dateMatch[1];
                if (!groupedVideos[date]) {
                    groupedVideos[date] = [];
                }
                groupedVideos[date].push(video);
            }
        });
        return groupedVideos;
    }

    // Function to load and display timelapse videos
    async function loadTimelapseVideos(camera = 'cam1') {
        try {
            const response = await fetch(`/timelapse_list?camera=${camera}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const videos = await response.json();
            const videoGrid = document.getElementById('timelapse-grid');
            videoGrid.innerHTML = ''; // Clear existing content

            const groupedVideos = groupVideosByDate(videos);

            // Sort dates in descending order
            const sortedDates = Object.keys(groupedVideos).sort((a, b) => new Date(b) - new Date(a));

            sortedDates.forEach(date => {
                // Add date group header
                const dateHeader = document.createElement('div');
                dateHeader.classList.add('date-group');
                dateHeader.textContent = date;
                videoGrid.appendChild(dateHeader);

                // Add videos for this date
                groupedVideos[date].forEach(videoName => {
                    const thumbnailContainer = document.createElement('div');
                    thumbnailContainer.classList.add('timelapse-thumbnail');

                    const img = document.createElement('img');
                    img.src = `/static/${camera}/${videoName.replace('.mp4', '.jpg')}`;
                    img.alt = `Timelapse ${videoName}`;

                    const videoLabel = document.createElement('p');
                    videoLabel.textContent = videoName;

                    thumbnailContainer.appendChild(img);
                    thumbnailContainer.appendChild(videoLabel);

                    thumbnailContainer.addEventListener('click', () => {
                        const video = document.getElementById('timelapse-video');
                        const videoPath = `/static/${camera}/${videoName}`;
                        const timestamp = new Date().getTime(); // cache busting
                        video.innerHTML = `<source src="${videoPath}?t=${timestamp}" type="video/mp4">Your browser does not support the video tag.`;
                        video.load();
                    });

                    videoGrid.appendChild(thumbnailContainer);
                });
            });
        } catch (error) {
            console.error('Error loading timelapse videos:', error);
        }
    }

    // Camera selection event listeners
    document.querySelectorAll('.camera-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            document.querySelectorAll('.camera-btn').forEach(b => b.classList.remove('active'));

            // Add active class to clicked button
            btn.classList.add('active');

            // Load videos for selected camera
            const camera = btn.dataset.camera;
            loadTimelapseVideos(camera);
        });
    });

    // Modify existing tab click handler to load timelapse videos
    document.querySelectorAll('.tabs a').forEach((tab) => {
        tab.addEventListener('click', (e) => {
            // If Timelapse tab is activated, load videos
            if (tab.getAttribute('href') === "#timelapse") {
                // Load videos for currently active camera
                const activeCamera = document.querySelector('.camera-btn.active').dataset.camera;
                loadTimelapseVideos(activeCamera);
            }
        });
    });

    // Optional: Load videos when page loads if timelapse tab is active
    if (document.querySelector('.tabs a[href="#timelapse"]').classList.contains('active')) {
        loadTimelapseVideos();
    }

    document.addEventListener("DOMContentLoaded", function () {
        // Retrieve stored values on load
        const storedWaterLevel = localStorage.getItem("sensorLevel");
        if (storedWaterLevel) {
            const waterLabel = document.querySelector('.arc-gauge .percentage');
            waterLabel.textContent = storedWaterLevel;
            // Update any related gauge progress if necessary
        }

        const storedPHMin = localStorage.getItem("phMin");
        const storedPHMax = localStorage.getItem("phMax");
        if (storedPHMin && storedPHMax) {
            // Assuming you have elements for pH gauge thresholds
            // For example, updating the pH gauge text:
            const phLabel = document.querySelector('.arc-gauge-ph .percentage');
            // You can decide whether to show one of the thresholds or both,
            // Or update them as a range indicator somewhere in the UI.
            phLabel.textContent = `${storedPHMin} - ${storedPHMax}`;
        }
    });

    // Listen for changes made in another tab/window
    window.addEventListener("storage", function (event) {
        if (event.key === "sensorLevel") {
            const waterLabel = document.querySelector('.arc-gauge .percentage');
            waterLabel.textContent = event.newValue;
        }
        if (event.key === "phMin" || event.key === "phMax") {
            const storedPHMin = localStorage.getItem("phMin");
            const storedPHMax = localStorage.getItem("phMax");
            const phLabel = document.querySelector('.arc-gauge-ph .percentage');
            phLabel.textContent = `${storedPHMin} - ${storedPHMax}`;
        }
    });

    // Email Registration Form Handling
    const emailForm = document.getElementById('email-registration-form');
    const emailInput = document.getElementById('notification-email');
    const emailNotification = document.getElementById('email-notification');

    if (emailForm) {
        emailForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const email = emailInput.value.trim();

            if (!email) {
                showEmailNotification('Please enter a valid email address', 'error');
                return;
            }

            // Create form data for submission
            const formData = new FormData();
            formData.append('email', email);

            // Submit the email registration
            fetch('/register_email', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showEmailNotification(data.message, 'success');
                        emailInput.value = ''; // Clear the input field
                    } else {
                        showEmailNotification(data.message, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error registering email:', error);
                    showEmailNotification('An error occurred. Please try again.', 'error');
                });
        });
    }

    function showEmailNotification(message, type) {
        emailNotification.textContent = message;
        emailNotification.className = `email-notification ${type}`;
        emailNotification.style.display = 'block';

        // Hide the notification after 5 seconds
        setTimeout(() => {
            emailNotification.style.display = 'none';
        }, 5000);
    }
});

document.addEventListener('DOMContentLoaded', function () {
    // Initialize variables to store available videos
    let availableVideos = {
        cam1: {},
        cam2: {}
    };

    // Initialize date picker with range selection enabled
    const timelapseDate = flatpickr('#timelapseDate', {
        mode: 'range',
        dateFormat: 'Y-m-d',
        disableMobile: true,
        maxDate: 'today',
        onOpen: (selectedDates, dateStr, instance) => {
            instance.calendarContainer.classList.add('centered-popup');
        },
        onClose: (selectedDates, dateStr, instance) => {
            instance.calendarContainer.classList.remove('centered-popup');
            if (dateStr) {
                loadVideosForDateRange(selectedDates);
            }
        },
        onChange: (selectedDates, dateStr) => {
            if (dateStr) {
                loadVideosForDateRange(selectedDates);
            }
        }
    });

    // Function to load videos for a specific date or range of dates
    function loadVideosForDateRange(dates) {
        const video1 = document.getElementById('timelapse-video-cam1');
        const video2 = document.getElementById('timelapse-video-cam2');

        // Clear existing video sources
        video1.innerHTML = '';
        video2.innerHTML = '';

        // If a single date is selected
        if (dates.length === 1) {
            const date = dates[0].toISOString().split('T')[0];
            loadVideoForDate(date, video1, 'cam1');
            loadVideoForDate(date, video2, 'cam2');
        }
        // If a range of dates is selected
        else if (dates.length === 2) {
            const startDate = dates[0];
            const endDate = dates[1];
            const dateList = [];

            let currentDate = new Date(startDate);
            while (currentDate <= endDate) {
                dateList.push(new Date(currentDate));
                currentDate.setDate(currentDate.getDate() + 1);
            }

            playVideosSequentially(dateList, video1, video2);
        }
    }

    // Function to load video for a specific date and camera
    function loadVideoForDate(date, videoElement, camera) {
        const videoName = `timelapse_${date}.mp4`;
        const timestamp = new Date().getTime(); // cache busting
        const source = document.createElement('source');
        source.src = `/static/${camera}/${videoName}?t=${timestamp}`;
        source.type = 'video/mp4';
        videoElement.innerHTML = ''; // Clear previous sources
        videoElement.appendChild(source);
        videoElement.load();
    }

    // Function to play videos sequentially for a range of dates
    function playVideosSequentially(dateList, video1, video2) {
        let currentIndex = 0;

        function loadAndPlayNext() {
            if (currentIndex < dateList.length) {
                const date = dateList[currentIndex].toISOString().split('T')[0];
                loadVideoForDate(date, video1, 'cam1');
                loadVideoForDate(date, video2, 'cam2');

                video1.onended = video2.onended = () => {
                    currentIndex++;
                    loadAndPlayNext();
                };

                video1.play();
                video2.play();
            }
        }

        loadAndPlayNext();
    }
});

// Function to extract date from filename
function extractDateFromFilename(filename) {
    const dateMatch = filename.match(/timelapse_(\d{4}-\d{2}-\d{2})/);
    if (dateMatch) {
        return dateMatch[1];
    }
    return null;
}

// Synchronize play/pause actions between both videos
const video1 = document.getElementById('timelapse-video-cam1');
const video2 = document.getElementById('timelapse-video-cam2');

video1.addEventListener('play', () => {
    video2.play();
});

video1.addEventListener('pause', () => {
    video2.pause();
});

video2.addEventListener('play', () => {
    video1.play();
});

video2.addEventListener('pause', () => {
    video1.pause();
});

// Load videos when the timelapse tab is activated
document.querySelectorAll('.tabs a').forEach((tab) => {
    tab.addEventListener('click', (e) => {
        if (tab.getAttribute('href') === "#timelapse") {
            loadTimelapseVideos();
        }
    });
});

// If timelapse tab is active on page load, load the videos
if (document.querySelector('.tabs a[href="#timelapse"]').classList.contains('active')) {
    loadTimelapseVideos();
}