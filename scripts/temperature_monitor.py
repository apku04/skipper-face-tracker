#!/usr/bin/env python3
"""
Temperature Monitor - Continuously monitor SHT3x and CPU temperatures
Measures ambient temperature (SHT3x at 0x44) and CPU temperature every 2 seconds
"""

import time
import smbus2
import struct
import signal
import sys
from datetime import datetime

# SHT3x Configuration
SHT3X_ADDR = 0x44
I2C_BUS = 1

# Global flag for graceful shutdown
running = True

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    print("\n\nShutting down temperature monitor...")
    running = False
    sys.exit(0)

def read_sht3x_temp_humidity():
    """
    Read temperature and humidity from SHT3x sensor at 0x44
    Returns: (temperature_C, humidity_percent) or (None, None) on error
    """
    try:
        bus = smbus2.SMBus(I2C_BUS)
        
        # Send measurement command (high repeatability, clock stretching disabled)
        # Command: 0x2400
        bus.write_i2c_block_data(SHT3X_ADDR, 0x24, [0x00])
        
        # Wait for measurement (max 15ms for high repeatability)
        time.sleep(0.02)
        
        # Read 6 bytes: temp MSB, temp LSB, temp CRC, humidity MSB, humidity LSB, humidity CRC
        data = bus.read_i2c_block_data(SHT3X_ADDR, 0x00, 6)
        bus.close()
        
        # Convert temperature data
        temp_raw = (data[0] << 8) | data[1]
        temp_c = -45 + (175 * temp_raw / 65535.0)
        
        # Convert humidity data
        humidity_raw = (data[3] << 8) | data[4]
        humidity = 100 * humidity_raw / 65535.0
        
        return temp_c, humidity
        
    except Exception as e:
        return None, None

def read_cpu_temperature():
    """
    Read Raspberry Pi CPU temperature from thermal zone
    Returns: temperature_C or None on error
    """
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp_millidegrees = int(f.read().strip())
            temp_c = temp_millidegrees / 1000.0
            return temp_c
    except Exception as e:
        return None

def format_temp_bar(temp, min_temp=20, max_temp=80):
    """
    Create a visual temperature bar
    """
    if temp is None:
        return "[" + " " * 20 + "]"
    
    # Clamp temperature to range
    temp_clamped = max(min_temp, min(max_temp, temp))
    bar_length = int(((temp_clamped - min_temp) / (max_temp - min_temp)) * 20)
    
    # Color coding
    if temp < 40:
        bar_char = "▓"  # Cool
    elif temp < 60:
        bar_char = "▓"  # Moderate
    else:
        bar_char = "█"  # Hot
    
    bar = bar_char * bar_length + "░" * (20 - bar_length)
    return f"[{bar}]"

def display_header():
    """Display monitoring header"""
    print("\n" + "=" * 80)
    print("  TEMPERATURE MONITOR - SHT3x (Ambient) + CPU")
    print("=" * 80)
    print(f"  SHT3x Address: 0x{SHT3X_ADDR:02X} (I2C Bus {I2C_BUS})")
    print(f"  Update Interval: 2 seconds")
    print(f"  Press Ctrl+C to stop")
    print("=" * 80)
    print()
    print(f"{'Time':<12} {'Ambient (SHT3x)':<25} {'CPU Temp':<25} {'Humidity':<12}")
    print("-" * 80)

def main():
    global running
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Display header
    display_header()
    
    # Statistics tracking
    sht3x_temps = []
    cpu_temps = []
    
    try:
        while running:
            # Get current time
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Read SHT3x sensor
            ambient_temp, humidity = read_sht3x_temp_humidity()
            
            # Read CPU temperature
            cpu_temp = read_cpu_temperature()
            
            # Track for statistics
            if ambient_temp is not None:
                sht3x_temps.append(ambient_temp)
            if cpu_temp is not None:
                cpu_temps.append(cpu_temp)
            
            # Format output
            if ambient_temp is not None:
                ambient_str = f"{ambient_temp:5.2f}°C {format_temp_bar(ambient_temp, 15, 50)}"
            else:
                ambient_str = "ERROR" + " " * 20
            
            if cpu_temp is not None:
                cpu_str = f"{cpu_temp:5.2f}°C {format_temp_bar(cpu_temp, 30, 85)}"
            else:
                cpu_str = "ERROR" + " " * 20
            
            if humidity is not None:
                humidity_str = f"{humidity:5.2f}%"
            else:
                humidity_str = "ERROR"
            
            # Calculate delta (CPU - Ambient)
            if ambient_temp is not None and cpu_temp is not None:
                delta = cpu_temp - ambient_temp
                delta_str = f"Δ {delta:+5.2f}°C"
            else:
                delta_str = ""
            
            # Print reading
            print(f"{current_time:<12} {ambient_str:<25} {cpu_str:<25} {humidity_str:<12} {delta_str}")
            
            # Wait 2 seconds
            time.sleep(2)
            
    except KeyboardInterrupt:
        signal_handler(None, None)
    
    finally:
        # Print statistics
        print("\n" + "-" * 80)
        print("  STATISTICS")
        print("-" * 80)
        
        if sht3x_temps:
            print(f"  Ambient (SHT3x):  Min: {min(sht3x_temps):.2f}°C  "
                  f"Max: {max(sht3x_temps):.2f}°C  "
                  f"Avg: {sum(sht3x_temps)/len(sht3x_temps):.2f}°C  "
                  f"Samples: {len(sht3x_temps)}")
        
        if cpu_temps:
            print(f"  CPU Temperature:  Min: {min(cpu_temps):.2f}°C  "
                  f"Max: {max(cpu_temps):.2f}°C  "
                  f"Avg: {sum(cpu_temps)/len(cpu_temps):.2f}°C  "
                  f"Samples: {len(cpu_temps)}")
        
        if sht3x_temps and cpu_temps:
            deltas = [c - a for c, a in zip(cpu_temps, sht3x_temps)]
            print(f"  Temperature Delta: Min: {min(deltas):.2f}°C  "
                  f"Max: {max(deltas):.2f}°C  "
                  f"Avg: {sum(deltas)/len(deltas):.2f}°C")
        
        print("=" * 80)

if __name__ == "__main__":
    main()
