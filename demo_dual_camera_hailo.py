#!/usr/bin/env python3
"""
Standalone Dual Camera Hailo Face Detection Demo

Shows real-time face detection from two cameras using Hailo acceleration.
Press 'q' to quit, 's' to switch display mode.
"""

import cv2
import numpy as np
from picamera2 import Picamera2
from picamera2.devices import Hailo
import time
import threading
from queue import Queue

# Detection parameters
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 640  # Square format for SCRFD model
CAMERA_FPS = 15

# Display modes
DISPLAY_MODE_SIDE_BY_SIDE = 0
DISPLAY_MODE_OVERLAY = 1
DISPLAY_MODE_CAM0_ONLY = 2
DISPLAY_MODE_CAM1_ONLY = 3


class HailoCameraThread:
    """Thread for capturing and processing frames from one camera"""
    
    def __init__(self, camera_num, hailo_model_path):
        self.camera_num = camera_num
        self.hailo_model_path = hailo_model_path
        self.frame_queue = Queue(maxsize=2)
        self.detection_queue = Queue(maxsize=2)
        self.running = False
        self.thread = None
        self.picam2 = None
        self.hailo = None
        self.fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        
    def start(self):
        """Start the camera thread"""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the camera thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.picam2:
            try:
                self.picam2.stop()
                self.picam2.close()
            except:
                pass
        if self.hailo:
            try:
                self.hailo.close()
            except:
                pass
    
    def _run(self):
        """Main thread loop"""
        try:
            # Initialize Hailo
            self.hailo = Hailo(self.hailo_model_path)
            print(f"Camera {self.camera_num}: Hailo initialized")
            
            # Initialize camera
            self.picam2 = Picamera2(self.camera_num)
            config = self.picam2.create_preview_configuration(
                main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"},
                controls={"FrameRate": CAMERA_FPS}
            )
            self.picam2.configure(config)
            self.picam2.start()
            print(f"Camera {self.camera_num}: Started at {CAMERA_WIDTH}x{CAMERA_HEIGHT} @ {CAMERA_FPS}fps")
            
            while self.running:
                # Capture frame
                frame = self.picam2.capture_array()
                
                # Run Hailo detection
                try:
                    results = self.hailo.run(frame)
                    detections = self._parse_detections(results, frame.shape)
                except Exception as e:
                    print(f"Camera {self.camera_num}: Detection error - {e}")
                    detections = []
                
                # Update FPS
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count / (current_time - self.last_fps_time)
                    self.frame_count = 0
                    self.last_fps_time = current_time
                
                # Queue frame and detections
                if not self.frame_queue.full():
                    self.frame_queue.put(frame.copy())
                if not self.detection_queue.full():
                    self.detection_queue.put(detections)
                
                time.sleep(0.001)  # Small sleep to prevent CPU spinning
                
        except Exception as e:
            print(f"Camera {self.camera_num}: Thread error - {e}")
            import traceback
            traceback.print_exc()
    
    def _parse_detections(self, results, frame_shape):
        """Parse Hailo raw output to face detections"""
        # For now, return raw results - we'll parse properly later
        # This is placeholder for actual SCRFD output parsing
        if results and isinstance(results, dict):
            # SCRFD returns multiple output layers
            # For demo, we'll just count detections
            return []  # TODO: Implement SCRFD post-processing
        return []
    
    def get_latest_frame(self):
        """Get the most recent frame"""
        if not self.frame_queue.empty():
            # Drain queue to get latest
            frame = None
            while not self.frame_queue.empty():
                frame = self.frame_queue.get()
            return frame
        return None
    
    def get_latest_detections(self):
        """Get the most recent detections"""
        if not self.detection_queue.empty():
            detections = None
            while not self.detection_queue.empty():
                detections = self.detection_queue.get()
            return detections
        return []


