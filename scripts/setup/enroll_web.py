#!/usr/bin/env python3
"""
Web-Based Face Enrollment for Deep Learning
============================================

Live browser interface with visual guidance for capturing enrollment photos.
Shows camera feed and instructions for each pose.

Usage:
    sudo python3 scripts/setup/enroll_web.py --name "Achuthan"
    
Then open: http://optimus:5001
"""

import argparse
import time
import sys
import os
from pathlib import Path
from picamera2 import Picamera2
import cv2
import threading
from flask import Flask, Response, render_template_string

# Flask app
app = Flask(__name__)

# Global state
current_frame = None
current_instruction = "Initializing..."
photo_count = 0
total_photos = 0
frame_lock = threading.Lock()
capture_mode = False

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Face Enrollment - {{name}}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            max-width: 900px;
            width: 100%;
        }
        h1 {
            text-align: center;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            text-align: center;
            opacity: 0.9;
            margin-bottom: 30px;
        }
        .video-container {
            position: relative;
            background: black;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }
        #video {
            width: 100%;
            height: auto;
            display: block;
        }
        .overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.8));
            padding: 20px;
            text-align: center;
        }
        .instruction {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        .progress {
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
            height: 30px;
            overflow: hidden;
            margin: 20px 0;
        }
        .progress-bar {
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            height: 100%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        .info-box {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        .tips {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .tip {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid #4facfe;
        }
        .tip-title {
            font-weight: bold;
            margin-bottom: 5px;
            color: #4facfe;
        }
        button {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 5px 20px rgba(79, 172, 254, 0.4);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 7px 25px rgba(79, 172, 254, 0.6);
        }
        button:active {
            transform: translateY(0);
        }
        .button-container {
            text-align: center;
            margin-top: 20px;
        }
        .status {
            text-align: center;
            font-size: 18px;
            margin-top: 20px;
            padding: 15px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .capturing {
            animation: pulse 1s infinite;
        }
    </style>
    <script>
        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('instruction').textContent = data.instruction;
                    document.getElementById('photo-count').textContent = data.photo_count;
                    document.getElementById('total-photos').textContent = data.total_photos;
                    
                    const progress = (data.photo_count / data.total_photos) * 100;
                    document.getElementById('progress-bar').style.width = progress + '%';
                    document.getElementById('progress-text').textContent = Math.round(progress) + '%';
                    
                    if (data.capture_mode) {
                        document.getElementById('overlay').classList.add('capturing');
                    } else {
                        document.getElementById('overlay').classList.remove('capturing');
                    }
                });
        }
        
        function startCapture() {
            fetch('/start_capture', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('start-button').disabled = true;
                        document.getElementById('start-button').textContent = 'Capturing...';
                    }
                });
        }
        
        setInterval(updateStatus, 500);
        window.onload = updateStatus;
    </script>
</head>
<body>
    <div class="container">
        <h1>🎯 Face Enrollment</h1>
        <p class="subtitle">Enrolling: <strong>{{name}}</strong></p>
        
        <div class="info-box">
            <h3>📋 Tips for Best Recognition:</h3>
            <div class="tips">
                <div class="tip">
                    <div class="tip-title">💡 Lighting</div>
                    Good, even lighting on your face
                </div>
                <div class="tip">
                    <div class="tip-title">📏 Distance</div>
                    Stand 50cm - 1m from camera
                </div>
                <div class="tip">
                    <div class="tip-title">👁️ Look at Camera</div>
                    Face the camera directly
                </div>
                <div class="tip">
                    <div class="tip-title">😊 Natural</div>
                    Relax and be yourself
                </div>
            </div>
        </div>
        
        <div class="video-container">
            <img id="video" src="/video_feed" alt="Camera Feed">
            <div class="overlay" id="overlay">
                <div class="instruction" id="instruction">{{instruction}}</div>
            </div>
        </div>
        
        <div class="progress">
            <div class="progress-bar" id="progress-bar" style="width: 0%;">
                <span id="progress-text">0%</span>
            </div>
        </div>
        
        <div class="status">
            <strong>Photos Captured:</strong> <span id="photo-count">0</span> / <span id="total-photos">0</span>
        </div>
        
        <div class="button-container">
            <button id="start-button" onclick="startCapture()">🚀 Start Enrollment</button>
        </div>
    </div>
