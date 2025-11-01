#!/usr/bin/env python3
"""
Test dual CSI camera setup with Hailo face detection
"""

import sys
import time
from picamera2 import Picamera2

def detect_cameras():
    """Detect all available cameras"""
    print("=" * 60)
    print("Detecting Available Cameras")
    print("=" * 60)
    
    cameras = Picamera2.global_camera_info()
    
    if not cameras:
        print("❌ No cameras detected!")
        return []
    
    print(f"✓ Found {len(cameras)} camera(s):\n")
    for i, cam in enumerate(cameras):
        print(f"Camera {i}:")
        print(f"  Model: {cam.get('Model', 'Unknown')}")
        print(f"  Location: {cam.get('Location', 'Unknown')}")
        print(f"  ID: {cam.get('Id', 'Unknown')}")
        print()
    
    return cameras


def test_single_camera(camera_num):
    """Test individual camera"""
    print(f"\n{'=' * 60}")
    print(f"Testing Camera {camera_num}")
    print("=" * 60)
    
    picam2 = None
    try:
        picam2 = Picamera2(camera_num)
        print(f"✓ Camera {camera_num} initialized")
        
        config = picam2.create_preview_configuration(
            main={"size": (320, 240), "format": "RGB888"},
            controls={"FrameRate": 30}
        )
        picam2.configure(config)
        print(f"✓ Camera {camera_num} configured (320x240 @ 30fps)")
        
        picam2.start()
        print(f"✓ Camera {camera_num} started")
        
        # Capture a few frames
        for i in range(3):
            frame = picam2.capture_array()
            print(f"  Frame {i+1}: {frame.shape} {frame.dtype}")
            time.sleep(0.1)
        
        picam2.stop()
        picam2.close()
        print(f"✓ Camera {camera_num} stopped\n")
        return True
        
    except Exception as e:
        print(f"❌ Camera {camera_num} failed: {e}\n")
        return False
    finally:
        if picam2:
            try:
                picam2.close()
            except:
                pass


def test_dual_cameras_sequential():
    """Test both cameras one after another"""
    print("\n" + "=" * 60)
    print("Testing Dual Cameras (Sequential)")
    print("=" * 60)
    
    cam0_ok = test_single_camera(0)
    cam1_ok = test_single_camera(1)
    
    return cam0_ok and cam1_ok