class DualCameraDemo:
    """Main demo application"""
    
    def __init__(self):
        self.hailo_model = "/usr/share/hailo-models/scrfd_2.5g_h8l.hef"
        self.cam0 = HailoCameraThread(0, self.hailo_model)
        self.cam1 = HailoCameraThread(1, self.hailo_model)
        self.display_mode = DISPLAY_MODE_SIDE_BY_SIDE
        self.running = False
        
    def start(self):
        """Start the demo"""
        print("Starting Dual Camera Hailo Demo...")
        print("Controls:")
        print("  q - Quit")
        print("  s - Switch display mode")
        print("  0 - Camera 0 only")
        print("  1 - Camera 1 only")
        print("  2 - Side by side")
        print("  3 - Overlay")
        
        self.running = True
        
        # Start camera threads
        self.cam0.start()
        time.sleep(0.5)  # Stagger starts
        self.cam1.start()
        
        # Wait for cameras to initialize
        time.sleep(2.0)
        
        # Main display loop
        cv2.namedWindow("Dual Camera Hailo Demo", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Dual Camera Hailo Demo", 1280, 480)
        
        try:
            while self.running:
                # Get latest frames
                frame0 = self.cam0.get_latest_frame()
                frame1 = self.cam1.get_latest_frame()
                
                if frame0 is None or frame1 is None:
                    time.sleep(0.01)
                    continue
                
                # Get detections
                dets0 = self.cam0.get_latest_detections()
                dets1 = self.cam1.get_latest_detections()
                
                # Draw detections
                frame0_vis = self._draw_detections(frame0, dets0, self.cam0.fps, "Cam 0")
                frame1_vis = self._draw_detections(frame1, dets1, self.cam1.fps, "Cam 1")
                
                # Create display based on mode
                if self.display_mode == DISPLAY_MODE_SIDE_BY_SIDE:
                    display = np.hstack([frame0_vis, frame1_vis])
                elif self.display_mode == DISPLAY_MODE_OVERLAY:
                    display = cv2.addWeighted(frame0_vis, 0.5, frame1_vis, 0.5, 0)
                elif self.display_mode == DISPLAY_MODE_CAM0_ONLY:
                    display = cv2.resize(frame0_vis, (1280, 640))
                elif self.display_mode == DISPLAY_MODE_CAM1_ONLY:
                    display = cv2.resize(frame1_vis, (1280, 640))
                else:
                    display = np.hstack([frame0_vis, frame1_vis])
                
                # Show frame
                cv2.imshow("Dual Camera Hailo Demo", display)
                
                # Handle keys
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Quitting...")
                    self.running = False
                elif key == ord('s'):
                    self.display_mode = (self.display_mode + 1) % 4
                    print(f"Display mode: {self.display_mode}")
                elif key == ord('0'):
                    self.display_mode = DISPLAY_MODE_CAM0_ONLY
                elif key == ord('1'):
                    self.display_mode = DISPLAY_MODE_CAM1_ONLY
                elif key == ord('2'):
                    self.display_mode = DISPLAY_MODE_SIDE_BY_SIDE
                elif key == ord('3'):
                    self.display_mode = DISPLAY_MODE_OVERLAY
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the demo"""
        print("Stopping cameras...")
        self.cam0.stop()
        self.cam1.stop()
        cv2.destroyAllWindows()
        print("Demo stopped")
    
    def _draw_detections(self, frame, detections, fps, label):
        """Draw detections and info on frame"""
        vis = frame.copy()
        h, w = vis.shape[:2]
        
        # Draw FPS and label
        cv2.putText(vis, f"{label} - {fps:.1f} FPS", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    1.0, (0, 255, 0), 2)
        
        # Draw detections (placeholder - implement SCRFD parsing)
        cv2.putText(vis, f"Hailo Active", 
                    (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, (255, 255, 0), 2)
        
        # Draw center crosshair
        cv2.line(vis, (w//2 - 20, h//2), (w//2 + 20, h//2), (0, 255, 255), 1)
        cv2.line(vis, (w//2, h//2 - 20), (w//2, h//2 + 20), (0, 255, 255), 1)
        
        return vis


def main():
    demo = DualCameraDemo()
    demo.start()


if __name__ == "__main__":
    main()
