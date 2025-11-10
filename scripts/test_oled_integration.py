#!/usr/bin/env python3
"""
Test OLED display with sample diagnostic data
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import oled_display

# Sample diagnostic data (similar to boot_diagnostics output)
sample_diagnostics = {
    'temperature': {
        'status': 'ok',
        'message': 'CPU temperature normal: 45.8°C',
        'value': 45.8
    },
    'wifi': {
        'status': 'ok',
        'message': 'WiFi connected: 192.168.1.243'
    },
    'klipper': {
        'status': 'ok',
        'message': 'Klipper/Moonraker accessible'
    },
    'camera': {
        'status': 'ok',
        'message': 'Camera device detected'
    },
    'speaker': {
        'status': 'warning',
        'message': 'No audio output device found'
    },
    'microphone': {
        'status': 'error',
        'message': 'No dedicated microphone found'
    }
}

def main():
    print("OLED Display Integration Test")
    print("=" * 40)
    
    # Initialize display
    print("Initializing display...")
    if not oled_display.init_display():
        print("✗ Failed to initialize display")
        return 1
    print("✓ Display initialized")
    
    # Show sample status
    print("\nDisplaying sample diagnostics...")
    if not oled_display.show_status(sample_diagnostics):
        print("✗ Failed to show status")
        return 1
    print("✓ Status displayed")
    
    print("\nDisplay will show for 10 seconds...")
    print("Check your OLED - you should see:")
    print("  - System Status header")
    print("  - ✓ TEMP, WiFi, Klip, Cam")
    print("  - ! Spkr (warning)")
    print("  - ✗ Mic (error)")
    print("  - Summary: Errors: 1")
    
    import time
    time.sleep(10)
    
    # Test text display
    print("\nTesting text display...")
    oled_display.show_text([
        "Text Display Test",
        "Line 2",
        "Line 3",
        "This is a longer line"
    ])
    print("✓ Text displayed (5 seconds)")
    time.sleep(5)
    
    # Clear display
    print("\nClearing display...")
    if not oled_display.clear():
        print("✗ Failed to clear")
        return 1
    print("✓ Display cleared")
    
    # Close
    print("\nClosing display...")
    if not oled_display.close():
        print("✗ Failed to close")
        return 1
    print("✓ Display closed")
    
    print("\n" + "=" * 40)
    print("All tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
