#!/usr/bin/env python3
"""
ReSpeaker 2-Mic HAT Amplifier Enable
Some versions require GPIO 12 to be HIGH to enable the speaker amplifier
"""

import sys
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO not available, trying gpiod...")
    try:
        import gpiod
        USE_GPIOD = True
    except ImportError:
        print("Neither RPi.GPIO nor gpiod available")
        sys.exit(1)
    USE_GPIOD = True
else:
    USE_GPIOD = False

AMP_ENABLE_PIN = 12  # BCM pin 12

def enable_amp_gpio():
    """Enable amplifier using RPi.GPIO"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(AMP_ENABLE_PIN, GPIO.OUT)
    GPIO.output(AMP_ENABLE_PIN, GPIO.HIGH)
    print(f"✓ Enabled amplifier on GPIO {AMP_ENABLE_PIN} (RPi.GPIO)")

def enable_amp_gpiod():
    """Enable amplifier using gpiod"""
    chip = gpiod.Chip('gpiochip4')  # Pi 5 uses gpiochip4
    line = chip.get_line(AMP_ENABLE_PIN)
    line.request(consumer="respeaker", type=gpiod.LINE_REQ_DIR_OUT)
    line.set_value(1)
    print(f"✓ Enabled amplifier on GPIO {AMP_ENABLE_PIN} (gpiod)")
    # Keep the script running to maintain GPIO state
    print("\nAmplifier enabled. Press Ctrl+C to disable and exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        line.set_value(0)
        print("\n✓ Amplifier disabled")

def main():
    print("=" * 50)
    print("ReSpeaker Amplifier Enable")
    print("=" * 50)
    print(f"\nEnabling amplifier on GPIO {AMP_ENABLE_PIN}...")
    
    try:
        if USE_GPIOD:
            enable_amp_gpiod()
        else:
            enable_amp_gpio()
            print("\nAmplifier enabled. Now try playing audio.")
            print("This script will keep running. Press Ctrl+C to exit.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                GPIO.output(AMP_ENABLE_PIN, GPIO.LOW)
                GPIO.cleanup()
                print("\n✓ Amplifier disabled")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
