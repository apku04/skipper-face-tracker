#!/usr/bin/env python3
"""
Read BMP280 sensor on TCA9548A Channel 1
=========================================

Reads temperature and pressure from BMP280 sensor connected
to TCA9548A multiplexer channel 1.

Usage:
    python3 scripts/read_bmp280_ch1.py
"""

import time
import smbus2 as smbus

# I2C addresses
MUX_ADDR = 0x70
BMP280_ADDR = 0x76

# BMP280 registers
BMP280_REG_ID = 0xD0
BMP280_REG_CTRL_MEAS = 0xF4
BMP280_REG_CONFIG = 0xF5
BMP280_REG_TEMP_MSB = 0xFA
BMP280_REG_PRESS_MSB = 0xF7

# Calibration registers
BMP280_REG_DIG_T1 = 0x88

def select_mux_channel(bus, channel):
    """Select TCA9548A channel"""
    bus.write_byte(MUX_ADDR, 1 << channel)

def read_calibration(bus):
    """Read BMP280 calibration data"""
    cal = {}
    
    # Temperature calibration
    data = bus.read_i2c_block_data(BMP280_ADDR, BMP280_REG_DIG_T1, 6)
    cal['T1'] = data[0] | (data[1] << 8)
    cal['T2'] = data[2] | (data[3] << 8)
    if cal['T2'] > 32767:
        cal['T2'] -= 65536
    cal['T3'] = data[4] | (data[5] << 8)
    if cal['T3'] > 32767:
        cal['T3'] -= 65536
    
    # Pressure calibration
    data = bus.read_i2c_block_data(BMP280_ADDR, 0x8E, 18)
    cal['P1'] = data[0] | (data[1] << 8)
    cal['P2'] = data[2] | (data[3] << 8)
    if cal['P2'] > 32767:
        cal['P2'] -= 65536
    cal['P3'] = data[4] | (data[5] << 8)
    if cal['P3'] > 32767:
        cal['P3'] -= 65536
    cal['P4'] = data[6] | (data[7] << 8)
    if cal['P4'] > 32767:
        cal['P4'] -= 65536
    cal['P5'] = data[8] | (data[9] << 8)
    if cal['P5'] > 32767:
        cal['P5'] -= 65536
    cal['P6'] = data[10] | (data[11] << 8)
    if cal['P6'] > 32767:
        cal['P6'] -= 65536
    cal['P7'] = data[12] | (data[13] << 8)
    if cal['P7'] > 32767:
        cal['P7'] -= 65536
    cal['P8'] = data[14] | (data[15] << 8)
    if cal['P8'] > 32767:
        cal['P8'] -= 65536
    cal['P9'] = data[16] | (data[17] << 8)
    if cal['P9'] > 32767:
        cal['P9'] -= 65536
    
    return cal

def compensate_temperature(adc_T, cal):
    """Compensate temperature reading"""
    var1 = (((adc_T >> 3) - (cal['T1'] << 1)) * cal['T2']) >> 11
    var2 = (((((adc_T >> 4) - cal['T1']) * ((adc_T >> 4) - cal['T1'])) >> 12) * cal['T3']) >> 14
    t_fine = var1 + var2
    temperature = (t_fine * 5 + 128) >> 8
    return temperature / 100.0, t_fine

def compensate_pressure(adc_P, t_fine, cal):
    """Compensate pressure reading"""
    var1 = t_fine - 128000
    var2 = var1 * var1 * cal['P6']
    var2 = var2 + ((var1 * cal['P5']) << 17)
    var2 = var2 + (cal['P4'] << 35)
    var1 = ((var1 * var1 * cal['P3']) >> 8) + ((var1 * cal['P2']) << 12)
    var1 = ((1 << 47) + var1) * cal['P1'] >> 33
    
    if var1 == 0:
        return 0  # Avoid division by zero
    
    p = 1048576 - adc_P
    p = (((p << 31) - var2) * 3125) // var1
    var1 = (cal['P9'] * (p >> 13) * (p >> 13)) >> 25
    var2 = (cal['P8'] * p) >> 19
    pressure = ((p + var1 + var2) >> 8) + (cal['P7'] << 4)
    
    return pressure / 256.0 / 100.0  # Convert to hPa

def read_bmp280(bus):
    """Read BMP280 sensor"""
    # Read raw data
    data = bus.read_i2c_block_data(BMP280_ADDR, BMP280_REG_PRESS_MSB, 6)
    
    adc_P = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
    adc_T = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
    
    return adc_T, adc_P

def main():
    print("=" * 60)
    print("BMP280 Sensor Reader (TCA9548A Channel 1)")
    print("=" * 60)
    print()
    
    # Open I2C bus
    bus = smbus.SMBus(1)
    
    # Select channel 1
    print("Selecting multiplexer channel 1...")
    select_mux_channel(bus, 1)
    
    # Check sensor
    chip_id = bus.read_byte_data(BMP280_ADDR, BMP280_REG_ID)
    print(f"Chip ID: 0x{chip_id:02X}")
    
    if chip_id != 0x58:
        print("❌ BMP280 not found!")
        return
    
    print("✅ BMP280 detected")
    print()
    
    # Configure sensor
    # Normal mode, temp oversampling x2, pressure oversampling x16
    bus.write_byte_data(BMP280_ADDR, BMP280_REG_CTRL_MEAS, 0xB7)
    # Standby 0.5ms, filter off
    bus.write_byte_data(BMP280_ADDR, BMP280_REG_CONFIG, 0x00)
    
    # Read calibration
    print("Reading calibration data...")
    cal = read_calibration(bus)
    print("✅ Calibration loaded")
    print()
    
    # Wait for first measurement
    time.sleep(0.1)
    
    print("Reading sensor (Ctrl+C to stop)...")
    print("-" * 60)
    
    try:
        while True:
            # Select channel (in case it was changed)
            select_mux_channel(bus, 1)
            
            # Read sensor
            adc_T, adc_P = read_bmp280(bus)
            
            # Compensate
            temperature, t_fine = compensate_temperature(adc_T, cal)
            pressure = compensate_pressure(adc_P, t_fine, cal)
            
            # Display
            print(f"Temperature: {temperature:6.2f} °C  |  Pressure: {pressure:7.2f} hPa", end='\r')
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n")
        print("Stopped.")
    
    # Disable all channels
    bus.write_byte(MUX_ADDR, 0x00)
    print()
    print("Multiplexer channels disabled.")

if __name__ == '__main__':
    main()
