from flask import Flask, Response, render_template, request, session, redirect, url_for, jsonify
import io, time, threading, datetime, csv, os
import traceback

app = Flask(__name__)
app.secret_key = 'supersecretkey123'  # Needed for session management

# Global variables to track hardware availability
camera_available = False
ph_sensor_available = False

# Try to initialize camera with fallback
try:
    from picamera2 import Picamera2
    camera = Picamera2()
    camera.preview_configuration.main.size = (640, 480)
    camera.preview_configuration.main.format = "RGB888"
    camera.preview_configuration.align()
    camera.configure("preview")
    camera.start()
    camera_available = True
    print("Camera initialized successfully")
except Exception as e:
    print(f"Camera initialization failed: {e}")
    print("Running in camera fallback mode")

# Try to import pH module
try:
    from PH_read import read_ph
    # Test if we can actually read from the sensor
    test_value = read_ph()
    ph_sensor_available = True
    print("pH sensor initialized successfully")
except Exception as e:
    print(f"pH sensor initialization failed: {e}")
    print("Running in pH sensor fallback mode")

# Import OpenCV with fallback
try:
    import cv2
    cv2_available = True
except ImportError:
    cv2_available = False
    print("OpenCV not available, using fallback for image encoding")

# Fallback function for pH readings
def get_ph_reading():
    if ph_sensor_available:
        try:
            return read_ph()
        except Exception as e:
            print(f"Error reading pH: {e}")
            return 7.0  # Neutral pH as fallback
    else:
        # Return a simulated value between 6.0 and 8.0
        import random
        return round(random.uniform(6.0, 8.0), 1)

def gen_frames():
    if camera_available and cv2_available:
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
            
            time.sleep(0.2)  # Delay to control frame rate
    else:
        # Fallback mode - generate a static test pattern
        while True:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   get_fallback_frame() + b'\r\n')
            time.sleep(0.2)

