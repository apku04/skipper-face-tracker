"""
Simple OLED display driver for MC01506 (SH1106 128x128)
Connected via TCA9548A I2C multiplexer on Channel 0 at address 0x3D

Thread-safe library for displaying status information.
"""

import threading
import time
from typing import Optional, Dict, List
import smbus2
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import ImageFont

# Hardware configuration
MUX_ADDR = 0x70
MUX_CHANNEL = 0
OLED_ADDR = 0x3D
OLED_WIDTH = 128
OLED_HEIGHT = 128

# Global state
_device: Optional[sh1106] = None
_bus: Optional[smbus2.SMBus] = None
_lock = threading.Lock()
_initialized = False


def _select_mux_channel():
    """Select the multiplexer channel for the OLED"""
    global _bus
    if _bus is None:
        _bus = smbus2.SMBus(1)
    _bus.write_byte(MUX_ADDR, 1 << MUX_CHANNEL)
    time.sleep(0.01)


def init_display() -> bool:
    """
    Initialize the OLED display
    
    Returns:
        bool: True if successful, False otherwise
    """
    global _device, _initialized
    
    with _lock:
        if _initialized and _device:
            return True
        
        try:
            # Select multiplexer channel
            _select_mux_channel()
            
            # Initialize OLED with 180° rotation
            serial = i2c(port=1, address=OLED_ADDR)
            _device = sh1106(serial, width=OLED_WIDTH, height=OLED_HEIGHT, rotate=2)
            
            # Clear display
            _device.clear()
            _initialized = True
            return True
            
        except Exception as e:
            print(f"Failed to initialize OLED display: {e}")
            _initialized = False
            return False


def clear() -> bool:
    """
    Clear the display
    
    Returns:
        bool: True if successful, False otherwise
    """
    global _device
    
    with _lock:
        if not _initialized or not _device:
            return False
        
        try:
            _select_mux_channel()
            _device.clear()
            return True
        except Exception as e:
            print(f"Failed to clear display: {e}")
            return False


def show_text(lines: List[str], font_size: int = 10) -> bool:
    """
    Display multiple lines of text
    
    Args:
        lines: List of text strings to display
        font_size: Font size in pixels (default: 10)
    
    Returns:
        bool: True if successful, False otherwise
    """
    global _device
    
    with _lock:
        if not _initialized or not _device:
            if not init_display():
                return False
        
        try:
            _select_mux_channel()
            
            with canvas(_device) as draw:
                y = 5
                line_height = font_size + 4
                
                for line in lines:
                    if y + line_height > OLED_HEIGHT:
                        break  # Out of space
                    draw.text((5, y), line, fill="white")
                    y += line_height
            
            return True
            
        except Exception as e:
            print(f"Failed to show text: {e}")
            return False


def show_status(status: Dict[str, any]) -> bool:
    """
    Display system status from boot diagnostics
    
    Args:
        status: Dictionary with diagnostic results
                Expected keys: temperature, wifi, klipper, camera, speaker, microphone
                Each value should have 'status' and 'message' fields
    
    Returns:
        bool: True if successful, False otherwise
    """
    global _device
    
    with _lock:
        if not _initialized or not _device:
            if not init_display():
                return False
        
        try:
            _select_mux_channel()
            
            # Map status to text indicators
            status_text = {
                'ok': 'OK',
                'warning': 'WRN',
                'error': 'ERR',
                'critical': 'CRIT'
            }
            
            with canvas(_device) as draw:
                # Title
                draw.text((5, 2), "System Status", fill="white")
                draw.line((5, 14, 123, 14), fill="white")
                
                y = 18
                line_height = 15
                
                # Display each diagnostic check
                checks = [
                    ('TEMP', status.get('temperature', {})),
                    ('WiFi', status.get('wifi', {})),
                    ('Klip', status.get('klipper', {})),
                    ('Cam', status.get('camera', {})),
                    ('Spkr', status.get('speaker', {})),
                    ('Mic', status.get('microphone', {})),
                ]
                
                for label, check_result in checks:
                    if y + line_height > OLED_HEIGHT - 20:
                        break
                    
                    check_status = check_result.get('status', 'unknown')
                    status_indicator = status_text.get(check_status, '???')
                    
                    # Draw label and status on same line
                    draw.text((5, y), label, fill="white")
                    draw.text((50, y), status_indicator, fill="white")
                    
                    y += line_height
                
                # Show overall status at bottom
                if y < OLED_HEIGHT - 16:
                    draw.line((5, y + 2, 123, y + 2), fill="white")
                    
                    # Count issues
                    errors = sum(1 for _, v in checks if v.get('status') in ['error', 'critical'])
                    warnings = sum(1 for _, v in checks if v.get('status') == 'warning')
                    
                    if errors > 0:
                        draw.text((5, y + 6), f"Errors: {errors}", fill="white")
                    elif warnings > 0:
                        draw.text((5, y + 6), f"Warns: {warnings}", fill="white")
                    else:
                        draw.text((5, y + 6), "All OK", fill="white")
            
            return True
            
        except Exception as e:
            print(f"Failed to show status: {e}")
            return False


def show_diagnostics_summary(diagnostics: Dict[str, Dict]) -> bool:
    """
    Display a summary of diagnostic results with better formatting
    
    Args:
        diagnostics: Dictionary of diagnostic results from boot_diagnostics
    
    Returns:
        bool: True if successful, False otherwise
    """
    return show_status(diagnostics)


def close() -> bool:
    """
    Close the display and release resources
    
    Returns:
        bool: True if successful, False otherwise
    """
    global _device, _bus, _initialized
    
    with _lock:
        if not _initialized:
            return True
        
        try:
            if _device:
                _select_mux_channel()
                _device.clear()
                _device = None
            
            if _bus:
                _bus.close()
                _bus = None
            
            _initialized = False
            return True
            
        except Exception as e:
            print(f"Failed to close display: {e}")
            return False


def is_initialized() -> bool:
    """
    Check if display is initialized
    
    Returns:
        bool: True if initialized, False otherwise
    """
    with _lock:
        return _initialized


# Convenience function for quick text display
def quick_display(text: str, duration: float = 3.0) -> bool:
    """
    Quickly display text for a duration, then clear
    
    Args:
        text: Text to display (will be split into lines if needed)
        duration: How long to show the text in seconds
    
    Returns:
        bool: True if successful, False otherwise
    """
    lines = text.split('\n')
    if show_text(lines):
        time.sleep(duration)
        clear()
        return True
    return False
