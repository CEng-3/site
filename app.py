import threading
import time
import datetime
import csv
import io
import os
import traceback
import random
import socket
import pickle
import struct
import smtplib
import hashlib

import authentication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Flask, Response, render_template, request, session, redirect, url_for, jsonify

# Hardware libraries with fallback
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("GPIO library not available. Running without GPIO control.")
    GPIO = None

try:
    from picamera2 import Picamera2
    camera_available = True
except Exception as e:
    print(f"Camera initialization failed: {e}")
    camera_available = False

try:
    from PH_read import read_ph
    ph_sensor_available = True
except Exception as e:
    print(f"pH sensor initialization failed: {e}")
    ph_sensor_available = False

# OpenCV for image processing with fallback
try:
    import cv2
    cv2_available = True
except ImportError:
    print("OpenCV not available. Using basic image handling.")
    cv2_available = False

# Try to import water level module
try:
    from water_level import record_water_cycle
    water_sensor_available = True
except Exception as e:
    print(f"Water level sensor initialization failed: {e}")
    water_sensor_available = False

app = Flask(__name__)
app.secret_key = authentication.get_secret_key()

# Camera setup
camera = None
if camera_available:
    try:
        camera = Picamera2()
        camera.preview_configuration.main.size = (640, 480)
        camera.preview_configuration.main.format = "RGB888"
        camera.preview_configuration.align()
        camera.configure("preview")
        camera.start()
    except Exception as e:
        print(f"Camera initialization error: {e}")
        camera = None

# LED Configuration
LED_PIN = 26
if GPIO:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_PIN, GPIO.OUT)

# Fallback functions
def get_ph_reading():
    if ph_sensor_available:
        try:
            ph_value = read_ph()
            # Check for negative values or values over 14 and use previous value if needed
            if ph_value < 0 or ph_value > 14:
                previous_readings = get_latest_readings()
                ph_value = previous_readings['ph']
            return ph_value
        except Exception as e:
            print(f"Error reading pH: {e}")
            return 7.0
    else:
        # Simulated pH value
        return round(random.uniform(6.0, 8.0), 1)

def get_water_reading():
    if water_sensor_available:
        try:
            cycle_low = record_water_cycle()  # Now receives single value
            return int(cycle_low)
        except Exception as e:
            print(f"Error reading water level: {e}")
            return 50
    else:
        # Simulated water level
        return round(random.uniform(40.0, 80.0))

def get_fallback_frame():
    """Return a fallback image when camera is unavailable"""
    fallback_path = 'static/camera_fallback.jpg'
    
    try:
        if cv2_available and os.path.exists(fallback_path):
            img = cv2.imread(fallback_path)
            _, buffer = cv2.imencode('.jpg', img)
            return buffer.tobytes()
    except Exception as e:
        print(f"Error loading fallback image: {e}")
    
    # Minimal valid JPEG if all else fails
    return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfe\xfe(\xa2\x8a\x00\xff\xd9'

def gen_frames():
    if camera_available and cv2_available and camera:
        while True:
            try:
                im = camera.capture_array()
                im = cv2.flip(im, -1) # Flip image vertically
                _, buffer = cv2.imencode('.jpg', im)
                frame = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       frame + b'\r\n')
            except Exception as e:
                print(f"Error capturing frame: {e}")
                # Yield fallback frame on error
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       get_fallback_frame() + b'\r\n')
            
            time.sleep(0.2)  # Control frame rate
    else:
        # Fallback mode - generate a static test pattern
        while True:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   get_fallback_frame() + b'\r\n')
            time.sleep(0.2)

def receive_frames():
    """Connect to Pi B and receive the camera feed."""
    PI_B_IP = "192.168.64.120"
    PORT = 4050
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((PI_B_IP, PORT))
        
        data = b""
        payload_size = struct.calcsize("Q")
        
        while True:
            try:
                while len(data) < payload_size:
                    packet = client_socket.recv(4096)
                    if not packet:
                        raise ConnectionError("Disconnected from Pi B")
                    data += packet
                
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]
                
                while len(data) < msg_size:
                    data += client_socket.recv(4096)
                
                frame_data = data[:msg_size]
                data = data[msg_size:]
                
                frame = pickle.loads(frame_data)
                _, buffer = cv2.imencode('.jpg', frame)
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       buffer.tobytes() + b'\r\n')
                
            except Exception as e:
                print(f"Error receiving frame: {e}")
                client_socket.close()
                # Reconnect
                time.sleep(1)
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(5)
                client_socket.connect((PI_B_IP, PORT))
                data = b""
                
    except Exception as e:
        print(f"[WARNING] Failed to connect to Pi B: {e}")
        while True:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   get_fallback_frame() + b'\r\n')
            time.sleep(0.2)            

