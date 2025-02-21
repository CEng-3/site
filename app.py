from flask import Flask, Response, render_template, request, session, redirect, url_for, jsonify
from picamera2 import Picamera2
from PH_read import read_ph
import io, time, cv2, threading, datetime, csv


app = Flask(__name__)
app.secret_key = 'supersecretkey123'  # Needed for session management

# Camera configuration
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

        time.sleep(0.2)  # Delay to control frame rate

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/ph_data')  # Change endpoint to match frontend
def ph_data():
    ph_value = read_ph()
    return jsonify({'ph': float(ph_value)})  # Proper JSON object

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
        # Wait 5 minutes between readings
        time.sleep(300)
        ph_value = read_ph()
        readings.append(ph_value)
        print(f"Recorded pH: {ph_value} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check if we've reached (or passed) the next hour boundary
        now = datetime.datetime.now()
        if now >= next_hour:
            if readings:
                avg_ph = sum(readings) / len(readings)
            else:
                avg_ph = 0.0  # Default if no readings (should not occur)
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

if __name__ == '__main__':
    print(app.url_map)
    logger_thread = threading.Thread(target=background_ph_logger, daemon=True)
    logger_thread.start()
    app.run(host="0.0.0.0", port=5000, debug=False)

