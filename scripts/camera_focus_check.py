#!/usr/bin/env python3
"""
Check camera focus capabilities and enable autofocus if available
"""

import cv2
import subprocess

def check_v4l2_controls(device=0):
    """Check available V4L2 controls for the camera"""
    print(f"Checking V4L2 controls for /dev/video{device}...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ['v4l2-ctl', '-d', f'/dev/video{device}', '--list-ctrls'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            output = result.stdout
            
            # Look for focus-related controls
            focus_controls = []
            for line in output.split('\n'):
                if 'focus' in line.lower():
                    focus_controls.append(line)
                    print(line)
            
            if not focus_controls:
                print("No focus controls found")
            
            return output
        else:
            print(f"Error: {result.stderr}")
            return None
            
    except FileNotFoundError:
        print("v4l2-ctl not found. Install with: sudo apt install v4l-utils")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_opencv_focus(device=0):
    """Test OpenCV focus capabilities"""
    print(f"\nTesting OpenCV focus controls for camera {device}...")
    print("=" * 60)
    
    cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print(f"❌ Cannot open camera {device}")
        return
    
    # Check autofocus support
    autofocus = cap.get(cv2.CAP_PROP_AUTOFOCUS)
    print(f"Autofocus status: {autofocus}")
    
    # Try to enable autofocus
    success = cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
    if success:
        print("✓ Autofocus enabled")
        new_status = cap.get(cv2.CAP_PROP_AUTOFOCUS)
        print(f"  New autofocus status: {new_status}")
    else:
        print("❌ Failed to enable autofocus (may not be supported)")
    
    # Check manual focus capability
    focus_value = cap.get(cv2.CAP_PROP_FOCUS)
    print(f"\nManual focus value: {focus_value}")
    
    # Try to set focus (this might fail if autofocus is active)
    print("\nAttempting to set manual focus to 50...")
    success = cap.set(cv2.CAP_PROP_FOCUS, 50)
    if success:
        print("✓ Manual focus set to 50")
    else:
        print("❌ Cannot set manual focus (autofocus may be active or not supported)")
    
    cap.release()

def enable_autofocus_v4l2(device=0):
    """Enable autofocus using v4l2-ctl"""
    print(f"\nAttempting to enable autofocus via v4l2-ctl...")
    print("=" * 60)
    
    try:
        # Try to set focus_auto=1
        result = subprocess.run(
            ['v4l2-ctl', '-d', f'/dev/video{device}', '-c', 'focus_auto=1'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✓ Autofocus enabled via v4l2-ctl")
            
            # Verify it worked
            result = subprocess.run(
                ['v4l2-ctl', '-d', f'/dev/video{device}', '-C', 'focus_auto'],
                capture_output=True,
                text=True,
                timeout=5
            )
            print(f"Current setting: {result.stdout.strip()}")
        else:
            print(f"❌ Failed: {result.stderr}")
            
    except FileNotFoundError:
        print("v4l2-ctl not found. Install with: sudo apt install v4l-utils")
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Camera Focus Diagnostics")
    print("=" * 60)
    
    # Check which cameras are available
    print("\nDetecting cameras...")
    for i in range(4):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"  Camera {i}: Found")
            cap.release()
        else:
            break
    
    device = 0
    print(f"\nChecking camera {device}...\n")
    
    # V4L2 controls
    check_v4l2_controls(device)
    
    # OpenCV controls
    test_opencv_focus(device)
    
    # Try to enable autofocus
    enable_autofocus_v4l2(device)
    
    print("\n" + "=" * 60)
    print("Recommendations:")
    print("1. If autofocus is supported, it should now be enabled")
    print("2. If not supported, you may need to manually adjust the lens")
    print("3. Some USB cameras have a physical focus ring")
    print("4. The IMX708 CSI camera has fixed focus (no adjustment)")

if __name__ == "__main__":
    main()
