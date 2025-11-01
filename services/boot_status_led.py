#!/usr/bin/env python3
"""
Boot Status LED Service

Turns on yellow LED (R+G) on boot to indicate system is online.
This runs as a systemd service on every boot.

LED: Yellow = Red (GPIO23) + Green (GPIO22) ON
"""

import time
import sys
import signal

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO not available")
    sys.exit(1)

# GPIO pins
PIN_R = 23
PIN_G = 22
PIN_B = 27

def setup_gpio():
    """Initialize GPIO for LED control"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIN_R, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_G, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_B, GPIO.OUT, initial=GPIO.LOW)

def set_yellow():
    """Turn on yellow LED (Red + Green)"""
    GPIO.output(PIN_R, GPIO.HIGH)
    GPIO.output(PIN_G, GPIO.HIGH)
    GPIO.output(PIN_B, GPIO.LOW)

def cleanup(signum=None, frame=None):
    """Clean shutdown - turn off all LEDs"""
    GPIO.output(PIN_R, GPIO.LOW)
    GPIO.output(PIN_G, GPIO.LOW)
    GPIO.output(PIN_B, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)

def main():
    """Main service loop"""
    print("Boot Status LED Service starting...")
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    
    # Initialize GPIO
    setup_gpio()
    
    # Turn on yellow LED
    set_yellow()
    print("✅ Yellow LED ON - System online")
    
    # Keep running until killed
    try:
        while True:
            time.sleep(60)  # Sleep to keep service alive
    except KeyboardInterrupt:
        cleanup()

if __name__ == '__main__':
    main()
