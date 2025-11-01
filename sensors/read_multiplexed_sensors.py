#!/usr/bin/env python3
"""
Read Multiple Sensors via TCA9548A Multiplexer
==============================================

Reads sensors connected through TCA9548A I2C multiplexer:
- Channel 0: SHT3x (temperature & humidity) at 0x44
- Channel 1: BMP280 (temperature & pressure) at 0x76

Usage:
    python3 scripts/read_multiplexed_sensors.py
    python3 scripts/read_multiplexed_sensors.py --continuous
"""

import argparse
import time
import sys

try:
    import smbus2 as smbus
except ImportError:
    import smbus

class TCA9548A:
    """TCA9548A I2C Multiplexer"""
    
    def __init__(self, bus_num=1, address=0x70):
        self.bus = smbus.SMBus(bus_num)
        self.address = address
    
    def select_channel(self, channel):
        """Select a channel (0-7)"""
        if channel < 0 or channel > 7:
            raise ValueError("Channel must be 0-7")
        mask = 1 << channel
        self.bus.write_byte(self.address, mask)
    
    def disable_all_channels(self):
        """Disable all channels"""
        self.bus.write_byte(self.address, 0x00)


class SHT3x:
    """SHT3x Temperature & Humidity Sensor"""
    
    def __init__(self, bus, address=0x44):
        self.bus = bus
        self.address = address
    
    def read_data(self):
        """Read temperature and humidity"""
        try:
            # Send measurement command (high repeatability)
            self.bus.write_i2c_block_data(self.address, 0x2C, [0x06])
            time.sleep(0.015)  # Wait for measurement
            
            # Read 6 bytes (temp + humidity with CRC)
            data = self.bus.read_i2c_block_data(self.address, 0x00, 6)
            
            # Convert temperature
            temp_raw = data[0] * 256 + data[1]
            temperature = -45 + (175 * temp_raw / 65535.0)
            
            # Convert humidity
            hum_raw = data[3] * 256 + data[4]
            humidity = 100 * hum_raw / 65535.0
            
            return temperature, humidity
        except Exception as e:
            return None, None


class BMP280:
    """BMP280 Temperature & Pressure Sensor (simplified)"""
    
    def __init__(self, bus, address=0x76):
        self.bus = bus
        self.address = address
        self._calibration_loaded = False
    
    def _load_calibration(self):
        """Load calibration data"""
        try:
            # Read calibration data
            cal = self.bus.read_i2c_block_data(self.address, 0x88, 24)
            
            # Temperature calibration
            self.dig_T1 = cal[1] * 256 + cal[0]
            self.dig_T2 = cal[3] * 256 + cal[2]
            if self.dig_T2 > 32767:
                self.dig_T2 -= 65536
            self.dig_T3 = cal[5] * 256 + cal[4]
            if self.dig_T3 > 32767:
                self.dig_T3 -= 65536
            
            # Pressure calibration
            self.dig_P1 = cal[7] * 256 + cal[6]
            self.dig_P2 = cal[9] * 256 + cal[8]
            if self.dig_P2 > 32767:
                self.dig_P2 -= 65536
            self.dig_P3 = cal[11] * 256 + cal[10]
            if self.dig_P3 > 32767:
                self.dig_P3 -= 65536
            self.dig_P4 = cal[13] * 256 + cal[12]
            if self.dig_P4 > 32767:
                self.dig_P4 -= 65536
            self.dig_P5 = cal[15] * 256 + cal[14]
            if self.dig_P5 > 32767:
                self.dig_P5 -= 65536
            self.dig_P6 = cal[17] * 256 + cal[16]
            if self.dig_P6 > 32767:
                self.dig_P6 -= 65536
            self.dig_P7 = cal[19] * 256 + cal[18]
            if self.dig_P7 > 32767:
                self.dig_P7 -= 65536
            self.dig_P8 = cal[21] * 256 + cal[20]
            if self.dig_P8 > 32767:
                self.dig_P8 -= 65536
            self.dig_P9 = cal[23] * 256 + cal[22]
            if self.dig_P9 > 32767:
                self.dig_P9 -= 65536
            
            self._calibration_loaded = True
        except Exception as e:
            print(f"Error loading BMP280 calibration: {e}")
    
    def read_data(self):
        """Read temperature and pressure"""
        try:
            if not self._calibration_loaded:
                self._load_calibration()
            
            # Set control register (temp/pressure oversampling x1, normal mode)
            self.bus.write_byte_data(self.address, 0xF4, 0x27)
            time.sleep(0.01)
            
            # Read raw data
            data = self.bus.read_i2c_block_data(self.address, 0xF7, 6)
            
            # Pressure
            adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
            # Temperature
            adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
            
            # Compensate temperature
            var1 = ((adc_t / 16384.0) - (self.dig_T1 / 1024.0)) * self.dig_T2
            var2 = (((adc_t / 131072.0) - (self.dig_T1 / 8192.0)) ** 2) * self.dig_T3
            t_fine = int(var1 + var2)
            temperature = (var1 + var2) / 5120.0
            
            # Compensate pressure
            var1 = (t_fine / 2.0) - 64000.0
            var2 = var1 * var1 * self.dig_P6 / 32768.0
            var2 = var2 + var1 * self.dig_P5 * 2.0
            var2 = (var2 / 4.0) + (self.dig_P4 * 65536.0)
            var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
            var1 = (1.0 + var1 / 32768.0) * self.dig_P1
            
            if var1 == 0:
                pressure = 0
            else:
                pressure = 1048576.0 - adc_p
                pressure = (pressure - (var2 / 4096.0)) * 6250.0 / var1
                var1 = self.dig_P9 * pressure * pressure / 2147483648.0
                var2 = pressure * self.dig_P8 / 32768.0
                pressure = pressure + (var1 + var2 + self.dig_P7) / 16.0
                pressure = pressure / 100.0  # Convert to hPa
            
            return temperature, pressure
        except Exception as e:
            return None, None


