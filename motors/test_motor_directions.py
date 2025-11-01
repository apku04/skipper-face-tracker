#!/usr/bin/env python3
"""
Interactive test to determine correct motor direction polarity.
This will help you figure out if AZ_DIR_POS_RIGHT and ALT_DIR_POS_DOWN should be True or False.
"""

import sys
import time
from klipper_motors import KlipperMotorController
from config import AppConfig

def main():
    print("=" * 60)
    print("Motor Direction Test")
    print("=" * 60)
    print()
    
    # Initialize motor controller
    cfg = AppConfig()
    motor = KlipperMotorController(
        base_url="http://localhost:7125",
        azimuth_min=cfg.azimuth_min,
        azimuth_max=cfg.azimuth_max,
        altitude_min=cfg.altitude_min,
        altitude_max=cfg.altitude_max
    )
    
    if not motor.initialize():
        print("ERROR: Could not connect to Klipper")
        return
    
    print("✓ Motors initialized")
    print()
    print("IMPORTANT: Stand in front of the camera/robot head")
    print()
    
    # Test Azimuth (horizontal)
    print("=" * 60)
    print("AZIMUTH (Horizontal) Test")
    print("=" * 60)
    print()
    print("The motor will move. Watch which direction it goes.")
    print()
    
    input("Press ENTER to move azimuth with positive angle (+5 degrees)...")
    motor.set_azimuth(5.0, speed=10)
    time.sleep(1)
    
    print()
    response = input("Did the head move to YOUR RIGHT? (y/n): ").strip().lower()
    az_correct = (response == 'y')
    
    print()
    input("Press ENTER to return to center...")
    motor.set_azimuth(0.0, speed=10)
    time.sleep(1)
    
    # Test Altitude (vertical)
    print()
    print("=" * 60)
    print("ALTITUDE (Vertical) Test")
    print("=" * 60)
    print()
    
    input("Press ENTER to move altitude with positive angle (+2 degrees)...")
    motor.set_altitude(2.0, speed=3)
    time.sleep(1)
    
    print()
    response = input("Did the head tilt DOWN? (y/n): ").strip().lower()
    alt_correct = (response == 'y')
    
    print()
    input("Press ENTER to return to center...")
    motor.set_altitude(0.0, speed=3)
    time.sleep(1)
    
    motor.disable_motors()
    
    # Results
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print()
    print(f"Azimuth: Positive angle moved to YOUR RIGHT: {az_correct}")
    print(f"Altitude: Positive angle moved DOWN: {alt_correct}")
    print()
    print("Face tracking logic:")
    print("  - When your face is to the RIGHT of center (dx > 0), motor should move RIGHT (positive)")
    print("  - When your face is BELOW center (dy > 0), motor should move DOWN (positive)")
    print()
    
    # Determine correct polarity settings
    if az_correct:
        print("AZ_DIR_POS_RIGHT should be: True")
        print("  (Positive dx → Positive azimuth → Right)")
    else:
        print("AZ_DIR_POS_RIGHT should be: False")
        print("  (Positive dx → Negative azimuth → Right)")
    
    print()
    
    if alt_correct:
        print("ALT_DIR_POS_DOWN should be: True")
        print("  (Positive dy → Positive altitude → Down)")
    else:
        print("ALT_DIR_POS_DOWN should be: False")
        print("  (Positive dy → Negative altitude → Down)")
    
    print()
    print("=" * 60)
    print(f"Update follow_face.py with:")
    print(f"AZ_DIR_POS_RIGHT = {az_correct}")
    print(f"ALT_DIR_POS_DOWN = {alt_correct}")
    print("=" * 60)

if __name__ == "__main__":
    main()