</body>
</html>
"""

def generate_frames():
    """Generator for streaming frames"""
    global current_frame, frame_lock
    
    while True:
        with frame_lock:
            if current_frame is None:
                time.sleep(0.1)
                continue
            frame = current_frame.copy()
        
        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)  # ~30 fps

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
                                 name=app.config['NAME'],
                                 instruction=current_instruction)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return {
        'instruction': current_instruction,
        'photo_count': photo_count,
        'total_photos': total_photos,
        'capture_mode': capture_mode
    }

@app.route('/start_capture', methods=['POST'])
def start_capture():
    global capture_mode
    capture_mode = True
    return {'success': True}

def capture_thread(name, output_dir):
    """Background thread for capturing photos"""
    global current_frame, current_instruction, photo_count, total_photos, frame_lock, capture_mode
    
    # Initialize camera
    current_instruction = "Initializing camera..."
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (1536, 864), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()
    time.sleep(2)
    
    current_instruction = "Ready! Click 'Start Enrollment' button"
    
    # Capture instructions
    instructions = [
        ("Look straight at camera (neutral)", 3),
        ("Look straight with a smile", 2),
        ("Turn head slightly LEFT", 2),
        ("Turn head slightly RIGHT", 2),
        ("Tilt head slightly UP", 2),
        ("Tilt head slightly DOWN", 2),
        ("Move CLOSER to camera", 2),
        ("Move FARTHER from camera", 2),
        ("Tilt head to LEFT shoulder", 1),
        ("Tilt head to RIGHT shoulder", 1),
    ]
    
    total_photos = sum(num for _, num in instructions)
    
    # Update preview continuously
    def preview_loop():
        global current_frame, frame_lock
        while True:
            frame = picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            with frame_lock:
                current_frame = frame_bgr
            time.sleep(0.033)
    
    preview_thread = threading.Thread(target=preview_loop, daemon=True)
    preview_thread.start()
    
    # Wait for start signal
    while not capture_mode:
        time.sleep(0.1)
    
    # Start capturing
    for instruction_text, num_photos in instructions:
        current_instruction = f"GET READY: {instruction_text}"
        
        # Countdown
        for i in range(3, 0, -1):
            current_instruction = f"{instruction_text} - {i}..."
            time.sleep(1)
        
        # Capture photos
        for i in range(num_photos):
            current_instruction = f"CAPTURING: {instruction_text}"
            
            frame = picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Save photo
            timestamp = int(time.time() * 1000)
            filename = f"{name}_{timestamp}_{photo_count:03d}.jpg"
            filepath = output_dir / filename
            
            cv2.imwrite(str(filepath), frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
            photo_count += 1
            
            print(f"✓ Captured: {filename}")
            
            if i < num_photos - 1:
                time.sleep(0.5)
    
    picam2.stop()
    current_instruction = f"✅ COMPLETE! Captured {photo_count} photos. Close this page."

def main():
    global current_instruction, photo_count, total_photos
    
    parser = argparse.ArgumentParser(description="Web-based face enrollment")
    parser.add_argument('--name', type=str, required=True, help='Person name')
    parser.add_argument('--output', type=str, default='enrollment_photos', help='Output directory')
    parser.add_argument('--port', type=int, default=5001, help='Web server port')
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("Web-Based Face Enrollment")
    print("=" * 70)
    print(f"\nEnrolling: {args.name}")
    print(f"Output: {output_dir}")
    print(f"\n🌐 Open in browser: http://optimus:{args.port}")
    print("\nPress Ctrl+C to stop")
    print("=" * 70)
    
    # Store config in app
    app.config['NAME'] = args.name
    
    # Start capture thread
    capture = threading.Thread(target=capture_thread, args=(args.name, output_dir), daemon=True)
    capture.start()
    
    # Start web server
    app.run(host='0.0.0.0', port=args.port, debug=False, threaded=True)

if __name__ == "__main__":
    main()
