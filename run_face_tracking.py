#!/usr/bin/env python3
"""
Modified face tracking that uses Klipper/Octopus instead of gpiozero.

Key changes from original:
- Removed gpiozero stepper control
- Added Klipper motor control via HTTP API
- Same tracking algorithm and logic
- Simplified motor interface
"""

# Import everything from original except motor control
import sys
import os

# Add klipper_motors to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Patch the motor control before importing follow_face
from klipper_motors import get_motor_controller

# Now we need to modify how the original code works
# Instead of patching the entire file, let's create a wrapper

print("=" * 60)
print("SKIPPER - Face Tracking with Klipper/Octopus")
print("=" * 60)

# Initialize Klipper motors
motor = get_motor_controller()
if not motor.initialize():
    print("✗ Failed to initialize Klipper. Is Klipper running?")
    print("  Check: curl http://localhost:7125/printer/info")
    sys.exit(1)

print("✓ Klipper motors initialized")
print("✓ Ready for face tracking")
print()

# Import modified tracking logic
print("Starting face tracking with Klipper control...")
print("Use Ctrl+C to stop")
print()

# The actual tracking code will go in follow_face_klipper.py
# For now, let's create a simple test

if __name__ == "__main__":
    print("To integrate with existing face tracking:")
    print("1. Import klipper_motors in your follow_face.py")
    print("2. Replace StepperWorker with Klipper motor control")
    print("3. Use motor.set_azimuth() and motor.set_altitude()")
    print()
    print("Testing motor control...")
    
    import time
    
    try:
        print("Moving azimuth to 10°...")
        motor.set_azimuth(10, speed=20)
        time.sleep(2)
        
        print("Moving altitude to 5°...")
        motor.set_altitude(5, speed=20)
        time.sleep(2)
        
        print("Moving both to center...")
        motor.move_both(0, 0, speed=20)
        time.sleep(2)
        
        print("✓ Motor test complete!")
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        motor.disable_motors()
        print("Motors disabled")
