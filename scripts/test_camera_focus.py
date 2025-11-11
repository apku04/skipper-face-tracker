#!/usr/bin/env python3
"""
Capture a test image from RPi Camera Module 3 to check focus quality
"""

import cv2
import time
from datetime import datetime

def capture_test_image(device=0, output_dir="."):
    """Capture high-quality test image"""
    
    print(f"Opening camera {device}...")
    cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print(f"❌ Cannot open camera {device}")
        return False
    
    # Use same resolution as face tracker (640x480)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Get actual resolution
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Resolution: {actual_w}x{actual_h}")
    
    # Let camera adjust
    print("Warming up camera (2 seconds)...")
    for i in range(10):
        ret, frame = cap.read()
        time.sleep(0.2)
    
    # Capture frame
    print("Capturing image...")
    ret, frame = cap.read()
    
    if not ret:
        print("❌ Failed to capture frame")
        cap.release()
        return False
    
    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/camera_test_{timestamp}.jpg"
    
    # Save at high quality
    cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"✓ Image saved: {filename}")
    
    # Calculate sharpness (Laplacian variance - higher = sharper)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    sharpness = laplacian.var()
    
    print(f"\nSharpness score: {sharpness:.2f}")
    if sharpness < 50:
        print("  ⚠ Image appears quite blurry")
    elif sharpness < 100:
        print("  ℹ Image slightly soft, but usable")
    elif sharpness < 300:
        print("  ✓ Image reasonably sharp")
    else:
        print("  ✓ Image very sharp")
    
    cap.release()
    
    print("\nTo view the image:")
    print(f"  scp pi@optimus:{filename} .")
    print("  Or open http://<pi-ip>:5000 if face tracker is running")
    
    return True

if __name__ == "__main__":
    import sys
    import os
    
    # Save to current directory
    output_dir = os.getcwd()
    
    print("RPi Camera Module 3 Focus Test")
    print("=" * 60)
    print("Note: RPi Camera 3 has FIXED FOCUS")
    print("Optimal distance: 50cm - 2m from camera")
    print("=" * 60)
    print()
    
    success = capture_test_image(device=0, output_dir=output_dir)
    
    if success:
        print("\n" + "=" * 60)
        print("Tips for best focus:")
        print("1. Position yourself 50cm-2m from camera")
        print("2. Ensure good lighting")
        print("3. Clean the camera lens")
        print("4. Check if protective film was removed from lens")
        print("=" * 60)
    
    sys.exit(0 if success else 1)
