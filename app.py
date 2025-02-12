from flask import Flask, Response, render_template, request, session, redirect, url_for
from picamera2 import Picamera2
import io, time, cv2

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

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)