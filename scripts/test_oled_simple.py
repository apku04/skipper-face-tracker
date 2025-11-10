#!/usr/bin/env python3
"""
Simple OLED test - try different configurations
"""

import time
import smbus2
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306, sh1106

MUX_ADDR = 0x70
MUX_CHANNEL = 0
OLED_ADDR = 0x3D

def select_mux_channel(bus, channel):
    bus.write_byte(MUX_ADDR, 1 << channel)
    time.sleep(0.01)

def test_display(device, name):
    print(f"\nTesting as {name}...")
    try:
        # Clear display completely
        device.clear()
        time.sleep(0.5)
        
        # Test 1: Simple filled rectangle
        print("  Drawing rectangle...")
        with canvas(device) as draw:
            draw.rectangle((10, 5, 50, 25), outline="white", fill="white")
        time.sleep(2)
        
        # Test 2: Text
        print("  Drawing text...")
        device.clear()
        with canvas(device) as draw:
            draw.text((10, 10), "HELLO", fill="white")
        time.sleep(2)
        
        # Clear
        device.clear()
        print(f"  ✓ {name} test complete")
        return True
        
    except Exception as e:
        print(f"  ✗ Error with {name}: {e}")
        return False

bus = smbus2.SMBus(1)
select_mux_channel(bus, MUX_CHANNEL)
print(f"Selected multiplexer channel {MUX_CHANNEL}")

# Try different configurations
configs = [
    ("SSD1306 128x64", lambda: ssd1306(i2c(port=1, address=OLED_ADDR), width=128, height=64)),
    ("SSD1306 128x32", lambda: ssd1306(i2c(port=1, address=OLED_ADDR), width=128, height=32)),
    ("SH1106 128x64", lambda: sh1106(i2c(port=1, address=OLED_ADDR), width=128, height=64)),
]

for name, device_func in configs:
    try:
        device = device_func()
        if test_display(device, name):
            print(f"\n✓ SUCCESS: Display works as {name}")
            device.clear()
            break
    except Exception as e:
        print(f"\n✗ Failed to initialize {name}: {e}")

bus.close()
