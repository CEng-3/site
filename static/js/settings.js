// ----------------- Water Level Gauge ----------------- //
function updateGauge() {
  const gaugeSVG = document.querySelector('.arc-gauge');
  const progressPath = gaugeSVG.querySelector('.progress');
  const percentageText = gaugeSVG.querySelector('.percentage');
  const totalArcLength = 160.57;

  fetch('/water_data')
    .then(response => response.json())
    .then(data => {
      const sensorPercentage = parseFloat(data.water) || 0;
      const offset = totalArcLength - (sensorPercentage / 100) * totalArcLength;
      progressPath.style.strokeDashoffset = offset.toFixed(2);
      percentageText.textContent = sensorPercentage.toFixed(0) + '%';

      // Update water threshold input
      const sensorLevelInput = document.getElementById("sensor-level");
      if (sensorLevelInput) {
        sensorLevelInput.value = sensorPercentage.toFixed(0) + '%';
      }
    })
    .catch(error => console.error('Error fetching water data:', error));
}

// Animate tank fill
function fillTank() {
  const button = document.getElementById("fillTankButton");
  button.disabled = true;
  const gaugeSVG = document.querySelector('.arc-gauge');
  const progressPath = gaugeSVG.querySelector('.progress');
  const percentageText = gaugeSVG.querySelector('.percentage');
  const totalArcLength = 160.57;
  let currentValue = parseFloat(percentageText.textContent) || 0;
  const targetValue = 100;

  const ledInterval = setInterval(() => {
    fetch('/flashLED', { method: 'POST' })
      .then(response => response.text())
      .then(data => console.log("LED flashed:", data))
      .catch(error => console.error("Error flashing LED:", error));
  }, 500);

  const fillInterval = setInterval(() => {
    if (currentValue < targetValue) {
      currentValue++;
      const offset = totalArcLength - (currentValue / 100) * totalArcLength;
      progressPath.style.strokeDashoffset = offset.toFixed(2);
      percentageText.textContent = currentValue.toFixed(0) + '%';
      const sensorLevelInput = document.getElementById("sensor-level");
      if (sensorLevelInput) {
        sensorLevelInput.value = currentValue.toFixed(0) + '%';
      }
    } else {
      clearInterval(fillInterval);
      clearInterval(ledInterval);
      button.disabled = false;
    }
  }, 50);
}

// Function to load thresholds from the server
function loadThresholds() {
  fetch('/get_thresholds')
    .then(response => response.json())
    .then(data => {
      // Update water level threshold
      const sensorLevelInput = document.getElementById("sensor-level");
      if (sensorLevelInput) {
        sensorLevelInput.value = data.water_level_threshold + "%";
      }

      // Update pH thresholds
      const phMinInput = document.getElementById("ph-min");
      if (phMinInput) {
        phMinInput.value = data.ph_min_threshold.toFixed(1);
      }

      const phMaxInput = document.getElementById("ph-max");
      if (phMaxInput) {
        phMaxInput.value = data.ph_max_threshold.toFixed(1);
      }
    })
    .catch(error => console.error('Error fetching thresholds:', error));
}

