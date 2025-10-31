#!/usr/bin/env python3
"""
Virtual Face Tracking with Dual Cameras + Hailo

Shows:
- Green box around detected face (from both cameras)
- Red dot at frame center
- Blue dot at face center
- Virtual motor commands (azimuth/altitude angles)
- No actual motor movement - just visualization

This proves the tracking logic before connecting to Klipper.
"""

from picamera2 import Picamera2
from picamera2.devices import Hailo
import cv2
import numpy as np
import time
import threading
from queue import Queue
from flask import Flask, Response
import io

# Camera parameters
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 640
CAMERA_FPS = 30  # Try higher FPS with single camera first

# Tracking parameters (from your working follow_face.py)
DEADBAND_PX = 80
DAMPING_ZONE_PX = 160
BOX_MARGIN = 0.30  # 30% inner margin for box-based tracking

# Virtual motor limits (degrees)
AZIMUTH_MIN = -13.0
AZIMUTH_MAX = 13.0
ALTITUDE_MIN = -4.0
ALTITUDE_MAX = 4.0

# Flask app for streaming
app = Flask(__name__)

class SCRFDParser:
    """Parse SCRFD model output to face detections"""
    
    def __init__(self):
        self.conf_threshold = 0.5
        
    def parse(self, results, img_shape):
        """
        Parse SCRFD raw output to face boxes
        
        SCRFD outputs:
        - conv42, conv49, conv55: Classification (face/no-face)
        - conv44, conv51, conv57: Bounding box regression
        - conv43, conv50, conv56: Landmarks (5 keypoints)
        
        Returns: List of (x, y, w, h, confidence) tuples
        """
        if not results or not isinstance(results, dict):
            return []
        
        # For now, return empty - we'll implement proper SCRFD parsing
        # The raw output needs stride-based decoding with anchors
        # This is complex, so let's start with a simplified approach
        
        # TODO: Implement proper SCRFD post-processing
        # For now, we'll use a mock detector to test the visualization
        return []


class VirtualTracker:
    """Calculate virtual motor positions without moving"""
    
    def __init__(self):
        self.current_az = 0.0  # Current azimuth angle
        self.current_alt = 0.0  # Current altitude angle
        
        # Tracking state
        self.target_x = None
        self.target_y = None
        
    def calculate_motor_command(self, face_box, frame_shape):
        """
        Calculate where motors would move to track face
        
        Args:
            face_box: (x, y, w, h) or None
            frame_shape: (height, width)
            
        Returns:
            dict with tracking info
        """
        h, w = frame_shape[:2]
        frame_center_x = w // 2
        frame_center_y = h // 2
        
        if face_box is None:
            return {
                'has_target': False,
                'azimuth': self.current_az,
                'altitude': self.current_alt,
                'error_x': 0,
                'error_y': 0,
                'in_deadband': True
            }
        
        x, y, fw, fh = face_box
        
        # Calculate face center
        face_center_x = int(x + fw / 2)
        face_center_y = int(y + fh / 2)
        
        # Calculate inner box (30% margin)
        margin_w = fw * BOX_MARGIN
        margin_h = fh * BOX_MARGIN
        inner_x1 = x + margin_w
        inner_y1 = y + margin_h
        inner_x2 = x + fw - margin_w
        inner_y2 = y + fh - margin_h
        
        # Check if frame center is inside face box
        center_in_box = (inner_x1 <= frame_center_x <= inner_x2 and
                         inner_y1 <= frame_center_y <= inner_y2)
        
        # Calculate error (distance from frame center to inner box edge)
        if center_in_box:
            error_x = 0
            error_y = 0
        else:
            # Distance to nearest edge of inner box
            if frame_center_x < inner_x1:
                error_x = frame_center_x - inner_x1  # Negative = move right
            elif frame_center_x > inner_x2:
                error_x = frame_center_x - inner_x2  # Positive = move left
            else:
                error_x = 0
                
            if frame_center_y < inner_y1:
                error_y = frame_center_y - inner_y1  # Negative = move down
            elif frame_center_y > inner_y2:
                error_y = frame_center_y - inner_y2  # Positive = move up
            else:
                error_y = 0
        
        # Calculate if in deadband/damping zones
        error_magnitude = np.sqrt(error_x**2 + error_y**2)
        in_deadband = error_magnitude < DEADBAND_PX
        in_damping = DEADBAND_PX <= error_magnitude < DAMPING_ZONE_PX
        
        # Calculate virtual motor deltas (simplified - no time integration)
        if in_deadband:
            delta_az = 0.0
            delta_alt = 0.0
        else:
            # Convert pixels to degrees (rough approximation)
            # Assuming ~60 degree FOV and 640px width
            px_to_deg = 60.0 / w
            delta_az = -error_x * px_to_deg * 0.1  # Damped
            delta_alt = error_y * px_to_deg * 0.1  # Damped (inverted Y)
        
        # Update virtual position
        self.current_az = np.clip(self.current_az + delta_az, AZIMUTH_MIN, AZIMUTH_MAX)
        self.current_alt = np.clip(self.current_alt + delta_alt, ALTITUDE_MIN, ALTITUDE_MAX)
        
        return {
            'has_target': True,
            'face_center': (face_center_x, face_center_y),
            'inner_box': (inner_x1, inner_y1, inner_x2, inner_y2),
            'azimuth': self.current_az,
            'altitude': self.current_alt,
            'error_x': error_x,
            'error_y': error_y,
            'in_deadband': in_deadband,
            'in_damping': in_damping
        }


