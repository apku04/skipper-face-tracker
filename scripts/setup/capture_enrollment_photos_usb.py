#!/usr/bin/env python3
"""
Capture Enrollment Photos from USB Webcam
==========================================

Uses any USB webcam or video device to capture enrollment photos.
Shows live preview in browser and lets you save photos for face recognition enrollment.

Usage:
    python3 scripts/capture_enrollment_photos_usb.py --name "YourName" --camera 0
    
    # Or specify output directory
    python3 scripts/capture_enrollment_photos_usb.py --name "YourName" --camera /dev/video0 --output enrollment_photos/
"""

import sys
import os
import argparse
import time
import cv2
import threading
from flask import Flask, Response, render_template_string
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Flask app for streaming
app = Flask(__name__)
current_frame = None
frame_lock = threading.Lock()
person_name = ""
photo_count = 0

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Face Enrollment - {{ name }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1a1a1a;
            color: #fff;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 {
            color: #4CAF50;
            margin-bottom: 10px;
        }
        .info {
            background: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .video-container {
            border: 4px solid #4CAF50;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        img {
            display: block;
            max-width: 100%;
            height: auto;
        }
        .instructions {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            max-width: 600px;
        }
        .instructions h2 {
            color: #4CAF50;
            margin-top: 0;
        }
        .instructions li {
            margin: 10px 0;
            line-height: 1.6;
        }
        .status {
            font-size: 1.2em;
            font-weight: bold;
            color: #4CAF50;
        }
    </style>
</head>
<body>
    <h1>📸 Face Enrollment: {{ name }}</h1>
    <div class="info">
        <p class="status">Photos captured: {{ count }}</p>
        <p>Press <strong>ENTER</strong> in terminal to capture | Type <strong>'done'</strong> when finished</p>
    </div>
    
    <div class="video-container">
        <img src="{{ url_for('video_feed') }}" alt="Live Feed">
    </div>
    
    <div class="instructions">
        <h2>Instructions:</h2>
        <ol>
            <li>Position your face in the center of the frame</li>
            <li>Press <strong>ENTER</strong> in the terminal to capture a photo</li>
            <li>Capture photos from different angles:
                <ul>
                    <li>Looking straight ahead</li>
                    <li>Turned slightly left</li>
                    <li>Turned slightly right</li>
                    <li>Looking up slightly</li>
                    <li>Looking down slightly</li>
                </ul>
            </li>
            <li>Capture at least <strong>5-10 photos</strong> for best results</li>
            <li>Type <strong>'done'</strong> when finished capturing</li>
        </ol>
    </div>
</body>
</html>
"""

def generate_frames():
    """Generator for streaming frames"""
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
    """Serve the main page"""
    return render_template_string(HTML_TEMPLATE, name=person_name, count=photo_count)


@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def start_flask_server():
    """Start Flask server in a separate thread"""
    app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False, debug=False)


def capture_photos(name, camera_device, output_dir):
    """Capture enrollment photos"""
    global current_frame, person_name, photo_count
    
    person_name = name
    photo_count = 0
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📸 Capturing enrollment photos for '{name}'")
    print(f"   Camera: {camera_device}")
    print(f"   Output: {output_dir}")
    print()
    
    # Parse camera device
    if isinstance(camera_device, str) and camera_device.startswith('/dev/video'):
        # Extract number from /dev/videoX
        cam_id = int(camera_device.split('video')[1])
    else:
        cam_id = int(camera_device)
    
    print("Initializing camera...")
    cap = cv2.VideoCapture(cam_id)
    
    if not cap.isOpened():
        print(f"❌ Error: Could not open camera {camera_device}")
        print("\nAvailable cameras:")
        for i in range(10):
            test_cap = cv2.VideoCapture(i)
            if test_cap.isOpened():
                print(f"  - Camera {i} (/dev/video{i})")
                test_cap.release()
        return
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1232)
    
    # Get actual resolution
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"✅ Camera initialized at {width}x{height}")
    print()
    
    # Start Flask server
    print("Starting web server...")
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()
    time.sleep(2)  # Give Flask time to start
    
    print("✅ Web server started!")
    print()
    print("=" * 60)
    print("📺 Open browser to: http://localhost:5000")
    print("=" * 60)
    print()
    print("Instructions:")
    print("  1. Open the URL above in your browser to see live preview")
    print("  2. Position your face in the camera view")
    print("  3. Press ENTER to capture a photo")
    print("  4. Capture 5-10 photos from different angles")
    print("  5. Type 'done' when finished")
    print()
    
    # Main capture loop
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error reading frame")
                break
            
            # Update current frame for streaming
            with frame_lock:
                current_frame = frame.copy()
            
            # Wait for user input
            user_input = input("Press ENTER to capture (or 'done' to finish): ").strip().lower()
            
            if user_input == 'done':
                print("\n✅ Capture session completed!")
                break
            
            # Capture photo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            photo_count += 1
            filename = f"{name}_{timestamp}_{photo_count:03d}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            print(f"📸 Captured: {filename}")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Capture interrupted by user")
    finally:
        cap.release()
        print()
        print(f"📁 Photos saved to: {output_dir}")
        print(f"📊 Total photos: {photo_count}")
        print()
        print("Next step: Enroll these photos:")
        print(f"  python3 scripts/enroll_hailo.py --name \"{name}\" --images {output_dir}/{name}_*.jpg")
        print()


def main():
    parser = argparse.ArgumentParser(description='Capture enrollment photos from USB webcam')
    parser.add_argument('--name', required=True, help='Name of person to enroll')
    parser.add_argument('--camera', default=0, help='Camera device (0, 1, or /dev/video0, etc.)')
    parser.add_argument('--output', default='enrollment_photos', help='Output directory for photos')
    
    args = parser.parse_args()
    
    capture_photos(args.name, args.camera, args.output)


if __name__ == '__main__':
    main()
