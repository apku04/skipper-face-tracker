#!/usr/bin/env python3
"""
Test robot head movement with Klipper motors.
Moves the head in a pattern to verify motor control.
"""

import sys
import time
sys.path.insert(0, '/home/pi/work/skipper')

from klipper_motors import KlipperMotorController

def main():
    print("=" * 60)
    print("Robot Head Movement Test")
    print("=" * 60)
    print()
    
    # Initialize motor controller
    print("1. Connecting to Klipper...")
    motor = KlipperMotorController(base_url="http://localhost:7125")
    
    if not motor.initialize():
        print("ERROR: Could not connect to Klipper!")
        print("Make sure Klipper and Moonraker are running:")
        print("  sudo systemctl status klipper moonraker")
        return 1
    
    print("   ✓ Connected to Klipper")
    print()
    
    # Set starting position
    print("2. Setting current position as zero...")
    motor._send_gcode("SET_KINEMATIC_POSITION X=0 Y=0 Z=0")
    time.sleep(0.5)
    print("   ✓ Position set to (0, 0)")
    print()
    
    print("3. Starting movement test sequence...")
    print("   Press Ctrl+C to stop at any time")
    print()
    
    try:
        # Test 1: Center position
        print("   Test 1: Return to center (0°, 0°)...")
        motor.move_both(azimuth=0, altitude=0, speed=20)
        time.sleep(2)
        print("   ✓ At center")
        
        # Test 2: Look left
        print("   Test 2: Look left (-20°, 0°)...")
        motor.set_azimuth(-20, speed=20)
        time.sleep(2)
        print("   ✓ Looking left")
        
        # Test 3: Look right
        print("   Test 3: Look right (+20°, 0°)...")
        motor.set_azimuth(20, speed=20)
        time.sleep(2)
        print("   ✓ Looking right")
        
        # Test 4: Return to center
        print("   Test 4: Return to center...")
        motor.set_azimuth(0, speed=20)
        time.sleep(2)
        
        # Test 5: Look up
        print("   Test 5: Look up (0°, +15°)...")
        motor.set_altitude(15, speed=20)
        time.sleep(2)
        print("   ✓ Looking up")
        
        # Test 6: Look down
        print("   Test 6: Look down (0°, -15°)...")
        motor.set_altitude(-15, speed=20)
        time.sleep(2)
        print("   ✓ Looking down")
        
        # Test 7: Return to center
        print("   Test 7: Return to center...")
        motor.move_both(azimuth=0, altitude=0, speed=20)
        time.sleep(2)
        
        # Test 8: Circle pattern
        print("   Test 8: Circle pattern...")
        positions = [
            (10, 10),   # Upper right
            (10, -10),  # Lower right
            (-10, -10), # Lower left
            (-10, 10),  # Upper left
            (0, 0)      # Center
        ]
        
        for i, (az, alt) in enumerate(positions, 1):
            print(f"      Position {i}/5: ({az:+3d}°, {alt:+3d}°)")
            motor.move_both(azimuth=az, altitude=alt, speed=25)
            time.sleep(1.5)
        
        print("   ✓ Circle complete")
        
        # Final: Return to center
        print()
        print("4. Returning to center position...")
        motor.move_both(azimuth=0, altitude=0, speed=20)
        time.sleep(2)
        
        print()
        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Your robot head is working correctly with Klipper control!")
        print()
        
        # Disable motors to save power
        print("Disabling motors...")
        motor.disable_motors()
        print("✓ Motors disabled")
        
        return 0
        
    except KeyboardInterrupt:
        print()
        print()
        print("Test interrupted by user")
        print("Returning to center...")
        motor.move_both(azimuth=0, altitude=0, speed=20)
        time.sleep(2)
        motor.disable_motors()
        return 0
        
    except Exception as e:
        print()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