# Flask Routes
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/ph_data')
def ph_data():
    ph_value = get_ph_reading()
    # Ensure the pH value is not negative
    if ph_value < 0:
        previous_readings = get_latest_readings()
        ph_value = previous_readings['ph']
    # Get the current water level to save both values
    water_value = get_water_reading()
    save_latest_readings(ph_value, water_value)
    return jsonify({'ph': float(ph_value)})

@app.route('/water_data')
def water_data():
    water_value = get_water_reading()
    # Get the current pH value to save both values
    ph_value = get_ph_reading()
    save_latest_readings(ph_value, water_value)
    return jsonify({'water': float(water_value)})

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_pi_b')
def video_feed_pi_b():
    return Response(receive_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/sensor_history')
def sensor_history():
    return render_template('sensor_history.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('authenticated'):
        return render_template('settings.html')
    
    if request.method == 'POST':
        password = request.form.get('password')
        hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Hash the inputted password
        stored_password_hash = authentication.get_password_hash()  # Get the stored hashed password
        
        if hashed_password == stored_password_hash:  # Compare the hashes
            session['authenticated'] = True
            return redirect(url_for('settings'))
        else:
            return render_template('login.html', error='Incorrect password')
    
    return render_template('login.html')

@app.route('/flashLED', methods=['POST'])
def flash_led():
    if GPIO:
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(LED_PIN, GPIO.LOW)
        return "LED flashed", 200
    return "GPIO not available", 500

@app.route('/timelapse_list')  # Note the change in route name
def timelapse_list():
    camera = request.args.get('camera', 'cam1')
    if camera == 'cam1':
        timelapse_dir = 'static/videos/pi'
    elif camera == 'cam2':
        timelapse_dir = 'static/videos/pi_'
    else:
        return jsonify([])

    # Ensure we only get valid MP4 files
    video_files = [f for f in os.listdir(timelapse_dir) if f.endswith('.mp4')]
    return jsonify(video_files)

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('index'))

# Data Logging and CSV Handling
global_lock = threading.Lock()
readings = []
water_levels = []
next_hour = datetime.datetime.now().replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)