class HailoVirtualTracker:
    """Main application"""
    
    def __init__(self, camera_num=0):
        self.camera_num = camera_num
        self.hailo_model = "/usr/share/hailo-models/scrfd_2.5g_h8l.hef"
        self.picam2 = None
        self.hailo = None
        self.parser = SCRFDParser()
        self.tracker = VirtualTracker()
        
        self.running = False
        self.frame_queue = Queue(maxsize=2)
        self.latest_frame = None
        self.fps = 0
        
    def start(self):
        """Start camera and Hailo"""
        print(f"Initializing Camera {self.camera_num}...")
        
        # Initialize Hailo
        self.hailo = Hailo(self.hailo_model)
        print("✓ Hailo initialized")
        
        # Initialize camera
        self.picam2 = Picamera2(self.camera_num)
        config = self.picam2.create_preview_configuration(
            main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"},
            controls={"FrameRate": CAMERA_FPS}
        )
        self.picam2.configure(config)
        self.picam2.start()
        print(f"✓ Camera started at {CAMERA_WIDTH}x{CAMERA_HEIGHT} @ {CAMERA_FPS}fps")
        
        self.running = True
        
        # Start processing thread
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        
        print("\n✓ Virtual tracking started")
        print("  View at: http://localhost:5000")
        print("  Press Ctrl+C to stop\n")
        
    def stop(self):
        """Stop everything"""
        self.running = False
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()
        if self.hailo:
            self.hailo.close()
        print("Stopped")
        
    def _process_loop(self):
        """Main processing loop"""
        frame_count = 0
        fps_start = time.time()
        
        while self.running:
            try:
                # Capture frame
                frame = self.picam2.capture_array()
                
                # Run Hailo detection (for now, returns empty)
                results = self.hailo.run(frame)
                detections = self.parser.parse(results, frame.shape)
                
                # For testing: Use OpenCV Haar cascade as fallback
                # (Remove this once SCRFD parsing works)
                if not detections:
                    detections = self._detect_faces_opencv(frame)
                
                # Pick best detection (largest face)
                best_face = None
                if detections:
                    best_face = max(detections, key=lambda d: d[2] * d[3])  # Largest area
                
                # Calculate tracking
                tracking_info = self.tracker.calculate_motor_command(
                    best_face[:4] if best_face else None,
                    frame.shape
                )
                
                # Draw visualization
                vis_frame = self._draw_visualization(frame, best_face, tracking_info)
                
                # Update latest frame for streaming
                self.latest_frame = vis_frame
                
                # Update FPS
                frame_count += 1
                if time.time() - fps_start >= 1.0:
                    self.fps = frame_count / (time.time() - fps_start)
                    frame_count = 0
                    fps_start = time.time()
                    
                    # Print status
                    print(f"FPS: {self.fps:.1f} | "
                          f"Az: {tracking_info['azimuth']:+6.2f}° | "
                          f"Alt: {tracking_info['altitude']:+6.2f}° | "
                          f"Target: {'YES' if tracking_info['has_target'] else 'NO '} | "
                          f"Deadband: {'YES' if tracking_info.get('in_deadband', False) else 'NO '}")
                
            except Exception as e:
                print(f"Error in process loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
    
    def _detect_faces_opencv(self, frame):
        """Fallback face detection using OpenCV (for testing)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        
        # Try to load cascade
        try:
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            # Convert to (x, y, w, h, confidence) format
            return [(x, y, w, h, 1.0) for (x, y, w, h) in faces]
        except:
            return []
    
    def _draw_visualization(self, frame, face_box, tracking_info):
        """Draw tracking visualization on frame"""
        vis = frame.copy()
        h, w = vis.shape[:2]
        
        frame_center_x = w // 2
        frame_center_y = h // 2
        
        # Draw frame center (red dot)
        cv2.circle(vis, (frame_center_x, frame_center_y), 8, (0, 0, 255), -1)
        cv2.circle(vis, (frame_center_x, frame_center_y), 10, (0, 0, 255), 2)
        
        if face_box:
            x, y, fw, fh, conf = face_box
            
            # Draw face box (green)
            cv2.rectangle(vis, (int(x), int(y)), (int(x+fw), int(y+fh)), (0, 255, 0), 3)
            
            # Draw confidence
            cv2.putText(vis, f"{conf:.2f}", (int(x), int(y)-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Draw inner box (tracking zone)
            if 'inner_box' in tracking_info:
                ix1, iy1, ix2, iy2 = tracking_info['inner_box']
                cv2.rectangle(vis, (int(ix1), int(iy1)), (int(ix2), int(iy2)),
                            (0, 255, 255), 2)
            
            # Draw face center (blue dot)
            if 'face_center' in tracking_info:
                fx, fy = tracking_info['face_center']
                cv2.circle(vis, (fx, fy), 6, (255, 0, 0), -1)
                cv2.circle(vis, (fx, fy), 8, (255, 0, 0), 2)
        
        # Draw status text
        status_y = 30
        cv2.putText(vis, f"FPS: {self.fps:.1f}", (10, status_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        status_y += 30
        cv2.putText(vis, f"Azimuth: {tracking_info['azimuth']:+6.2f}°", (10, status_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        status_y += 30
        cv2.putText(vis, f"Altitude: {tracking_info['altitude']:+6.2f}°", (10, status_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        status_y += 30
        if tracking_info.get('in_deadband'):
            status_text = "CENTERED"
            color = (0, 255, 0)
        elif tracking_info.get('in_damping'):
            status_text = "DAMPING"
            color = (0, 255, 255)
        else:
            status_text = "TRACKING"
            color = (255, 165, 0)
        cv2.putText(vis, status_text, (10, status_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Draw deadband zones (visualization)
        cv2.circle(vis, (frame_center_x, frame_center_y), DEADBAND_PX, (0, 255, 0), 1)
        cv2.circle(vis, (frame_center_x, frame_center_y), DAMPING_ZONE_PX, (0, 255, 255), 1)
        
        return vis
    
    def get_frame(self):
        """Get latest frame for streaming"""
        return self.latest_frame


# Flask routes
tracker = None

@app.route('/')
def index():
    return '''
    <html>
    <head><title>Virtual Face Tracker</title></head>
    <body style="background: #000; margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh;">
        <div style="text-align: center;">
            <h1 style="color: #0f0;">Virtual Face Tracking (No Motors)</h1>
            <img src="/video_feed" style="max-width: 90%; border: 2px solid #0f0;">
            <p style="color: #fff; margin-top: 20px;">
                🟢 Green box = Face detection<br>
                🔴 Red dot = Frame center<br>
                🔵 Blue dot = Face center<br>
                🟡 Yellow = Virtual motor angles
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            if tracker and tracker.latest_frame is not None:
                frame = tracker.latest_frame
                # Convert to JPEG
                ret, jpeg = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.03)  # ~30 FPS
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


def main():
    global tracker
    
    print("=" * 60)
    print("Virtual Face Tracker with Hailo")
    print("=" * 60)
    print("\nThis demonstrates tracking logic WITHOUT moving motors")
    print("Once this works, we'll connect to Klipper\n")
    
    tracker = HailoVirtualTracker(camera_num=0)  # Use camera 0 first
    tracker.start()
    
    # Start Flask in main thread
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        tracker.stop()


if __name__ == "__main__":
    main()
