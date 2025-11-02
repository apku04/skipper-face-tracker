#!/usr/bin/env python3
"""
Boot Diagnostics Service
Runs diagnostics on boot and displays status via RGB LED

Uses alarm configuration from alarms/alarm_config.yaml
"""

import signal
import sys
import time
import subprocess
import socket
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Warning: RPi.GPIO not available")
    GPIO = None

from utils.logging_config import get_logger, get_data_log_path
from alarms.alarm_manager import AlarmManager

# Global state
running = True
logger = None
alarm_manager = None
gpio_pins = {}

# Diagnostic results
diagnostics = {}

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    if logger:
        logger.info("Shutting down boot diagnostics service...")
    running = False
    cleanup_gpio()
    sys.exit(0)

def setup_gpio():
    """Initialize GPIO pins for RGB LED"""
    global gpio_pins
    
    if not GPIO:
        return
    
    gpio_pins = alarm_manager.get_gpio_pins()
    
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(gpio_pins['red'], GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(gpio_pins['green'], GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(gpio_pins['blue'], GPIO.OUT, initial=GPIO.LOW)

def cleanup_gpio():
    """Clean up GPIO on exit"""
    if not GPIO or not gpio_pins:
        return
    
    GPIO.output(gpio_pins['red'], GPIO.LOW)
    GPIO.output(gpio_pins['green'], GPIO.LOW)
    GPIO.output(gpio_pins['blue'], GPIO.LOW)
    GPIO.cleanup([gpio_pins['red'], gpio_pins['green'], gpio_pins['blue']])

def set_led_rgb(r, g, b):
    """Set LED color by RGB values (0-255)"""
    if not GPIO or not gpio_pins:
        return
    
    GPIO.output(gpio_pins['red'], GPIO.HIGH if r > 0 else GPIO.LOW)
    GPIO.output(gpio_pins['green'], GPIO.HIGH if g > 0 else GPIO.LOW)
    GPIO.output(gpio_pins['blue'], GPIO.HIGH if b > 0 else GPIO.LOW)

def led_off():
    """Turn off LED"""
    set_led_rgb(0, 0, 0)

def blink_led_rgb(r, g, b, duration=0.5):
    """Blink LED once with RGB color"""
    set_led_rgb(r, g, b)
    time.sleep(duration)
    led_off()
    time.sleep(duration)

# Diagnostic Functions

def check_temperature():
    """Check CPU temperature"""
    if not alarm_manager.is_diagnostic_enabled('temperature'):
        return True
    
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp_millidegrees = int(f.read().strip())
            temp_c = temp_millidegrees / 1000.0
        
        warning_temp, critical_temp = alarm_manager.get_temperature_thresholds()
        
        if temp_c >= critical_temp:
            diagnostics['temperature'] = {
                'status': 'critical',
                'message': f'CPU temperature critical: {temp_c:.1f}°C',
                'value': temp_c
            }
        elif temp_c >= warning_temp:
            diagnostics['temperature'] = {
                'status': 'warning',
                'message': f'CPU temperature high: {temp_c:.1f}°C',
                'value': temp_c
            }
        else:
            diagnostics['temperature'] = {
                'status': 'ok',
                'message': f'CPU temperature normal: {temp_c:.1f}°C',
                'value': temp_c
            }
        
        logger.info(diagnostics['temperature']['message'])
        return diagnostics['temperature']['status'] == 'ok'
        
    except Exception as e:
        diagnostics['temperature'] = {
            'status': 'error',
            'message': f'Failed to read temperature: {e}'
        }
        logger.error(diagnostics['temperature']['message'])
        return False

def check_wifi():
    """Check WiFi connectivity"""
    if not alarm_manager.is_diagnostic_enabled('wifi'):
        return True
    
    try:
        wifi_config = alarm_manager.get_diagnostic_config('wifi')
        
        # Check if we have an IP address
        result = subprocess.run(
            ['hostname', '-I'],
            capture_output=True,
            text=True,
            timeout=wifi_config.get('timeout', 5)
        )
        
        ip_addresses = result.stdout.strip()
        
        if ip_addresses:
            # Try to ping a reliable host
            result = subprocess.run(
                ['ping', '-c', str(wifi_config.get('ping_count', 1)), '-W', '2',
                 wifi_config.get('ping_host', '8.8.8.8')],
                capture_output=True,
                timeout=wifi_config.get('timeout', 5)
            )
            
            if result.returncode == 0:
                diagnostics['wifi'] = {
                    'status': 'ok',
                    'message': f'WiFi connected: {ip_addresses}'
                }
                logger.info(diagnostics['wifi']['message'])
                return True
            else:
                diagnostics['wifi'] = {
                    'status': 'error',
                    'message': 'WiFi connected but no internet'
                }
                logger.warning(diagnostics['wifi']['message'])
                return False
        else:
            diagnostics['wifi'] = {
                'status': 'error',
                'message': 'No IP address (WiFi not connected)'
            }
            logger.error(diagnostics['wifi']['message'])
            return False
            
    except Exception as e:
        diagnostics['wifi'] = {
            'status': 'error',
            'message': f'WiFi check failed: {e}'
        }
        logger.error(diagnostics['wifi']['message'])
        return False

def check_klipper():
    """Check if Klipper is accessible"""
    if not alarm_manager.is_diagnostic_enabled('klipper'):
        return True
    
    try:
        klipper_config = alarm_manager.get_diagnostic_config('klipper')
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(klipper_config.get('timeout', 2))
        result = sock.connect_ex((
            klipper_config.get('host', 'localhost'),
            klipper_config.get('port', 7125)
        ))
        sock.close()
        
        if result == 0:
            diagnostics['klipper'] = {
                'status': 'ok',
                'message': 'Klipper/Moonraker accessible'
            }
            logger.info(diagnostics['klipper']['message'])
            return True
        else:
            diagnostics['klipper'] = {
                'status': 'error',
                'message': 'Klipper/Moonraker not accessible'
            }
            logger.warning(diagnostics['klipper']['message'])
            return False
            
    except Exception as e:
        diagnostics['klipper'] = {
            'status': 'error',
            'message': f'Klipper check failed: {e}'
        }
        logger.warning(diagnostics['klipper']['message'])
        return False

def check_camera():
    """Check if camera is available"""
    if not alarm_manager.is_diagnostic_enabled('camera'):
        return True
    
    try:
        camera_config = alarm_manager.get_diagnostic_config('camera')
        camera_devices = camera_config.get('devices', ['/dev/video0', '/dev/video1'])
        
        camera_found = any(Path(p).exists() for p in camera_devices)
        
        if camera_found:
            diagnostics['camera'] = {
                'status': 'ok',
                'message': 'Camera device detected'
            }
            logger.info(diagnostics['camera']['message'])
            return True
        else:
            diagnostics['camera'] = {
                'status': 'error',
                'message': 'No camera device found'
            }
            logger.warning(diagnostics['camera']['message'])
            return False
            
    except Exception as e:
        diagnostics['camera'] = {
            'status': 'error',
            'message': f'Camera check failed: {e}'
        }
        logger.warning(diagnostics['camera']['message'])
        return False

def check_speaker():
    """Check if speaker/audio output is available"""
    if not alarm_manager.is_diagnostic_enabled('speaker'):
        return True
    
    try:
        speaker_config = alarm_manager.get_diagnostic_config('speaker')
        
        result = subprocess.run(
            speaker_config.get('command', ['aplay', '-l']),
            capture_output=True,
            text=True,
            timeout=speaker_config.get('timeout', 5)
        )
        
        if result.returncode == 0 and 'card' in result.stdout.lower():
            diagnostics['speaker'] = {
                'status': 'ok',
                'message': 'Audio output device detected'
            }
            logger.info(diagnostics['speaker']['message'])
            return True
        else:
            diagnostics['speaker'] = {
                'status': 'error',
                'message': 'No audio output device found'
            }
            logger.warning(diagnostics['speaker']['message'])
            return False
            
    except Exception as e:
        diagnostics['speaker'] = {
            'status': 'error',
            'message': f'Speaker check failed: {e}'
        }
        logger.warning(diagnostics['speaker']['message'])
        return False

def check_microphone():
    """Check if microphone/audio input is available (excluding speaker-only devices)"""
    if not alarm_manager.is_diagnostic_enabled('microphone'):
        return True
    
    try:
        mic_config = alarm_manager.get_diagnostic_config('microphone')
        
        result = subprocess.run(
            mic_config.get('command', ['arecord', '-l']),
            capture_output=True,
            text=True,
            timeout=mic_config.get('timeout', 5)
        )
        
        if result.returncode == 0 and result.stdout:
            # Check if there are any dedicated microphone devices
            # Exclude USB Audio devices that are primarily speakers
            output = result.stdout.lower()
            
            # Look for dedicated microphone keywords
            mic_keywords = ['microphone', 'mic', 'respeaker', 'webcam', 'usb audio device']
            has_dedicated_mic = any(keyword in output for keyword in mic_keywords)
            
            # Check if only USB speaker with input (AB13X, etc.)
            is_only_speaker = 'usb audio' in output and not has_dedicated_mic
            
            if has_dedicated_mic:
                diagnostics['microphone'] = {
                    'status': 'ok',
                    'message': 'Dedicated microphone detected'
                }
                logger.info(diagnostics['microphone']['message'])
                return True
            elif is_only_speaker:
                diagnostics['microphone'] = {
                    'status': 'error',
                    'message': 'No dedicated microphone found (only speaker input interface)'
                }
                logger.warning(diagnostics['microphone']['message'])
                return False
            else:
                # Generic audio input found
                diagnostics['microphone'] = {
                    'status': 'ok',
                    'message': 'Audio input device detected'
                }
                logger.info(diagnostics['microphone']['message'])
                return True
        else:
            diagnostics['microphone'] = {
                'status': 'error',
                'message': 'No audio input device found'
            }
            logger.warning(diagnostics['microphone']['message'])
            return False
            
    except Exception as e:
        diagnostics['microphone'] = {
            'status': 'error',
            'message': f'Microphone check failed: {e}'
        }
        logger.warning(diagnostics['microphone']['message'])
        return False

def run_diagnostics():
    """Run all diagnostic checks"""
    logger.info("=== Starting Boot Diagnostics ===")
    
    check_temperature()
    check_wifi()
    check_klipper()
    check_camera()
    check_speaker()
    check_microphone()
    
    logger.info("=== Diagnostics Complete ===")

def save_diagnostics_log():
    """Save diagnostics results to log file"""
    log_file = get_data_log_path("boot_diagnostics", extension="log")
    
    with open(log_file, 'w') as f:
        f.write(f"Boot Diagnostics - {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n\n")
        
        for name, result in diagnostics.items():
            status_symbol = "✓" if result['status'] == 'ok' else "✗"
            f.write(f"{status_symbol} {name.upper()}: {result['status'].upper()}\n")
            f.write(f"   {result['message']}\n\n")
    
    logger.info(f"Diagnostics log saved to: {log_file}")

def display_alarm_led(alarm_config):
    """Display LED pattern based on alarm configuration"""
    global running
    
    if not alarm_config:
        # Default: green solid
        set_led_rgb(0, 255, 0)
        while running:
            time.sleep(1)
        return
    
    led_pattern = alarm_manager.get_led_pattern(alarm_config)
    r, g, b = led_pattern['color']
    
    if led_pattern['blink']:
        # Blinking pattern
        blink_rate = led_pattern['blink_rate']
        while running:
            set_led_rgb(r, g, b)
            time.sleep(blink_rate)
            led_off()
            time.sleep(blink_rate)
    else:
        # Solid pattern
        set_led_rgb(r, g, b)
        while running:
            # For temperature critical, recheck periodically
            if 'temperature' in alarm_config.get('check', ''):
                time.sleep(10)
                check_temperature()
                # Re-evaluate alarm
                _, new_alarm = alarm_manager.get_highest_priority_alarm(diagnostics)
                if new_alarm != alarm_config:
                    # Status changed, update LED
                    return display_alarm_led(new_alarm)
            else:
                time.sleep(1)

def main():
    global running, logger, alarm_manager
    
    # Setup logging
    logger = get_logger('boot_diagnostics', log_to_file=True)
    logger.info("Boot Diagnostics Service starting...")
    
    # Load alarm configuration
    alarm_manager = AlarmManager()
    logger.info("Alarm configuration loaded")
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Setup GPIO
    setup_gpio()
    
    # Phase 1: Blinking during diagnostics
    logger.info("Phase 1: Running diagnostics...")
    
    boot_pattern = alarm_manager.get_boot_pattern()
    boot_config = alarm_manager.get_boot_config()
    blink_color = boot_pattern['color']
    blink_duration = boot_pattern['blink_rate']
    max_blinks = boot_config.get('diagnostic_phase_duration', 10)
    
    for i in range(max_blinks):
        if not running:
            break
        
        blink_led_rgb(*blink_color, duration=blink_duration)
        
        # Run diagnostics during blinking
        if i == 2:
            check_temperature()
        elif i == 3:
            check_wifi()
        elif i == 4:
            check_klipper()
        elif i == 5:
            check_camera()
        elif i == 6:
            check_speaker()
        elif i == 7:
            check_microphone()
    
    # Phase 2: Save diagnostics results
    save_diagnostics_log()
    
    # Phase 3: Determine and display highest priority alarm
    alarm_name, alarm_config = alarm_manager.get_highest_priority_alarm(diagnostics)
    
    if alarm_config:
        logger.info(f"Active alarm: {alarm_name} (priority: {alarm_config.get('priority')})")
        logger.info(f"Message: {alarm_config.get('message')}")
    else:
        logger.info("No active alarms, all systems OK")
    
    # Display the appropriate LED pattern
    display_alarm_led(alarm_config)

if __name__ == "__main__":
    main()
