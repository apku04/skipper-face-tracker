#!/usr/bin/env python3
"""Find which video device index works for the Logitech camera"""
import cv2
import sys

print("Scanning for working video devices...")
print("-" * 50)

working_devices = []

for i in range(40):  # Check /dev/video0 through /dev/video39
    cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            height, width = frame.shape[:2]
            print(f"✓ /dev/video{i} - Working! Resolution: {width}x{height}")
            working_devices.append(i)
        else:
            print(f"  /dev/video{i} - Opens but can't read frames")
        cap.release()

print()
print("-" * 50)
if working_devices:
    print(f"✓ Found {len(working_devices)} working device(s): {working_devices}")
    print()
    print(f"Update follow_face.py:")
    print(f"  Change: CAP_INDEX = {working_devices[0]}")
else:
    print("✗ No working video devices found")
    print()
    print("Troubleshooting:")
    print("  1. Check USB connection: lsusb | grep -i logitech")
    print("  2. Try unplugging and replugging the camera")
    print("  3. Check kernel logs: dmesg | tail -30")
