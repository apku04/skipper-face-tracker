#!/usr/bin/env python3
"""
Test different camera backends and settings to find one that works.
"""

import cv2
import time

def test_camera(index, backend, backend_name):
    """Test opening camera with specific backend."""
    print(f"\n{'='*60}")
    print(f"Testing: /dev/video{index} with {backend_name}")
    print('='*60)
    
    try:
        cap = cv2.VideoCapture(index, backend)
        
        if not cap.isOpened():
            print(f"✗ Failed to open camera with {backend_name}")
            return False
        
        print(f"✓ Camera opened with {backend_name}")
        
        # Try to read a frame
        ret, frame = cap.read()
        if ret:
            print(f"✓ Successfully captured frame: {frame.shape}")
            cap.release()
            return True
        else:
            print(f"✗ Could not capture frame")
            cap.release()
            return False
            
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def main():
    print("Testing camera with different backends and indices...\n")
    
    backends = [
        (cv2.CAP_V4L2, "V4L2"),
        (cv2.CAP_ANY, "ANY"),
        (cv2.CAP_GSTREAMER, "GSTREAMER"),
    ]
    
    # Try indices 0-4
    for index in range(5):
        for backend, name in backends:
            if test_camera(index, backend, name):
                print(f"\n{'*'*60}")
                print(f"SUCCESS! Use: cv2.VideoCapture({index}, cv2.CAP_{name})")
                print('*'*60)
                return
    
    print("\n✗ No working camera configuration found")
    print("\nDiagnostic info:")
    print("- Check: ls -la /dev/video*")
    print("- Check: dmesg | tail -20")
    print("- Camera may need powered USB hub or different cable")

if __name__ == "__main__":
    main()