def read_all_sensors(mux_address=0x70, bus_num=1, continuous=False):
    """Read all sensors through multiplexer"""
    
    print("=" * 70)
    print("Multi-Sensor Reader via TCA9548A Multiplexer")
    print("=" * 70)
    print()
    
    try:
        mux = TCA9548A(bus_num, mux_address)
        bus = smbus.SMBus(bus_num)
    except Exception as e:
        print(f"❌ Error opening I2C bus: {e}")
        return
    
    # Initialize sensors
    sht3x = SHT3x(bus, 0x44)
    bmp280 = BMP280(bus, 0x76)
    
    print("Sensors:")
    print("  - Channel 0: SHT3x (Temperature & Humidity) at 0x44")
    print("  - Channel 1: BMP280 (Temperature & Pressure) at 0x76")
    print()
    
    if continuous:
        print("Reading continuously (Ctrl+C to stop)...")
        print()
    
    try:
        while True:
            # Read SHT3x on channel 0
            mux.select_channel(0)
            time.sleep(0.01)
            sht_temp, sht_hum = sht3x.read_data()
            
            # Read BMP280 on channel 1
            mux.select_channel(1)
            time.sleep(0.01)
            bmp_temp, bmp_pressure = bmp280.read_data()
            
            # Display results
            print("-" * 70)
            print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            if sht_temp is not None and sht_hum is not None:
                print(f"📊 SHT3x (Channel 0):")
                print(f"   Temperature:  {sht_temp:6.2f} °C")
                print(f"   Humidity:     {sht_hum:6.2f} %")
            else:
                print(f"❌ SHT3x: Error reading sensor")
            
            print()
            
            if bmp_temp is not None and bmp_pressure is not None:
                print(f"📊 BMP280 (Channel 1):")
                print(f"   Temperature:  {bmp_temp:6.2f} °C")
                print(f"   Pressure:     {bmp_pressure:7.2f} hPa")
                
                # Calculate altitude (approximate)
                altitude = 44330.0 * (1.0 - (bmp_pressure / 1013.25) ** (1.0 / 5.255))
                print(f"   Altitude:     {altitude:7.1f} m (approx)")
            else:
                print(f"❌ BMP280: Error reading sensor")
            
            print()
            
            # Average temperature if both sensors working
            if sht_temp is not None and bmp_temp is not None:
                avg_temp = (sht_temp + bmp_temp) / 2.0
                temp_diff = abs(sht_temp - bmp_temp)
                print(f"🌡️  Average Temperature: {avg_temp:.2f} °C")
                print(f"   (Difference: {temp_diff:.2f} °C)")
                print()
            
            if not continuous:
                break
            
            time.sleep(2)  # Wait 2 seconds between readings
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    finally:
        mux.disable_all_channels()


def main():
    parser = argparse.ArgumentParser(description='Read sensors via TCA9548A multiplexer')
    parser.add_argument('--bus', type=int, default=1, help='I2C bus number (default: 1)')
    parser.add_argument('--address', type=lambda x: int(x, 0), default=0x70,
                        help='Multiplexer address (default: 0x70)')
    parser.add_argument('--continuous', action='store_true',
                        help='Read continuously (Ctrl+C to stop)')
    
    args = parser.parse_args()
    
    read_all_sensors(args.address, args.bus, args.continuous)


if __name__ == '__main__':
    main()
