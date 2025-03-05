import threading
import time
import datetime
import csv
import io
import os
import traceback
import random

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
app.secret_key = 'supersecretkey123'  # Needed for session management

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
            return read_ph()
        except Exception as e:
            print(f"Error reading pH: {e}")
            return 7.0
    else:
        # Simulated pH value
        return round(random.uniform(6.0, 8.0), 1)

def get_water_reading():
    if water_sensor_available:
        try:
            _, cycle_low = record_water_cycle()
            return cycle_low
        except Exception as e:
            print(f"Error reading water level: {e}")
            return 50.0
    else:
        # Simulated water level
        return round(random.uniform(40.0, 80.0), 1)

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
    return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfe\xfe(\xa2\x8a\x00\xff\xd9'

def gen_frames():
    if camera_available and cv2_available and camera:
        while True:
            try:
                im = camera.capture_array()
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

# Flask Routes
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/ph_data')
def ph_data():
    ph_value = get_ph_reading()
    return jsonify({'ph': float(ph_value)})

@app.route('/water_data')
def water_data():
    water_value = get_water_reading()
    return jsonify({'water': float(water_value)})

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/sensor_history')
def sensor_history():
    return render_template('sensor_history.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('authenticated'):
        return render_template('settings.html')
    
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'aerotower123':
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
                
                # Write to CSV
                try:
                    with open('ph_hourly.csv', 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([
                            next_hour.strftime('%Y-%m-%d'),
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
        with open('ph_hourly.csv', 'r') as csvfile:
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
        with open('ph_hourly.csv', 'r') as csvfile:
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

# Main Execution
if __name__ == '__main__':
    print("Aeroponic Tower Garden Website Starting...")
    print(f"Hardware status: " + 
          f"Camera={'Available' if camera_available else 'Unavailable'}, " +
          f"pH Sensor={'Available' if ph_sensor_available else 'Unavailable'}, " +
          f"Water Sensor={'Available' if water_sensor_available else 'Unavailable'}")
    
    # Ensure CSV file exists with headers if it doesn't
    try:
        with open('ph_hourly.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Check if file is empty, if so, write headers
            csvfile.seek(0, os.SEEK_END)
            if csvfile.tell() == 0:
                writer.writerow(["Date", "Time", "pH", "Water Level (%)"])
    except Exception as e:
        print(f"Error preparing CSV file: {e}")
    
    # Start the background sensor logger thread
    logger_thread = threading.Thread(target=background_sensor_logger, daemon=True)
    logger_thread.start()
    
    try:
        # Start the Flask app
        app.run(host="0.0.0.0", port=5000, debug=False)
    finally:
        # Cleanup GPIO if used
        if GPIO:
            GPIO.cleanup()