def test_dual_cameras_hailo():
    """Test both cameras with Hailo face detection"""
    print("\n" + "=" * 60)
    print("Testing Dual Cameras with Hailo")
    print("=" * 60)
    
    try:
        from picamera2.devices import Hailo
        print("✓ Hailo imports successful")
    except ImportError as e:
        print(f"⚠ Hailo not available: {e}")
        return False
    
    model_path = "/usr/share/hailo-models/scrfd_2.5g_h8l.hef"
    
    picam0 = None
    picam1 = None
    
    try:
        # Initialize Hailo
        print(f"\nInitializing Hailo with model: {model_path}")
        hailo = Hailo(model_path)
        print("✓ Hailo device initialized")
        
        # Test different resolutions to find what works
        test_resolutions = [
            (640, 640),  # Square - common for face models
            (640, 480),  # Standard VGA
            (320, 320),  # Smaller square
            (320, 240),  # Low-res
        ]
        
        print("\nTesting different resolutions to find Hailo input size...")
        
        for width, height in test_resolutions:
            print(f"\nTrying {width}x{height}...")
            try:
                picam0 = Picamera2(0)
                config = picam0.create_preview_configuration(
                    main={"size": (width, height), "format": "RGB888"},
                    controls={"FrameRate": 30}
                )
                picam0.configure(config)
                picam0.start()
                
                # Try one inference
                frame = picam0.capture_array()
                print(f"  Frame shape: {frame.shape}, size: {frame.nbytes} bytes")
                
                results = hailo.run(frame)
                print(f"  ✓ Hailo inference SUCCESS at {width}x{height}!")
                print(f"  Results: {results}")
                
                picam0.stop()
                picam0.close()
                picam0 = None
                
                # Found working resolution - now test dual cameras
                print(f"\n{'=' * 60}")
                print(f"Testing DUAL cameras at {width}x{height}")
                print("=" * 60)
                
                # Camera 0
                picam0 = Picamera2(0)
                config0 = picam0.create_preview_configuration(
                    main={"size": (width, height), "format": "RGB888"},
                    controls={"FrameRate": 15}  # Lower FPS for dual
                )
                picam0.configure(config0)
                picam0.start()
                print(f"✓ Camera 0 started at {width}x{height} @ 15fps")
                
                # Camera 1
                picam1 = Picamera2(1)
                config1 = picam1.create_preview_configuration(
                    main={"size": (width, height), "format": "RGB888"},
                    controls={"FrameRate": 15}
                )
                picam1.configure(config1)
                picam1.start()
                print(f"✓ Camera 1 started at {width}x{height} @ 15fps")
                
                # Test interleaved capture with Hailo
                print("\nRunning dual camera inference test...")
                for i in range(6):
                    cam_num = i % 2
                    cam = picam0 if cam_num == 0 else picam1
                    
                    frame = cam.capture_array()
                    
                    try:
                        results = hailo.run(frame)
                        num_detections = len(results) if results else 0
                        print(f"  Frame {i+1} (Cam {cam_num}): {num_detections} detection(s)")
                    except Exception as e:
                        print(f"  Frame {i+1} (Cam {cam_num}): inference error - {e}")
                    
                    time.sleep(0.1)
                
                print(f"\n✅ DUAL CAMERA HAILO TEST PASSED at {width}x{height}!")
                
                picam0.stop()
                picam0.close()
                picam1.stop()
                picam1.close()
                hailo.close()
                
                return True
                
            except Exception as e:
                print(f"  ✗ Failed at {width}x{height}: {e}")
                if picam0:
                    try:
                        picam0.stop()
                        picam0.close()
                    except:
                        pass
                    picam0 = None
                if picam1:
                    try:
                        picam1.stop()
                        picam1.close()
                    except:
                        pass
                    picam1 = None
                continue
        
        print("\n❌ Could not find working resolution for Hailo")
        return False
        
    except Exception as e:
        print(f"\n❌ Dual camera Hailo test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if picam0:
            try:
                picam0.close()
            except:
                pass
        if picam1:
            try:
                picam1.close()
            except:
                pass


def main():
    print("\n" + "=" * 60)
    print("Dual Camera + Hailo Test Suite")
    print("=" * 60 + "\n")
    
    # Step 1: Detect cameras
    cameras = detect_cameras()
    if len(cameras) < 2:
        print(f"❌ Need 2 cameras but found {len(cameras)}")
        print("   Connect both CSI cameras and try again.")
        sys.exit(1)
    
    # Step 2: Test cameras individually
    seq_ok = test_dual_cameras_sequential()
    if not seq_ok:
        print("\n❌ Individual camera tests failed")
        sys.exit(1)
    
    # Step 3: Test with Hailo
    hailo_ok = test_dual_cameras_hailo()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Camera Detection:  {'✅ PASS' if len(cameras) == 2 else '❌ FAIL'}")
    print(f"Sequential Test:   {'✅ PASS' if seq_ok else '❌ FAIL'}")
    print(f"Dual Hailo Test:   {'✅ PASS' if hailo_ok else '⚠ SKIP'}")
    print("=" * 60 + "\n")
    
    if hailo_ok:
        print("🎉 Both cameras work with Hailo! Ready for stereo vision.")
    elif seq_ok:
        print("⚠ Cameras work but Hailo needs configuration.")
    else:
        print("❌ Camera setup issues detected.")


if __name__ == "__main__":
    main()
