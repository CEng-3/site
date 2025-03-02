# app.py
import threading
import time
import datetime
import csv
import io
import cv2
import RPi.GPIO as GPIO
from flask import Flask, Response, render_template, request, session, redirect, url_for, jsonify
from picamera2 import Picamera2
from PH_read import read_ph
from water_level import record_water_cycle

app = Flask(__name__)
app.secret_key = 'supersecretkey123'  # Needed for session management

# -------------------------
# Camera configuration
# -------------------------
camera = Picamera2()
camera.preview_configuration.main.size = (640, 480)
camera.preview_configuration.main.format = "RGB888"
camera.preview_configuration.align()
camera.configure("preview")
camera.start()

def gen_frames():
    while True:
        im = camera.capture_array()
        _, buffer = cv2.imencode('.jpg', im)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               frame + b'\r\n')
        time.sleep(0.2)  # control frame rate

# -------------------------
# Flask Endpoints
# -------------------------
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/ph_data')
def ph_data():
    ph_value = read_ph()
    return jsonify({'ph': float(ph_value)})

@app.route('/water_data')
def water_data():
    try:
        with open("current_water.txt", "r") as f:
            water = f.read().strip()
        return jsonify({'water': float(water)})
    except Exception as e:
        return jsonify({'water': 0})

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

# Example LED control endpoint:
LED_PIN = 26
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

@app.route('/flashLED', methods=['POST'])
def flash_led():
    GPIO.output(LED_PIN, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(LED_PIN, GPIO.LOW)
    return "LED flashed", 200

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('index'))

@app.route('/get_csv_data')
def get_csv_data():
    filter_val = request.args.get('filter', 'today')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    data = []
    today = datetime.date.today()
    try:
        with open('ph_hourly.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not row: continue
                rec_date = datetime.datetime.strptime(row[0], '%d-%m-%Y').date()
                rec_time = row[1]
                ph_value = row[2]
                water_value = row[3]
                if filter_val == 'today' and rec_date == today:
                    data.append({'date': row[0], 'time': rec_time, 'ph': ph_value, 'water': water_value})
                elif filter_val == 'yesterday' and rec_date == (today - datetime.timedelta(days=1)):
                    data.append({'date': row[0], 'time': rec_time, 'ph': ph_value, 'water': water_value})
                elif filter_val == 'this_month':
                    if rec_date.year == today.year and rec_date.month == today.month:
                        data.append({'date': row[0], 'time': rec_time, 'ph': ph_value, 'water': water_value})
                elif filter_val == 'custom' and start_date and end_date:
                    start_dt = datetime.datetime.strptime(start_date, '%d-%m-%Y').date()
                    end_dt = datetime.datetime.strptime(end_date, '%d-%m-%Y').date()
                    if start_dt <= rec_date <= end_dt:
                        data.append({'date': row[0], 'time': rec_time, 'ph': ph_value, 'water': water_value})
                elif filter_val not in ['today', 'yesterday', 'this_month', 'custom']:
                    data.append({'date': row[0], 'time': rec_time, 'ph': ph_value, 'water': water_value})
    except Exception as e:
        return jsonify({"error": f"Error reading CSV file: {str(e)}"}), 500
    return jsonify(data)

@app.route('/download')
def download():
    filter_val = request.args.get('filter', 'today')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    data = []
    today = datetime.date.today()
    try:
        with open('ph_hourly.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not row: continue
                rec_date = datetime.datetime.strptime(row[0], '%d-%m-%Y').date()
                rec_time = row[1]
                ph_value = row[2]
                water_value = row[3]
                if filter_val == 'today' and rec_date == today:
                    data.append({'date': row[0], 'time': rec_time, 'ph': ph_value, 'water': water_value})
                elif filter_val == 'yesterday' and rec_date == (today - datetime.timedelta(days=1)):
                    data.append({'date': row[0], 'time': rec_time, 'ph': ph_value, 'water': water_value})
                elif filter_val == 'this_month':
                    if rec_date.year == today.year and rec_date.month == today.month:
                        data.append({'date': row[0], 'time': rec_time, 'ph': ph_value, 'water': water_value})
                elif filter_val == 'custom' and start_date and end_date:
                    start_dt = datetime.datetime.strptime(start_date, '%d-%m-%Y').date()
                    end_dt = datetime.datetime.strptime(end_date, '%d-%m-%Y').date()
                    if start_dt <= rec_date <= end_dt:
                        data.append({'date': row[0], 'time': rec_time, 'ph': ph_value, 'water': water_value})
                elif filter_val not in ['today', 'yesterday', 'this_month', 'custom']:
                    data.append({'date': row[0], 'time': rec_time, 'ph': ph_value, 'water': water_value})
    except Exception as e:
        return jsonify({"error": f"Error reading CSV file: {str(e)}"}), 500
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Time", "pH", "Water level (%)"])
    for row in data:
        writer.writerow([row["date"], row["time"], row["ph"], row["water"]])
    csv_content = output.getvalue()
    output.close()
    return Response(csv_content, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=filtered_data.csv"})

# -------------------------
# Background Logging Threads
# -------------------------
# We use separate threads for:
# 1. Reading pH every 5 minutes.
# 2. Running a water sensor cycle (which lasts 5 minutes).
# 3. Every hour, logging the average pH (over that hour) and the lowest water level from all cycles.

from threading import Lock
data_lock = Lock()
ph_readings = []       # List to hold pH values from each 5-minute cycle.
water_lowests = []     # List to hold water cycle lowest measurements.
# Calculate the next whole-hour time for CSV logging.
next_hour = datetime.datetime.now().replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)

def ph_monitor():
    while True:
        time.sleep(300)  # every 5 minutes
        ph_val = read_ph()
        with data_lock:
            ph_readings.append(ph_val)
        print(f"pH reading: {ph_val}")

def water_monitor():
    while True:
        # record_water_cycle() takes about 5 minutes.
        _, cycle_low = record_water_cycle()
        with data_lock:
            water_lowests.append(cycle_low)
        print(f"Water cycle recorded. Lowest = {cycle_low:.1f}%")

def hourly_logger():
    global next_hour
    while True:
        now = datetime.datetime.now()
        if now >= next_hour:
            with data_lock:
                avg_ph = sum(ph_readings) / len(ph_readings) if ph_readings else 0.0
                hour_water_low = min(water_lowests) if water_lowests else 100.0
                # Reset the lists for the new hour.
                ph_readings.clear()
                water_lowests.clear()
            # Write one CSV row with timestamp, average pH, and lowest water level.
            with open('ph_hourly.csv', 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([next_hour.strftime('%d-%m-%Y'),
                                 next_hour.strftime('%H:%M'),
                                 f"{avg_ph:.1f}",
                                 f"{hour_water_low:.1f}"])
            print(f"Logged hourly data for {next_hour.strftime('%H:%M')} -> pH: {avg_ph:.1f}, Water: {hour_water_low:.1f}%")
            next_hour += datetime.timedelta(hours=1)
        time.sleep(10)

# -------------------------
# Start Background Threads and Flask
# -------------------------
if __name__ == '__main__':
    try:
        # Start the monitor threads.
        threading.Thread(target=ph_monitor, daemon=True).start()
        threading.Thread(target=water_monitor, daemon=True).start()
        threading.Thread(target=hourly_logger, daemon=True).start()
        print("Starting Flask app...")
        app.run(host="0.0.0.0", port=5000, debug=False)
    finally:
        GPIO.cleanup()

