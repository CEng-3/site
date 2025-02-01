1. Create a directory
```
mkdir flask-site
```
2. Create a virtual environment
```
python3 -m venv venv
```
3. Activate virtual environment
```
source venv/bin/activate
```
4. Install Python libraries
```
pip install flask
```
5. Install system libraries
```
sudo apt-get install -y python3-opencv
```
6. Create symbolic link
```
cd venv/lib/python3*/site-packages/
ln -s /usr/lib/python3/dist-packages/cv2.* .
```
7. Run website
```
python3 app.py
```

Visit localhost:5000 in Chromium