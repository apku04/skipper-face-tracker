#!/usr/bin/env python3
"""
Test TCA9548A I2C Multiplexer with BME280 Sensor
================================================

Tests the TCA9548A/PCA9548A I2C multiplexer and scans for devices
on each channel. Specifically tests BME280 sensor on channel 0.

Hardware:
- TCA9548A at address 0x70 (default)
- BME280 sensor on channel 0 (should appear at 0x76 or 0x77)

Usage:
    python3 scripts/test_tca9548a_bme280.py
    python3 scripts/test_tca9548a_bme280.py --address 0x70 --bus 1
"""

import argparse
import time
import sys

try:
    import smbus2 as smbus
except ImportError:
    import smbus

# BME280 default I2C addresses
BME280_ADDR_PRIMARY = 0x76
BME280_ADDR_SECONDARY = 0x77

# BME280 chip ID register
BME280_REG_ID = 0xD0
BME280_CHIP_ID = 0x60

class TCA9548A:
    """TCA9548A I2C Multiplexer"""
    
    def __init__(self, bus_num=1, address=0x70):
        self.bus = smbus.SMBus(bus_num)
        self.address = address
        self.current_channel = None
    
    def select_channel(self, channel):
        """Select a channel (0-7)"""
        if channel < 0 or channel > 7:
            raise ValueError("Channel must be 0-7")
        
        # Write channel bitmask (1 << channel)
        mask = 1 << channel
        self.bus.write_byte(self.address, mask)
        self.current_channel = channel
    
    def disable_all_channels(self):
        """Disable all channels"""
        self.bus.write_byte(self.address, 0x00)
        self.current_channel = None
    
    def scan_channel(self, channel):
        """Scan for I2C devices on a specific channel"""
        self.select_channel(channel)
        devices = []
        
        for addr in range(0x08, 0x78):
            try:
                self.bus.read_byte(addr)
                devices.append(addr)
            except:
                pass
        
        return devices


def read_bme280_chip_id(bus, address):
    """Read BME280 chip ID to verify it's a BME280"""
    try:
        chip_id = bus.read_byte_data(address, BME280_REG_ID)
        return chip_id
    except:
        return None


def test_multiplexer(bus_num=1, mux_address=0x70):
    """Test TCA9548A multiplexer"""
    
    print("=" * 60)
    print("TCA9548A I2C Multiplexer Test")
    print("=" * 60)
    print()
    print(f"Configuration:")
    print(f"  I2C Bus: {bus_num}")
    print(f"  Multiplexer Address: 0x{mux_address:02X}")
    print()
    
    try:
        mux = TCA9548A(bus_num, mux_address)
        bus = smbus.SMBus(bus_num)
    except Exception as e:
        print(f"❌ Error opening I2C bus: {e}")
        return False
    
    # Test multiplexer presence
    print("Testing multiplexer...")
    try:
        mux.disable_all_channels()
        print("✅ TCA9548A multiplexer detected")
        print()
    except Exception as e:
        print(f"❌ Multiplexer not found at 0x{mux_address:02X}: {e}")
        return False
    
    # Scan all channels
    print("Scanning all 8 channels...")
    print("-" * 60)
    
    all_devices = {}
    
    for channel in range(8):
        try:
            devices = mux.scan_channel(channel)
            all_devices[channel] = devices
            
            if devices:
                print(f"Channel {channel}: ", end="")
                for addr in devices:
                    print(f"0x{addr:02X} ", end="")
                print()
            else:
                print(f"Channel {channel}: (no devices)")
        except Exception as e:
            print(f"Channel {channel}: Error - {e}")
    
    print()
    
    # Test BME280 on channel 0
    print("=" * 60)
    print("Testing BME280 on Channel 0")
    print("=" * 60)
    print()
    
    if 0 not in all_devices or not all_devices[0]:
        print("❌ No devices found on channel 0")
        print()
        print("Troubleshooting:")
        print("  1. Check BME280 is connected to channel 0 (SD0/SC0)")
        print("  2. Verify power (3.3V and GND)")
        print("  3. Check I2C pull-up resistors (usually on BME280 module)")
        print("  4. Try another channel if wired differently")
        mux.disable_all_channels()
        return False
    
    # Select channel 0
    mux.select_channel(0)
    
    # Check for BME280 at common addresses
    bme280_found = False
    bme280_address = None
    
    for addr in [BME280_ADDR_PRIMARY, BME280_ADDR_SECONDARY]:
        if addr in all_devices[0]:
            chip_id = read_bme280_chip_id(bus, addr)
            print(f"Device at 0x{addr:02X}:")
            
            if chip_id == BME280_CHIP_ID:
                print(f"  ✅ BME280 detected (Chip ID: 0x{chip_id:02X})")
                bme280_found = True
                bme280_address = addr
                break
            elif chip_id == 0x58:
                print(f"  ℹ️  BMP280 detected (Chip ID: 0x{chip_id:02X})")
                print(f"     Note: BMP280 has no humidity sensor")
                bme280_found = True
                bme280_address = addr
                break
            elif chip_id:
                print(f"  ⚠️  Unknown chip (Chip ID: 0x{chip_id:02X})")
            else:
                print(f"  ❌ Cannot read chip ID")
    
    if not bme280_found:
        print()
        print("❌ BME280/BMP280 not found on channel 0")
        print()
        print("Devices found:")
        for addr in all_devices[0]:
            print(f"  - 0x{addr:02X}")
        print()
        print("Expected addresses: 0x76 or 0x77")
        mux.disable_all_channels()
        return False
    
    print()
    print("=" * 60)
    print("Reading BME280 Sensor Data")
    print("=" * 60)
    print()
    
    # Try reading sensor with Adafruit library
    try:
        import board
        import adafruit_bme280.advanced as adafruit_bme280
        from adafruit_extended_bus import ExtendedI2C as I2C
        
        # Create I2C interface
        i2c = I2C(bus_num)
        
        # Create BME280 instance
        bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=bme280_address)
        
        # Read sensor
        print("Temperature: {:.2f} °C".format(bme280.temperature))
        print("Humidity:    {:.2f} %".format(bme280.humidity))
        print("Pressure:    {:.2f} hPa".format(bme280.pressure))
        print()
        print("✅ BME280 reading successful!")
        
    except ImportError as e:
        print("⚠️  Adafruit BME280 library not installed")
        print("   To install: pip3 install adafruit-circuitpython-bme280 adafruit-extended-bus")
        print()
        print("✅ BME280 detected successfully (library test skipped)")
    except Exception as e:
        print(f"❌ Error reading BME280: {e}")
        print()
        print("Troubleshooting:")
        print("  - BME280 detected but cannot read data")
        print("  - May need power cycle or sensor reset")
    
    # Cleanup
    mux.disable_all_channels()
    print()
    print("Test complete!")
    return bme280_found


def main():
    parser = argparse.ArgumentParser(description='Test TCA9548A multiplexer with BME280')
    parser.add_argument('--bus', type=int, default=1, help='I2C bus number (default: 1)')
    parser.add_argument('--address', type=lambda x: int(x, 0), default=0x70,
                        help='Multiplexer I2C address (default: 0x70)')
    
    args = parser.parse_args()
    
    success = test_multiplexer(args.bus, args.address)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
