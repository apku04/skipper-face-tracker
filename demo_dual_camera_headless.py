#!/usr/bin/env python3
"""
Headless Dual Camera Hailo Face Detection Demo

Runs without display, shows FPS stats in terminal.
Press Ctrl+C to quit.
"""

from picamera2 import Picamera2
from picamera2.devices import Hailo
import time
import threading
from collections import deque

# Camera parameters
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 640  # Square format for SCRFD model
CAMERA_FPS = 15


class HailoCameraThread:
    """Thread for capturing and processing frames from one camera"""
    
    def __init__(self, camera_num, hailo_model_path):
        self.camera_num = camera_num
        self.hailo_model_path = hailo_model_path
        self.running = False
        self.thread = None
        self.picam2 = None
        self.hailo = None
        
        # Stats
        self.fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.detection_count = 0
        self.fps_history = deque(maxlen=10)
        
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
            print(f"Camera {self.camera_num}: Initializing Hailo...")
            self.hailo = Hailo(self.hailo_model_path)
            print(f"Camera {self.camera_num}: ✓ Hailo initialized")
            
            # Initialize camera
            print(f"Camera {self.camera_num}: Initializing camera...")
            self.picam2 = Picamera2(self.camera_num)
            config = self.picam2.create_preview_configuration(
                main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"},
                controls={"FrameRate": CAMERA_FPS}
            )
            self.picam2.configure(config)
            self.picam2.start()
            print(f"Camera {self.camera_num}: ✓ Started at {CAMERA_WIDTH}x{CAMERA_HEIGHT} @ {CAMERA_FPS}fps")
            
            frame_times = deque(maxlen=30)
            
            while self.running:
                loop_start = time.time()
                
                # Capture frame
                frame = self.picam2.capture_array()
                
                # Run Hailo detection
                try:
                    results = self.hailo.run(frame)
                    if results:
                        self.detection_count += 1
                except Exception as e:
                    if self.frame_count % 100 == 0:  # Only print occasionally
                        print(f"Camera {self.camera_num}: Detection error - {e}")
                
                # Update FPS
                self.frame_count += 1
                frame_times.append(time.time() - loop_start)
                
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count / (current_time - self.last_fps_time)
                    self.fps_history.append(self.fps)
                    self.frame_count = 0
                    self.last_fps_time = current_time
                    
                    # Calculate average frame time
                    if frame_times:
                        avg_frame_time = sum(frame_times) / len(frame_times)
                        print(f"Camera {self.camera_num}: {self.fps:.1f} FPS | "
                              f"Frame: {avg_frame_time*1000:.1f}ms | "
                              f"Detections: {self.detection_count}")
                
                time.sleep(0.001)
                
        except Exception as e:
            print(f"Camera {self.camera_num}: ❌ Thread error - {e}")
            import traceback
            traceback.print_exc()
    
    def get_stats(self):
        """Get camera statistics"""
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        return {
            'camera': self.camera_num,
            'fps': self.fps,
            'avg_fps': avg_fps,
            'detections': self.detection_count
        }


class HeadlessDualCameraDemo:
    """Headless demo application"""
    
    def __init__(self):
        self.hailo_model = "/usr/share/hailo-models/scrfd_2.5g_h8l.hef"
        self.cam0 = HailoCameraThread(0, self.hailo_model)
        self.cam1 = HailoCameraThread(1, self.hailo_model)
        self.running = False
        
    def start(self):
        """Start the demo"""
        print("=" * 60)
        print("Headless Dual Camera Hailo Demo")
        print("=" * 60)
        print("Press Ctrl+C to quit\n")
        
        self.running = True
        
        # Start camera threads
        print("Starting cameras...")
        self.cam0.start()
        time.sleep(0.5)  # Stagger starts
        self.cam1.start()
        
        # Wait for initialization
        time.sleep(2.0)
        
        print("\n" + "=" * 60)
        print("Running (FPS stats update every second)")
        print("=" * 60 + "\n")
        
        try:
            last_summary = time.time()
            
            while self.running:
                time.sleep(0.1)
                
                # Print summary every 5 seconds
                if time.time() - last_summary >= 5.0:
                    self._print_summary()
                    last_summary = time.time()
                
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the demo"""
        print("\nStopping cameras...")
        self.cam0.stop()
        self.cam1.stop()
        
        # Final summary
        print("\n" + "=" * 60)
        print("FINAL STATS")
        print("=" * 60)
        self._print_summary()
        print("\nDemo stopped")
    
    def _print_summary(self):
        """Print statistics summary"""
        stats0 = self.cam0.get_stats()
        stats1 = self.cam1.get_stats()
        
        total_fps = stats0['fps'] + stats1['fps']
        total_avg_fps = stats0['avg_fps'] + stats1['avg_fps']
        total_detections = stats0['detections'] + stats1['detections']
        
        print(f"\n{'─' * 60}")
        print(f"Camera 0: {stats0['fps']:5.1f} FPS (avg: {stats0['avg_fps']:5.1f}) | "
              f"Detections: {stats0['detections']:6d}")
        print(f"Camera 1: {stats1['fps']:5.1f} FPS (avg: {stats1['avg_fps']:5.1f}) | "
              f"Detections: {stats1['detections']:6d}")
        print(f"{'─' * 60}")
        print(f"TOTAL:    {total_fps:5.1f} FPS (avg: {total_avg_fps:5.1f}) | "
              f"Detections: {total_detections:6d}")
        print(f"{'─' * 60}")


def main():
    demo = HeadlessDualCameraDemo()
    demo.start()


if __name__ == "__main__":
    main()
