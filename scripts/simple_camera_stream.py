#!/usr/bin/env python3
"""
Simple MJPEG camera stream - no processing, just raw camera feed
Use to test if camera is working properly
"""

import io
import time
import threading
from flask import Flask, Response
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput

app = Flask(__name__)

# Global frame storage
latest_frame = None
frame_lock = threading.Lock()

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

def generate_frames(output):
    """Generate frames for MJPEG stream"""
    while True:
        with output.condition:
            output.condition.wait()
            frame = output.frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    """Simple web page"""
    return '''
    <html>
    <head>
        <title>RPi Camera 3 Test Stream</title>
        <style>
            body { 
                background: #222; 
                color: #fff; 
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 20px;
            }
            img { 
                max-width: 90%; 
                border: 2px solid #444;
                margin: 20px auto;
            }
            h1 { color: #4CAF50; }
            .info {
                background: #333;
                padding: 15px;
                border-radius: 5px;
                display: inline-block;
                margin: 20px;
            }
        </style>
    </head>
    <body>
        <h1>RPi Camera Module 3 - Raw Stream Test</h1>
        <div class="info">
            <p><strong>Resolution:</strong> 640x480</p>
            <p><strong>No processing</strong> - Direct camera output</p>
            <p>Check focus, clarity, and camera health</p>
        </div>
        <img src="/video_feed" alt="Camera Stream">
        <div class="info">
            <p>If you see a clear image, camera is working fine.</p>
            <p>If blurry at 50cm-2m distance, lens may need cleaning.</p>
        </div>
    </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    global output
    return Response(generate_frames(output),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("=" * 60)
    print("RPi Camera Module 3 - Simple Stream Test")
    print("=" * 60)
    
    # Initialize camera
    print("Initializing camera...")
    picam2 = Picamera2()
    
    # Configure for video
    video_config = picam2.create_video_configuration(
        main={"size": (640, 480), "format": "RGB888"},
        controls={"FrameRate": 30}
    )
    picam2.configure(video_config)
    
    print("✓ Camera configured: 640x480 @ 30fps")
    
    # Setup MJPEG encoder
    output = StreamingOutput()
    picam2.start_recording(MJPEGEncoder(), FileOutput(output))
    
    print("✓ Camera started")
    print()
    print("=" * 60)
    print("Stream available at:")
    print("  http://0.0.0.0:5001")
    print("  or")
    print("  http://<your-pi-ip>:5001")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        picam2.stop_recording()
        picam2.close()
        print("✓ Camera closed")
