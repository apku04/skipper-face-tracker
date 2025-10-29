#!/usr/bin/env python3
"""
Test OLED display connection and functionality.
"""

import sys
import time

print("Testing SH1107 OLED Display...")
print("-" * 50)

# Check I2C devices
print("\n1. Scanning I2C bus...")
import subprocess
try:
    result = subprocess.run(['i2cdetect', '-y', '1'], capture_output=True, text=True)
    print(result.stdout)
    if '3c' in result.stdout or '3C' in result.stdout:
        print("✓ Device detected at 0x3C")
    else:
        print("✗ No device at 0x3C")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error running i2cdetect: {e}")
    sys.exit(1)

# Try to initialize display
print("\n2. Initializing display...")
try:
    from luma.core.interface.serial import i2c
    from luma.oled.device import sh1107
    from luma.core.render import canvas
    from PIL import ImageFont
    
    print("✓ Luma packages imported")
    
    # Create serial interface with slower speed
    print("   Creating I2C interface at 0x3C...")
    serial = i2c(port=1, address=0x3C)
    
    print("   Creating SH1107 device (128x128)...")
    device = sh1107(serial, width=128, height=128)
    
    print("✓ Display initialized successfully")
    
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try to draw something
print("\n3. Testing display output...")
try:
    font = ImageFont.load_default()
    
    # Test 1: Simple text
    print("   Test 1: Drawing simple text...")
    with canvas(device) as draw:
        draw.text((10, 10), "Hello!", font=font, fill=255)
    time.sleep(1)
    print("   ✓ Test 1 passed")
    
    # Test 2: Multiple lines
    print("   Test 2: Drawing multiple lines...")
    with canvas(device) as draw:
        draw.text((5, 5), "Line 1", font=font, fill=255)
        draw.text((5, 20), "Line 2", font=font, fill=255)
        draw.text((5, 35), "Line 3", font=font, fill=255)
    time.sleep(1)
    print("   ✓ Test 2 passed")
    
    # Test 3: Clear screen
    print("   Test 3: Clearing display...")
    with canvas(device) as draw:
        pass  # Empty canvas = clear
    time.sleep(0.5)
    print("   ✓ Test 3 passed")
    
    # Test 4: Final message
    print("   Test 4: Final message...")
    with canvas(device) as draw:
        draw.text((10, 50), "Display OK!", font=font, fill=255)
    print("   ✓ Test 4 passed")
    
    print("\n✓ ALL TESTS PASSED!")
    print("\nYour display is working correctly.")
    print("The I2C error in main.py might be due to timing/initialization order.")
    
except OSError as e:
    print(f"\n✗ I/O Error: {e}")
    print("\nPossible causes:")
    print("  1. Display not properly powered")
    print("  2. Loose I2C connections")
    print("  3. I2C bus speed too fast")
    print("  4. Another process using the display")
    print("\nTry:")
    print("  - Check power connections")
    print("  - Re-seat I2C cables")
    print("  - Reboot the Pi")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("Display test completed successfully!")
