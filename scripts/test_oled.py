#!/usr/bin/env python3
"""
Test script for MC01506 OLED display connected via TCA9548A multiplexer
OLED is on Channel 0 at address 0x3D
"""

import time
import smbus2
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1327, sh1106, ssd1306
from PIL import ImageFont

# Multiplexer configuration
MUX_ADDR = 0x70
MUX_CHANNEL = 0

# OLED configuration
OLED_ADDR = 0x3D

def select_mux_channel(bus, channel):
    """Select a channel on the TCA9548A multiplexer"""
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be 0-7")
    bus.write_byte(MUX_ADDR, 1 << channel)
    time.sleep(0.01)

def main():
    print("OLED Display Test")
    print("=================")
    print(f"Multiplexer: 0x{MUX_ADDR:02x}")
    print(f"Channel: {MUX_CHANNEL}")
    print(f"OLED Address: 0x{OLED_ADDR:02x}")
    print()
    
    # Select multiplexer channel
    bus = smbus2.SMBus(1)
    select_mux_channel(bus, MUX_CHANNEL)
    print(f"✓ Selected multiplexer channel {MUX_CHANNEL}")
    
    # Initialize OLED
    # Try different controllers - MC01506 128x128 might be SH1106
    print("Trying SH1106 controller...")
    serial = i2c(port=1, address=OLED_ADDR)
    device = sh1106(serial, width=128, height=128, rotate=2)  # rotate=2 flips 180 degrees
    print(f"✓ OLED initialized (128x128 SH1106, rotated 180°)")
    
    # Clear display completely first
    print("Clearing display...")
    device.clear()
    time.sleep(1)
    print()
    
    try:
        # Test 1: Display text
        print("Test 1: Displaying text...")
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            draw.text((10, 10), "Skipper", fill="white")
            draw.text((10, 25), "OLED Test", fill="white")
            draw.text((10, 40), "MC01506", fill="white")
        time.sleep(3)
        
        # Test 2: Animation
        print("Test 2: Simple animation...")
        for i in range(20):
            with canvas(device) as draw:
                x = (i * 6) % 128
                draw.ellipse((x, 20, x+10, 30), outline="white", fill="white")
            time.sleep(0.1)
        
        # Test 3: System info
        print("Test 3: Displaying system info...")
        with canvas(device) as draw:
            draw.text((5, 5), "Status: OK", fill="white")
            draw.text((5, 20), f"Time: {time.strftime('%H:%M:%S')}", fill="white")
            draw.text((5, 35), "Temp: 45C", fill="white")
            draw.text((5, 50), "WiFi: Connected", fill="white")
        time.sleep(3)
        
        # Test 4: Clear display
        print("Test 4: Clearing display...")
        device.clear()
        
        print()
        print("✓ All tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\n✗ Test interrupted")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        # Clear display and close
        device.clear()
        bus.close()
        print("Display cleared and closed")

if __name__ == "__main__":
    main()
