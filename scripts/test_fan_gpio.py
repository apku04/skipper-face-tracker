#!/usr/bin/env python3
"""
GPIO17 Fan Hardware Diagnostic

Tests GPIO17 output and provides troubleshooting steps.
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except:
    print("❌ RPi.GPIO not available")
    sys.exit(1)

PIN_FAN = 17

def test_gpio17():
    print("=" * 60)
    print("GPIO17 Fan Hardware Diagnostic")
    print("=" * 60)
    print()
    print("This will toggle GPIO17 HIGH/LOW repeatedly")
    print("Use a multimeter or LED to verify the signal")
    print()
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_FAN, GPIO.OUT, initial=GPIO.LOW)
    
    print("Testing GPIO17 output...")
    print()
    
    try:
        for i in range(10):
            print(f"[{i+1}/10] GPIO17 = HIGH (3.3V)")
            GPIO.output(PIN_FAN, GPIO.HIGH)
            time.sleep(1)
            
            print(f"[{i+1}/10] GPIO17 = LOW  (0V)")
            GPIO.output(PIN_FAN, GPIO.LOW)
            time.sleep(1)
            print()
            
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        GPIO.output(PIN_FAN, GPIO.LOW)
        GPIO.cleanup()
        print("✅ Test complete - GPIO17 cleaned up")

    print()
    print("=" * 60)
    print("HARDWARE TROUBLESHOOTING")
    print("=" * 60)
    print()
    print("If fan didn't spin, check:")
    print()
    print("1. TRANSISTOR CONNECTION:")
    print("   - Base/Gate → GPIO17")
    print("   - Collector → Fan negative (-)")
    print("   - Emitter → Ground (GND)")
    print("   - Fan positive (+) → 5V or 12V power supply")
    print()
    print("2. VERIFY WITH MULTIMETER:")
    print("   - Measure GPIO17 during HIGH: should be ~3.3V")
    print("   - Measure GPIO17 during LOW: should be ~0V")
    print()
    print("3. TRANSISTOR REQUIREMENTS:")
    print("   - For NPN: Base needs 0.7V+ to turn on")
    print("   - 3.3V from GPIO17 should be sufficient")
    print("   - May need base resistor (1kΩ typical)")
    print()
    print("4. CHECK CONNECTIONS:")
    print("   - GPIO17 pin (physical pin 11)")
    print("   - Ground connection")
    print("   - Fan power supply (separate from Pi if > 5V)")
    print()
    print("5. TEST WITH LED:")
    print("   - Connect LED + resistor (220Ω) between GPIO17 and GND")
    print("   - LED should blink during test")
    print("   - This confirms GPIO17 is working")
    print()

if __name__ == '__main__':
    test_gpio17()
