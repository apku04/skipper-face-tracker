#!/usr/bin/env python3
"""
Motor Calibration Tool for Skipper Robot Head

This tool helps you safely find the physical limits of your robot head
and configure the motion boundaries.
"""

import sys
import time
from klipper_motors import KlipperMotorController

def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def get_float_input(prompt, default=None):
    """Get float input from user with optional default."""
    if default is not None:
        prompt = f"{prompt} (default: {default}): "
    else:
        prompt = f"{prompt}: "
    
    while True:
        try:
            response = input(prompt).strip()
            if not response and default is not None:
                return default
            return float(response)
        except ValueError:
            print("Please enter a valid number")

def manual_jog(motor, axis_name, default_speed=10):
    """Manual jogging mode to find limits."""
    print(f"\n--- Manual Jog Mode: {axis_name} ---")
    print("Commands:")
    print("  +[amount] : Move positive (e.g., +5)")
    print("  -[amount] : Move negative (e.g., -5)")
    print("  0         : Return to zero")
    print("  done      : Finish and record limit")
    print()
    
    current_pos = 0.0
    speed = default_speed  # Use provided default speed
    
    while True:
        cmd = input(f"Current position: {current_pos:.1f}° > ").strip().lower()
        
        if cmd == "done":
            return current_pos
        elif cmd == "0":
            if axis_name == "Azimuth":
                motor.set_azimuth(0, speed)
            else:
                motor.set_altitude(0, speed)
            current_pos = 0.0
            time.sleep(0.5)
        elif cmd.startswith('+') or cmd.startswith('-'):
            try:
                delta = float(cmd)
                current_pos += delta
                
                if axis_name == "Azimuth":
                    motor.set_azimuth(current_pos, speed)
                else:
                    motor.set_altitude(current_pos, speed)
                
                time.sleep(0.5)
                print(f"Moved to {current_pos:.1f}°")
            except ValueError:
                print("Invalid command. Use format: +5 or -10")
        else:
            print("Invalid command")

def main():
    print_header("Skipper Robot Head Calibration")
    print("\nThis tool will help you safely find the motion limits")
    print("of your robot head and configure boundaries.")
    print("\n⚠  IMPORTANT: Watch the robot head carefully during calibration!")
    print("   Stop before hitting any physical limits.")
    
    input("\nPress ENTER when ready to start...")
    
    # Initialize motor controller
    print("\nConnecting to Klipper...")
    motor = KlipperMotorController()
    
    if not motor.initialize():
        print("✗ Failed to connect to Klipper")
        return 1
    
    print("✓ Connected")
    
    # Start with slow test movements
    print_header("Initial Test Movement")
    print("\nFirst, let's do a small test movement to verify direction.")
    print("The head will move +2° in azimuth (pan)...")
    
    input("Press ENTER to test...")
    motor.set_azimuth(2, 5)
    time.sleep(1)
    
    response = input("\nDid the head move LEFT? (yes/no): ").strip().lower()
    if response != 'yes':
        print("\n⚠  Direction may be reversed. You may need to add '!' to dir_pin")
        print("   in your printer.cfg for stepper_0")
    
    motor.set_azimuth(0, 5)
    time.sleep(1)
    
    # Calibrate Azimuth (Pan) - Left/Right
    print_header("Calibrate Azimuth (Pan/Left-Right)")
    print("\nWe'll find the left and right limits.")
    print("Move in small increments (+5 or -5) and stop BEFORE hitting limits.")
    
    input("\nPress ENTER to start azimuth calibration...")
    
    print("\n1. Find LEFT limit (negative direction):")
    print("   Start with small moves like -5, -10, etc.")
    left_limit = manual_jog(motor, "Azimuth")
    print(f"\n✓ Left limit recorded: {left_limit:.1f}°")
    
    # Return to center
    motor.set_azimuth(0, 10)
    time.sleep(1)
    
    print("\n2. Find RIGHT limit (positive direction):")
    print("   Start with small moves like +5, +10, etc.")
    right_limit = manual_jog(motor, "Azimuth")
    print(f"\n✓ Right limit recorded: {right_limit:.1f}°")
    
    # Return to center
    motor.set_azimuth(0, 10)
    time.sleep(2)
    
    # Calibrate Altitude (Tilt) - Up/Down
    print_header("Calibrate Altitude (Tilt/Up-Down)")
    print("\nNow we'll find the up and down limits.")
    print("⚠  NOTE: Altitude uses EXTREMELY slow speed (2°/s) for ultra-smooth motion")
    
    input("\nPress ENTER to start altitude calibration...")
    
    print("\n1. Find DOWN limit (negative direction):")
    print("   Start with small moves like -5, -10, etc.")
    down_limit = manual_jog(motor, "Altitude", default_speed=2)  # Super slow!
    print(f"\n✓ Down limit recorded: {down_limit:.1f}°")
    
    # Return to center
    motor.set_altitude(0, 2)  # Super slow speed
    time.sleep(1)
    
    print("\n2. Find UP limit (positive direction):")
    print("   Start with small moves like +5, +10, etc.")
    up_limit = manual_jog(motor, "Altitude", default_speed=2)  # Super slow!
    print(f"\n✓ Up limit recorded: {up_limit:.1f}°")
    
    # Return to center
    motor.set_altitude(0, 2)  # Super slow speed
    time.sleep(1)
    
    # Apply safety margin
    print_header("Safety Margins")
    print("\nRecommend adding safety margins to avoid hitting limits.")
    
    safety_margin = get_float_input("Enter safety margin in degrees", 2.0)
    
    azimuth_min = left_limit + safety_margin
    azimuth_max = right_limit - safety_margin
    altitude_min = down_limit + safety_margin
    altitude_max = up_limit - safety_margin
    
    # Generate config
    print_header("Calibration Complete!")
    print("\nYour calibrated limits:")
    print(f"  Azimuth (Pan):   {azimuth_min:.1f}° to {azimuth_max:.1f}°")
    print(f"  Altitude (Tilt): {altitude_min:.1f}° to {altitude_max:.1f}°")
    
    print("\n" + "-"*60)
    print("Add this to your config.py:")
    print("-"*60)
    print(f"""
# Motor limits (calibrated)
azimuth_min = {azimuth_min:.1f}
azimuth_max = {azimuth_max:.1f}
altitude_min = {altitude_min:.1f}
altitude_max = {altitude_max:.1f}
""")
    print("-"*60)
    
    # Test the limits
    print("\nWould you like to test the configured limits?")
    response = input("This will move to each limit point (yes/no): ").strip().lower()
    
    if response == 'yes':
        print("\nTesting limits...")
        positions = [
            ("Center", 0, 0),
            ("Left limit", azimuth_min, 0),
            ("Center", 0, 0),
            ("Right limit", azimuth_max, 0),
            ("Center", 0, 0),
            ("Down limit", 0, altitude_min),
            ("Center", 0, 0),
            ("Up limit", 0, altitude_max),
            ("Center", 0, 0),
        ]
        
        for name, az, alt in positions:
            print(f"  → {name}: ({az:.1f}°, {alt:.1f}°)")
            motor.move_both(az, alt, 20)
            time.sleep(2)
        
        print("\n✓ Limit test complete!")
    
    motor.disable_motors()
    print("\n✓ Motors disabled. Calibration complete!")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Calibration interrupted by user")
        try:
            motor = KlipperMotorController()
            motor.disable_motors()
        except:
            pass
        sys.exit(1)
