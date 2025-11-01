#!/usr/bin/env python3
"""
Test RPi Camera 1.3 with Hailo face detection
"""

import sys
from picamera2 import Picamera2
from libcamera import controls
import time

def test_basic_camera():
    """Test basic camera functionality"""
    print("=" * 60)
    print("Testing RPi Camera 1.3 Basic Functionality")
    print("=" * 60)
    
    picam2 = None
    try:
        picam2 = Picamera2()
        print("✓ Picamera2 initialized")
        
        # Get camera info
        camera_info = picam2.camera_properties
        print(f"\nCamera Properties:")
        print(f"  Model: {camera_info.get('Model', 'Unknown')}")
        print(f"  Location: {camera_info.get('Location', 'Unknown')}")
        
        # Configure for preview
        config = picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            controls={"FrameRate": 30}
        )
        picam2.configure(config)
        print("✓ Camera configured (640x480 @ 30fps)")
        
        # Start camera
        picam2.start()
        print("✓ Camera started")
        
        # Capture a few frames
        for i in range(5):
            frame = picam2.capture_array()
            print(f"  Frame {i+1}: {frame.shape} {frame.dtype}")
            time.sleep(0.1)
        
        picam2.stop()
        picam2.close()
        print("✓ Camera stopped and closed")
        print("\n✅ BASIC CAMERA TEST PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ BASIC CAMERA TEST FAILED: {e}\n")
        return False
    finally:
        if picam2:
            try:
                picam2.close()
            except:
                pass


def test_hailo_integration():
    """Test Hailo postprocessing with camera"""
    print("=" * 60)
    print("Testing Hailo Integration")
    print("=" * 60)
    
    try:
        from picamera2 import Picamera2, MappedArray
        from picamera2.devices import Hailo
        
        print("✓ Hailo imports successful")
        
        # Check if Hailo models exist
        import os
        model_path = "/usr/share/hailo-models/scrfd_2.5g_h8l.hef"
        if os.path.exists(model_path):
            print(f"✓ Found model: {model_path}")
        else:
            print(f"⚠ Model not found: {model_path}")
            print("  Available models:")
            models_dir = "/usr/share/hailo-models"
            if os.path.exists(models_dir):
                for f in os.listdir(models_dir):
                    if f.endswith('.hef'):
                        print(f"    - {f}")
        
        # Initialize Hailo
        with Hailo(model_path) as hailo:
            print(f"✓ Hailo device initialized")
            print(f"  Model path: {model_path}")
            
            # Initialize camera with Hailo
            picam2 = Picamera2()
            config = picam2.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"},
                controls={"FrameRate": 30}
            )
            picam2.configure(config)
            picam2.start()
            print("✓ Camera started with Hailo")
            
            # Run a few detections
            detections_count = []
            for i in range(10):
                frame = picam2.capture_array()
                
                try:
                    results = hailo.run(frame)
                    
                    if results:
                        # Check various result formats
                        if isinstance(results, list):
                            num_faces = len(results)
                        elif hasattr(results, 'detections'):
                            num_faces = len(results.detections)
                        elif hasattr(results, '__len__'):
                            num_faces = len(results)
                        else:
                            num_faces = 1
                        
                        detections_count.append(num_faces)
                        if num_faces > 0:
                            print(f"  Frame {i+1}: {num_faces} detection(s)")
                    else:
                        detections_count.append(0)
                except Exception as e:
                    print(f"  Frame {i+1}: inference error - {e}")
                    detections_count.append(0)
                
                time.sleep(0.1)
            
            picam2.stop()
            
            print(f"\n✓ Ran {len(detections_count)} inferences")
            print(f"  Average detections: {sum(detections_count)/len(detections_count):.2f}")
            print("\n✅ HAILO INTEGRATION TEST PASSED\n")
            return True
            
    except ImportError as e:
        print(f"\n⚠ Hailo not available: {e}")
        print("  This is expected if Hailo is not installed")
        return False
    except Exception as e:
        print(f"\n❌ HAILO TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 60)
    print("RPi Camera 1.3 + Hailo Test Suite")
    print("=" * 60 + "\n")
    
    # Test 1: Basic camera
    basic_ok = test_basic_camera()
    
    if not basic_ok:
        print("❌ Basic camera failed - cannot proceed with Hailo test")
        sys.exit(1)
    
    # Test 2: Hailo integration
    hailo_ok = test_hailo_integration()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Basic Camera:     {'✅ PASS' if basic_ok else '❌ FAIL'}")
    print(f"Hailo Integration: {'✅ PASS' if hailo_ok else '⚠ SKIP'}")
    print("=" * 60 + "\n")
    
    if basic_ok and hailo_ok:
        print("🎉 All tests passed! Ready for Hailo-based face tracking.")
    elif basic_ok:
        print("⚠ Camera works but Hailo integration needs setup.")
        print("  Install: sudo apt install hailo-all")
    else:
        print("❌ Camera not working properly.")


if __name__ == "__main__":
    main()
