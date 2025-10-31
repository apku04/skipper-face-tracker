#!/usr/bin/env python3
"""
Capture Enrollment Photos from CSI Cameras
===========================================

Uses your dual CSI cameras to capture enrollment photos.
Shows live preview in browser and lets you save photos for face recognition enrollment.

Usage:
    python3 scripts/capture_enrollment_photos.py --name "YourName" --camera 0
    
    # Or specify output directory
    python3 scripts/capture_enrollment_photos.py --name "YourName" --camera 0 --output enrollment_photos/
"""

import sys
import os
import argparse
import time
import cv2
import threading
from flask import Flask, Response
from picamera2 import Picamera2

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Flask app for streaming
app = Flask(__name__)
current_frame = None
frame_lock = threading.Lock()

def generate_frames():
    """Generator for streaming frames"""
    while True:
        with frame_lock:
            if current_frame is None:
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
    """Web page with video stream"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enrollment Photo Capture</title>
        <style>
            body {
                margin: 0;
                padding: 20px;
                background: #1a1a1a;
                color: #fff;
                font-family: Arial, sans-serif;
                text-align: center;
            }
            h1 { color: #4CAF50; }
            #video-container {
                margin: 20px auto;
                max-width: 90%;
            }
            img {
                width: 100%;
                max-width: 800px;
                border: 3px solid #4CAF50;
                border-radius: 10px;
            }
            .instructions {
                max-width: 600px;
                margin: 20px auto;
                text-align: left;
                background: #2a2a2a;
                padding: 20px;
                border-radius: 10px;
            }
            .instructions h2 { color: #4CAF50; margin-top: 0; }
            .instructions ul { line-height: 1.8; }
        </style>
    </head>
    <body>
        <h1>📸 Enrollment Photo Capture</h1>
        <div id="video-container">
            <img src="/video_feed" alt="Camera Feed">
        </div>
        <div class="instructions">
            <h2>Instructions:</h2>
            <ul>
                <li><strong>Position your face</strong> in different angles:
                    <ul>
                        <li>Front view (straight)</li>
                        <li>Slight left turn</li>
                        <li>Slight right turn</li>
                        <li>Looking slightly up</li>
                        <li>Looking slightly down</li>
                    </ul>
                </li>
                <li><strong>Press ENTER in terminal</strong> to capture each photo</li>
                <li><strong>Type 'done'</strong> when finished (need 3-5 photos)</li>
            </ul>
        </div>
    </body>
    </html>
    '''


@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')


def start_flask_server():
    """Start Flask server in background thread"""
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)


def capture_photos(name: str, camera_id: int, output_dir: str):
    """Capture enrollment photos from CSI camera with browser preview"""
    global current_frame
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📸 Capturing enrollment photos for '{name}'")
    print(f"   Camera: {camera_id}")
    print(f"   Output: {output_dir}\n")
    
    # Initialize camera
    print("Initializing camera...")
    picam2 = Picamera2(camera_id)
    
    # Configure for capture
    config = picam2.create_still_configuration(
        main={"size": (1640, 1232)},  # Full resolution for enrollment
        lores={"size": (640, 480), "format": "RGB888"},  # Preview stream
        display="lores"
    )
    picam2.configure(config)
    picam2.start()
    
    # Wait for camera to stabilize
    print("Warming up camera...")
    time.sleep(2)
    
    # Start Flask server in background
    print("Starting web preview server...")
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()
    time.sleep(2)  # Give Flask time to start
    
    print("\n✓ Camera ready!")
    print(f"\n🌐 Open browser to: http://localhost:5000")
    print("   (or http://<your-pi-ip>:5000 from another device)\n")
    
    # Start preview update thread
    def update_preview():
        global current_frame
        while True:
            try:
                frame_rgb = picam2.capture_array("lores")
                # Convert RGB to BGR for OpenCV
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                
                with frame_lock:
                    current_frame = frame_bgr
                
                time.sleep(0.033)  # ~30 fps
            except Exception as e:
                print(f"Preview error: {e}")
                break
    
    preview_thread = threading.Thread(target=update_preview, daemon=True)
    preview_thread.start()
    
    print("Instructions:")
    print("  1. Position your face in different angles:")
    print("     - Front view (straight)")
    print("     - Slight left turn")
    print("     - Slight right turn")
    print("     - Looking slightly up")
    print("     - Looking slightly down")
    print("  2. Try different lighting if possible (bright, dim, side light)")
    print("  3. Press ENTER to capture each photo")
    print("  4. Type 'done' when finished (need 3-5 photos)\n")
    
    photo_count = 0
    
    try:
        while True:
            # Show preview info
            print(f"[{photo_count} photos captured] Ready to capture... ", end='', flush=True)
            
            user_input = input()
            
            if user_input.lower() in ['done', 'quit', 'exit', 'q']:
                break
            
            # Capture photo at full resolution
            timestamp = int(time.time() * 1000)
            filename = f"{name.replace(' ', '_')}_{photo_count+1}_{timestamp}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            print(f"  📸 Capturing... ", end='', flush=True)
            picam2.capture_file(filepath)
            photo_count += 1
            print(f"✓ Saved: {filename}")
    
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    
    finally:
        picam2.stop()
        picam2.close()
    
    print(f"\n✓ Captured {photo_count} photo(s) for '{name}'")
    print(f"  Saved to: {output_dir}\n")
    
    if photo_count > 0:
        print("Next step: Enroll these photos")
        print(f"  python3 scripts/enroll_face.py --name \"{name}\" --images {output_dir}/{name.replace(' ', '_')}_*.jpg\n")
    
    return photo_count


def main():
    parser = argparse.ArgumentParser(
        description='Capture enrollment photos from CSI camera',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--name', type=str, required=True,
                       help='Name of the person (for filename prefix)')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera ID (0 or 1, default: 0)')
    parser.add_argument('--output', type=str, default='enrollment_photos',
                       help='Output directory for photos (default: enrollment_photos)')
    
    args = parser.parse_args()
    
    capture_photos(args.name, args.camera, args.output)


if __name__ == '__main__':
    main()