def background_sensor_logger():
    global readings, water_levels, next_hour
    
    while True:
        try:
            # Wait 5 minutes between readings
            time.sleep(300)
            
            # Get sensor readings
            ph_value = get_ph_reading()
            water_value = get_water_reading()
            
            with global_lock:
                readings.append(ph_value)
                water_levels.append(water_value)
            
            print(f"Recorded pH: {ph_value}, Water: {water_value} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check if we've reached (or passed) the next hour boundary
            now = datetime.datetime.now()
            if now >= next_hour:
                with global_lock:
                    avg_ph = sum(readings) / len(readings) if readings else 7.0
                    min_water = min(water_levels) if water_levels else 50.0
                    readings.clear()
                    water_levels.clear()
                
                # Write to CSV with the corrected date format: DD-MM-YYYY
                try:
                    with open('static/data/ph_hourly.csv', 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([
                            next_hour.strftime('%d-%m-%Y'),  # Changed from '%Y-%m-%d' to '%d-%m-%Y'
                            next_hour.strftime('%H:%M:%S'),
                            f"{avg_ph:.1f}",
                            f"{min_water:.1f}"
                        ])
                    print(f"Logged data for {next_hour.strftime('%H:%M:%S')}: pH={avg_ph:.1f}, Water={min_water:.1f}")
                except Exception as e:
                    print(f"Error logging data: {e}")
                
                next_hour += datetime.timedelta(hours=1)
        
        except Exception as e:
            print(f"Error in sensor logger: {e}")
            traceback.print_exc()
            time.sleep(60)

# CSV Data Retrieval and Download Routes
@app.route('/get_csv_data')
def get_csv_data():
    filter_val = request.args.get('filter', 'today')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    data = []
    today = datetime.date.today()
    
    try:
        with open('static/data/ph_hourly.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)  # Use DictReader for more robust parsing
            for row in reader:
                rec_date = datetime.datetime.strptime(row['Date'], '%d-%m-%Y').date()
                
                # Filtering logic
                if (filter_val == 'today' and rec_date == today) or \
                   (filter_val == 'yesterday' and rec_date == (today - datetime.timedelta(days=1))) or \
                   (filter_val == 'this_month' and rec_date.year == today.year and rec_date.month == today.month) or \
                   (filter_val == 'custom' and start_date and end_date and 
                    datetime.datetime.strptime(start_date, '%d-%m-%Y').date() <= rec_date <= 
                    datetime.datetime.strptime(end_date, '%d-%m-%Y').date()) or \
                   (filter_val not in ['today', 'yesterday', 'this_month', 'custom']):
                    data.append({
                        'date': row['Date'], 
                        'time': row['Time'], 
                        'ph': row['pH'], 
                        'water': row['Water Level (%)']
                    })
        
        # Ensure we return an array
        return jsonify(data if data else [])
    
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return jsonify([]), 500

@app.route('/download')
def download():
    filter_val = request.args.get('filter', 'today')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    data = []
    today = datetime.date.today()
    
    try:
        with open('static/data/ph_hourly.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)  # Use DictReader to handle headers
            
            for row in reader:
                rec_date = datetime.datetime.strptime(row['Date'], '%d-%m-%Y').date()
                
                # Filtering logic
                if (filter_val == 'today' and rec_date == today) or \
                   (filter_val == 'yesterday' and rec_date == (today - datetime.timedelta(days=1))) or \
                   (filter_val == 'this_month' and rec_date.year == today.year and rec_date.month == today.month) or \
                   (filter_val == 'custom' and start_date and end_date and 
                    datetime.datetime.strptime(start_date, '%d-%m-%Y').date() <= rec_date <= 
                    datetime.datetime.strptime(end_date, '%d-%m-%Y').date()) or \
                   (filter_val not in ['today', 'yesterday', 'this_month', 'custom']):
                    data.append({
                        'date': row['Date'], 
                        'time': row['Time'], 
                        'ph': row['pH'], 
                        'water': row['Water Level (%)']
                    })
    
        # Generate downloadable CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(["Date", "Time", "pH", "Water Level (%)"])
        
        # Write data rows
        for row in data:
            writer.writerow([
                row["date"], 
                row["time"], 
                row["ph"], 
                row["water"]
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            csv_content, 
            mimetype="text/csv", 
            headers={"Content-Disposition": "attachment; filename=filtered_data.csv"}
        )
    
    except Exception as e:
        print(f"Download error: {e}")
        return jsonify({"error": f"Error reading CSV file: {str(e)}"}), 500

# Add these imports at the top with the other imports
import csv
import os

# Add these globals near the other global variables
thresholds_file = 'static/data/thresholds.csv'

# Initialize thresholds with default values
def initialize_thresholds():
    if not os.path.exists(thresholds_file):
        with open(thresholds_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['water_level_threshold', 'ph_min_threshold', 'ph_max_threshold'])
            writer.writerow(['20', '6.0', '7.5'])  # Default values

def get_thresholds():
    try:
        with open(thresholds_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            row = next(reader)
            return {
                'water_level_threshold': float(row[0]),
                'ph_min_threshold': float(row[1]),
                'ph_max_threshold': float(row[2])
            }
    except Exception as e:
        print(f"Error reading thresholds: {e}")
        return {
            'water_level_threshold': 20,
            'ph_min_threshold': 6.0,
            'ph_max_threshold': 7.5
        }

# Add these routes for managing thresholds
@app.route('/get_thresholds')
def get_threshold_values():
    return jsonify(get_thresholds())

@app.route('/save_thresholds', methods=['POST'])
def save_thresholds():
    try:
        data = request.json
        water_threshold = data.get('water_level_threshold', 20)
        ph_min = data.get('ph_min_threshold', 6.0)
        ph_max = data.get('ph_max_threshold', 7.5)
        
        with open(thresholds_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['water_level_threshold', 'ph_min_threshold', 'ph_max_threshold'])
            writer.writerow([water_threshold, ph_min, ph_max])
        
        return jsonify({"status": "success", "message": "Thresholds saved successfully"}), 200
    except Exception as e:
        print(f"Error saving thresholds: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Define the path for the latest readings CSV file
latest_readings_file = 'static/data/latest_readings.csv'

# Function to save the latest sensor readings to CSV
def save_latest_readings(ph_value, water_value):
    try:
        with open(latest_readings_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ph', 'water'])
            writer.writerow([ph_value, water_value])
        print(f"Saved readings: pH={ph_value}, Water={water_value}")
    except Exception as e:
        print(f"Error saving latest readings: {e}")

# Function to get the latest readings from CSV
def get_latest_readings():
    try:
        if os.path.exists(latest_readings_file):
            with open(latest_readings_file, 'r') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip header row
                row = next(reader)  # Get the data row
                ph_value = float(row[0])
                # Ensure we don't return negative pH values
                if ph_value < 0:
                    ph_value = 7.0  # Default to neutral pH if value is negative
                return {
                    'ph': ph_value,
                    'water': float(row[1])
                }
        # Return default values if file doesn't exist or is empty
        return {'ph': 7.0, 'water': 50.0}
    except Exception as e:
        print(f"Error reading latest readings: {e}")
        return {'ph': 7.0, 'water': 50.0}

# Initialize the latest readings file if it doesn't exist
def initialize_latest_readings():
    if not os.path.exists(latest_readings_file):
        save_latest_readings(7.0, 50.0)  # Default values

@app.route('/initial_readings')
def initial_readings():
    return jsonify(get_latest_readings())

# Define the path for the emails CSV file
emails_file = 'static/data/registered_emails.csv'

# Violation tracking variables - update these
water_violations = 0
ph_violations = 0
water_notification_sent = False  # Separate flag for water
ph_notification_sent = False     # Separate flag for pH
last_reset_time = datetime.datetime.now()

# Initialize emails file if it doesn't exist
def initialize_emails_file():
    if not os.path.exists(emails_file):
        with open(emails_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['email'])

# Function to get all registered emails
def get_registered_emails():
    try:
        emails = []
        if os.path.exists(emails_file):
            with open(emails_file, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header row
                for row in reader:
                    if row and row[0].strip():  # Check if row exists and email is not empty
                        emails.append(row[0])
        return emails
    except Exception as e:
        print(f"Error reading emails: {e}")
        return []

# Function to add a new email
def add_email(email):
    try:
        # Check if email already exists
        emails = get_registered_emails()
        if email in emails:
            return False, "Email already registered"
            
        with open(emails_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([email])
        return True, "Email registered successfully"
    except Exception as e:
        print(f"Error adding email: {e}")
        return False, f"Error: {str(e)}"

# Function to remove an email
def remove_email(email):
    try:
        emails = get_registered_emails()
        if email not in emails:
            return False, "Email not found"
            
        # Read all emails
        rows = []
        with open(emails_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Write back all emails except the one to remove
        with open(emails_file, 'w', newline='') as f:
            writer = csv.writer(f)
            for row in rows:
                if not row or row[0] != email:
                    writer.writerow(row)
        
        return True, "Email removed successfully"
    except Exception as e:
        print(f"Error removing email: {e}")
        return False, f"Error: {str(e)}"

# Function to send notification emails
def send_notification_emails(subject, message):
    emails = get_registered_emails()
    if not emails:
        print("No registered emails to notify")
        return False
    
    try:
        # Email configuration - replace with your SMTP details
        smtp_server = "smtp.gmail.com"  # Example for Gmail
        smtp_port = 587
        smtp_username = "tustower@gmail.com"  # Replace with your email
        smtp_password = authentication.get_app_password()  # Use the app password
        
        # Create connection
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Send emails
        for email in emails:
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = smtp_username
                msg['To'] = email
                msg['Subject'] = subject
                
                # Add body to email
                msg.attach(MIMEText(message, 'plain'))
                
                # Send message
                server.send_message(msg)
                print(f"Notification sent to {email}")
                
            except Exception as e:
                print(f"Error sending email to {email}: {e}")
        
        # Close the connection
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send notification emails: {e}")
        traceback.print_exc()
        return False

# Function to check thresholds and track violations - update this function
def check_thresholds_and_notify():
    global water_violations, ph_violations, water_notification_sent, ph_notification_sent, last_reset_time
    
    # Get current readings
    readings = get_latest_readings()
    water_level = readings['water']
    ph_value = readings['ph']
    
    # Get thresholds
    thresholds = get_thresholds()
    water_threshold = thresholds['water_level_threshold']
    ph_min = thresholds['ph_min_threshold']
    ph_max = thresholds['ph_max_threshold']
    
    # Check for water level violations
    if water_level < water_threshold:
        water_violations += 1
        print(f"Water violation #{water_violations} detected: {water_level}% is below threshold {water_threshold}%")
    else:
        water_violations = 0
        # Removed the code that resets water_notification_sent flag
    
    # Check for pH violations
    if ph_value < ph_min or ph_value > ph_max:
        ph_violations += 1
        print(f"pH violation #{ph_violations} detected: {ph_value} is outside range {ph_min}-{ph_max}")
    else:
        ph_violations = 0
        # Removed the code that resets ph_notification_sent flag
    
    # Check if we need to send water notification
    if water_violations == 5 and not water_notification_sent:
        subject = f"ALERT: Water level is {water_level}%"
        message = f"The Water level is below the acceptable threshold.\nThreshold Range: {water_threshold}%\nCurrent water level: {water_level}%\n\nWebsite:\nhttps://tustower.com."
        
        if send_notification_emails(subject, message):
            water_notification_sent = True
            print(f"Water notification emails sent at {datetime.datetime.now()} after exactly 5 consecutive violations")
    
    # Check if we need to send pH notification
    if ph_violations == 5 and not ph_notification_sent:
        subject = f"ALERT: pH is {ph_value}"
        message = f"The pH level has exceeded the acceptable range.\nThreshold Range: {ph_min} - {ph_max}\nCurrent pH: {ph_value}\n\nWebsite:\nhttps://tustower.com"
        
        if send_notification_emails(subject, message):
            ph_notification_sent = True
            print(f"pH notification emails sent at {datetime.datetime.now()} after exactly 5 consecutive violations")
    
    # Reset violations and notification flags every 24 hours
    now = datetime.datetime.now()
    if (now - last_reset_time).days >= 1:
        water_violations = 0
        ph_violations = 0
        water_notification_sent = False
        ph_notification_sent = False
        last_reset_time = now
        print(f"Daily reset of violation counters at {now}")

# Routes for email management
@app.route('/register_email', methods=['POST'])
def register_email():
    try:
        email = request.form.get('email')
        if not email:
            return jsonify({"status": "error", "message": "Email is required"}), 400
            
        success, message = add_email(email)
        if success:
            return jsonify({"status": "success", "message": message}), 200
        else:
            return jsonify({"status": "error", "message": message}), 400
    except Exception as e:
        print(f"Error registering email: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_emails')
def get_emails():
    if not session.get('authenticated'):
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
        
    emails = get_registered_emails()
    return jsonify({"status": "success", "emails": emails}), 200

@app.route('/remove_email', methods=['POST'])
def remove_email_route():
    if not session.get('authenticated'):
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
        
    try:
        email = request.form.get('email')
        if not email:
            return jsonify({"status": "error", "message": "Email is required"}), 400
            
        success, message = remove_email(email)
        if success:
            return jsonify({"status": "success", "message": message}), 200
        else:
            return jsonify({"status": "error", "message": message}), 400
    except Exception as e:
        print(f"Error removing email: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Function to periodically check thresholds and send notifications
def threshold_monitor():
    while True:
        try:
            check_thresholds_and_notify()
        except Exception as e:
            print(f"Error in threshold monitor: {e}")
        
        time.sleep(300)  # Check every minute - this is the delay between checks

# Main Execution
if __name__ == '__main__':
    print("Aeroponic Tower Garden Website Starting...")
    print(f"Hardware status: " + 
          f"Camera={'Available' if camera_available else 'Unavailable'}, " +
          f"pH Sensor={'Available' if ph_sensor_available else 'Unavailable'}, " +
          f"Water Sensor={'Available' if water_sensor_available else 'Unavailable'}")
    
    # Ensure CSV file exists with headers if it doesn't
    try:
        with open('static/data/ph_hourly.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Check if file is empty, if so, write headers
            csvfile.seek(0, os.SEEK_END)
            if csvfile.tell() == 0:
                writer.writerow(["Date", "Time", "pH", "Water Level (%)"])
    except Exception as e:
        print(f"Error preparing CSV file: {e}")
    
    # Initialize thresholds file
    initialize_thresholds()
    
    # Initialize latest readings file
    initialize_latest_readings()
    
    # Initialize emails file
    initialize_emails_file()
    
    # Start the background sensor logger thread
    logger_thread = threading.Thread(target=background_sensor_logger, daemon=True)
    logger_thread.start()
    
    # Start the threshold monitor thread
    threshold_thread = threading.Thread(target=threshold_monitor, daemon=True)
    threshold_thread.start()
    
    try:
        # Start the Flask app
        app.run(host="0.0.0.0", port=5000, debug=False)
    finally:
        # Cleanup GPIO if used
        if GPIO:
            GPIO.cleanup()