// Function to save thresholds to server
function saveThresholds() {
  // Parse values from inputs
  const waterThreshold = parseFloat(document.getElementById("sensor-level").value) || 20;
  const phMinThreshold = parseFloat(document.getElementById("ph-min").value) || 6.0;
  const phMaxThreshold = parseFloat(document.getElementById("ph-max").value) || 7.5;

  // Send to server
  fetch('/save_thresholds', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      water_level_threshold: waterThreshold,
      ph_min_threshold: phMinThreshold,
      ph_max_threshold: phMaxThreshold
    })
  })
    .then(response => response.json())
    .then(data => {
      if (data.status !== "success") {
        alert("Error saving thresholds: " + data.message);
      }
    })
    .catch(error => {
      console.error('Error saving thresholds:', error);
      alert("Error saving thresholds. Please try again.");
    });
}
document.addEventListener("DOMContentLoaded", function () {

  // Existing code to load thresholds and other configurations
  loadThresholds();

  // Modify existing event listeners to save thresholds to server
  document.getElementById("decrement-btn").addEventListener("click", function () {
    const sensorLevelInput = document.getElementById("sensor-level");
    let currentValue = parseFloat(sensorLevelInput.value) || 0;
    if (currentValue > 0) {
      currentValue--;
      sensorLevelInput.value = currentValue + '%';

      // Save thresholds after changing
      saveThresholds();
    }
  });

  document.getElementById("increment-btn").addEventListener("click", function () {
    const sensorLevelInput = document.getElementById("sensor-level");
    let currentValue = parseFloat(sensorLevelInput.value) || 0;
    if (currentValue < 100) {
      currentValue++;
      sensorLevelInput.value = currentValue + '%';

      // Save thresholds after changing
      saveThresholds();
    }
  });

  // Similarly for pH thresholds:
  document.getElementById("decrement-ph-min").addEventListener("click", function () {
    const phMinInput = document.getElementById("ph-min");
    let currentValue = parseFloat(phMinInput.value) || 0;
    currentValue = Math.max(0, currentValue - 0.1);
    phMinInput.value = currentValue.toFixed(1);

    // Save thresholds after changing
    saveThresholds();
  });
  document.getElementById("increment-ph-min").addEventListener("click", function () {
    const phMinInput = document.getElementById("ph-min");
    let currentValue = parseFloat(phMinInput.value) || 0;
    currentValue += 0.1;
    phMinInput.value = currentValue.toFixed(1);

    // Save thresholds after changing
    saveThresholds();
  });
  document.getElementById("decrement-ph-max").addEventListener("click", function () {
    const phMaxInput = document.getElementById("ph-max");
    let currentValue = parseFloat(phMaxInput.value) || 0;
    currentValue = Math.max(0, currentValue - 0.1);
    phMaxInput.value = currentValue.toFixed(1);

    // Save thresholds after changing
    saveThresholds();
  });
  document.getElementById("increment-ph-max").addEventListener("click", function () {
    const phMaxInput = document.getElementById("ph-max");
    let currentValue = parseFloat(phMaxInput.value) || 0;
    currentValue += 0.1;
    phMaxInput.value = currentValue.toFixed(1);

    // Save thresholds after changing
    saveThresholds();
  });

  // Add event listener for the Fill Tank button
  document.getElementById("fillTankButton").addEventListener("click", function () {
    fillTank();
  });

  // Initialize gauge on page load
  updateGauge();

  // Update gauge periodically
  setInterval(updateGauge, 10000);
});

// Email Management Functions
document.addEventListener('DOMContentLoaded', function () {
  // Load registered emails
  loadRegisteredEmails();

  // Function to load registered emails
  function loadRegisteredEmails() {
    fetch('/get_emails')
      .then(response => response.json())
      .then(data => {
        const emailListContainer = document.getElementById('email-list');

        if (data.status === 'success' && Array.isArray(data.emails)) {
          if (data.emails.length > 0) {
            // Display emails
            emailListContainer.innerHTML = '';
            data.emails.forEach(email => {
              const emailItem = document.createElement('div');
              emailItem.className = 'email-item';

              const emailText = document.createElement('div'); // Changed back to div for better block layout
              emailText.className = 'email-text';
              emailText.textContent = email;

              const removeButton = document.createElement('button');
              removeButton.className = 'remove-email';
              removeButton.textContent = 'Remove';
              removeButton.setAttribute('data-email', email);
              removeButton.addEventListener('click', function () {
                removeEmail(email);
              });

              emailItem.appendChild(emailText);
              emailItem.appendChild(removeButton);
              emailListContainer.appendChild(emailItem);
            });
          } else {
            // No emails registered
            emailListContainer.innerHTML = '<div class="no-emails">No emails registered for alerts.</div>';
          }
        } else {
          // Error loading emails
          emailListContainer.innerHTML = '<div class="no-emails">Error loading registered emails.</div>';
        }
      })
      .catch(error => {
        console.error('Error loading emails:', error);
        const emailListContainer = document.getElementById('email-list');
        emailListContainer.innerHTML = '<div class="no-emails">Error loading registered emails. Please try again.</div>';
      });
  }
  // Function to remove an email
  function removeEmail(email) {
    if (!confirm(`Are you sure you want to remove ${email}?`)) {
      return;
    }

    const formData = new FormData();
    formData.append('email', email);

    fetch('/remove_email', {
      method: 'POST',
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          // Success - just refresh the email list without showing an alert
          loadRegisteredEmails();
        } else {
          // Still show error messages
          alert('Error: ' + data.message);
        }
      })
      .catch(error => {
        console.error('Error removing email:', error);
        alert('An error occurred while removing the email. Please try again.');
      });
  }
});