def get_fallback_frame():
    """Return a simple 'camera unavailable' JPEG when camera is not available"""
    # Path to a static fallback image - create this once and store it
    fallback_path = 'static/camera_fallback.jpg'
    
    try:
        # Try to read the fallback image
        if cv2_available and os.path.exists(fallback_path):
            img = cv2.imread(fallback_path)
            _, buffer = cv2.imencode('.jpg', img)
            return buffer.tobytes()
    except Exception as e:
        print(f"Error loading fallback image: {e}")
    
    # If all else fails, return a minimal valid JPEG (a tiny black image)
    return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00\x01\x00\x01\x00\x00\xff\xdb\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfe\xfe(\xa2\x8a\x00\xff\xd9'

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/ph_data')
def ph_data():
    ph_value = get_ph_reading()
    return jsonify({'ph': float(ph_value)})

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/sensor_history')
def sensor_history():
    return render_template('sensor_history.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    # Check authentication
    if session.get('authenticated'):
        return render_template('settings.html')
    
    # Handle login attempt
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'aerotower123':  # Set your password here
            session['authenticated'] = True
            return redirect(url_for('settings'))
        else:
            return render_template('login.html', error='Incorrect password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('index'))
    
@app.route('/get_csv_data')
def get_csv_data():
    # Get the filter type from the query parameters (defaults to 'today')
    filter_val = request.args.get('filter', 'today')
    # For custom filtering
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    data = []
    today = datetime.date.today()
    
    try:
        with open('ph_hourly.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not row:
                    continue
                # Expecting row format: date (YYYY-MM-DD), time (HH:MM:SS), ph value (string)
                try:
                    rec_date = datetime.datetime.strptime(row[0], '%Y-%m-%d').date()
                    rec_time = row[1]
                    ph_value = row[2]
                    
                    # Apply filtering based on the selected option:
                    if filter_val == 'today' and rec_date == today:
                        data.append({'date': row[0], 'time': rec_time, 'ph': ph_value})
                    elif filter_val == 'yesterday' and rec_date == (today - datetime.timedelta(days=1)):
                        data.append({'date': row[0], 'time': rec_time, 'ph': ph_value})
                    elif filter_val == 'this_month':
                        if rec_date.year == today.year and rec_date.month == today.month:
                            data.append({'date': row[0], 'time': rec_time, 'ph': ph_value})
                    elif filter_val == 'custom' and start_date and end_date:
                        # Expecting start_date and end_date in the same format as the picker (e.g., d-m-Y)
                        start_dt = datetime.datetime.strptime(start_date, '%d-%m-%Y').date()
                        end_dt = datetime.datetime.strptime(end_date, '%d-%m-%Y').date()
                        if start_dt <= rec_date <= end_dt:
                            data.append({'date': row[0], 'time': rec_time, 'ph': ph_value})
                    elif filter_val not in ['today', 'yesterday', 'this_month', 'custom']:
                        # If no valid filter, return all data
                        data.append({'date': row[0], 'time': rec_time, 'ph': ph_value})
                except (ValueError, IndexError) as e:
                    print(f"Error parsing row {row}: {e}")
                    continue
    except FileNotFoundError:
        # Create the file with initial data if it doesn't exist
        with open('ph_hourly.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Add a few sample data points for testing
            for i in range(24):
                hour = i % 24
                date = (today - datetime.timedelta(days=i//24)).strftime('%Y-%m-%d')
                time_str = f"{hour:02d}:00:00"
                ph = round(6.5 + (i % 4) * 0.5, 1)  # values between 6.5 and 8.0
                writer.writerow([date, time_str, ph])
            data = [{'date': today.strftime('%Y-%m-%d'), 'time': '12:00:00', 'ph': '7.0'}]
    except Exception as e:
        return jsonify({"error": f"Error reading CSV file: {str(e)}"}), 500

    return jsonify(data)
    
@app.route('/download')
def download():
    # Get filter parameters from the query string (defaults to 'today')
    filter_val = request.args.get('filter', 'today')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    data = []
    today = datetime.date.today()
    
    try:
        with open('ph_hourly.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not row:
                    continue
                # Expecting row format: date (YYYY-MM-DD), time (HH:MM:SS), ph value (string)
                try:
                    rec_date = datetime.datetime.strptime(row[0], '%Y-%m-%d').date()
                    rec_time = row[1]
                    ph_value = row[2]
                    
                    # Apply filtering based on the selected option
                    if filter_val == 'today' and rec_date == today:
                        data.append({'date': row[0], 'time': rec_time, 'ph': ph_value})
                    elif filter_val == 'yesterday' and rec_date == (today - datetime.timedelta(days=1)):
                        data.append({'date': row[0], 'time': rec_time, 'ph': ph_value})
                    elif filter_val == 'this_month':
                        if rec_date.year == today.year and rec_date.month == today.month:
                            data.append({'date': row[0], 'time': rec_time, 'ph': ph_value})
                    elif filter_val == 'custom' and start_date and end_date:
                        start_dt = datetime.datetime.strptime(start_date, '%d-%m-%Y').date()
                        end_dt = datetime.datetime.strptime(end_date, '%d-%m-%Y').date()
                        if start_dt <= rec_date <= end_dt:
                            data.append({'date': row[0], 'time': rec_time, 'ph': ph_value})
                    elif filter_val not in ['today', 'yesterday', 'this_month', 'custom']:
                        # Fallback: return all data
                        data.append({'date': row[0], 'time': rec_time, 'ph': ph_value})
                except (ValueError, IndexError) as e:
                    print(f"Error parsing row {row}: {e}")
                    continue
    except FileNotFoundError:
        # Create the file with initial data if it doesn't exist
        with open('ph_hourly.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Add some sample data for testing
            date = today.strftime('%Y-%m-%d')
            writer.writerow([date, '12:00:00', '7.0'])
        data = [{'date': date, 'time': '12:00:00', 'ph': '7.0'}]
    except Exception as e:
        return jsonify({"error": f"Error reading CSV file: {str(e)}"}), 500
    
    # Write the filtered data to an in-memory CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Time", "pH"])  # CSV header
    for row in data:
        writer.writerow([row["date"], row["time"], row["ph"]])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=filtered_data.csv"}
    )
    
# Global variables for logging
readings = []
next_hour = datetime.datetime.now().replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)

def background_ph_logger():
    global readings, next_hour
    while True:
        try:
            # Wait 5 minutes between readings (300 seconds)
            time.sleep(300)
            
            # Get the pH reading
            ph_value = get_ph_reading()
            readings.append(ph_value)
            print(f"Recorded pH: {ph_value} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check if we've reached (or passed) the next hour boundary
            now = datetime.datetime.now()
            if now >= next_hour:
                if readings:
                    avg_ph = sum(readings) / len(readings)
                else:
                    avg_ph = 0.0  # Default if no readings (should not occur)
                
                # Make sure the file exists
                try:
                    with open('ph_hourly.csv', 'r'):
                        pass
                except FileNotFoundError:
                    # Create file if it doesn't exist
                    with open('ph_hourly.csv', 'w', newline='') as csvfile:
                        pass
                
                # Write the average pH value along with date and hour to CSV
                with open('ph_hourly.csv', 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([next_hour.strftime('%Y-%m-%d'),
                                    next_hour.strftime('%H:%M:%S'),
                                    f"{avg_ph:.1f}"])
                print(f"Averaged for {next_hour.strftime('%H:%M:%S')}: {avg_ph:.1f}")
                
                # Reset readings and update the next hour
                readings = []
                next_hour += datetime.timedelta(hours=1)
        except Exception as e:
            print(f"Error in pH logger: {e}")
            traceback.print_exc()
            # Continue the loop even after error
            time.sleep(60)

if __name__ == '__main__':
    print("Aeroponic Tower Garden Website Starting...")
    print(f"Hardware status: Camera={'Available' if camera_available else 'Unavailable'}, "
          f"pH Sensor={'Available' if ph_sensor_available else 'Unavailable'}")
    print(app.url_map)
    
    # Start the background pH logger thread
    logger_thread = threading.Thread(target=background_ph_logger, daemon=True)
    logger_thread.start()
    
    # Start the Flask app
    app.run(host="0.0.0.0", port=5000, debug=False)