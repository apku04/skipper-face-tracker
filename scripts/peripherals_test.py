#!/usr/bin/env python3
"""
Peripherals Test Script

Controls:
- RGB status LED: R=GPIO23, G=GPIO22, B=GPIO27
- Fan control (via transistor): GATE=GPIO17

Features:
- Led test (cycle colors)
- Read SHT3x once or continuously
- Auto fan control based on temperature threshold

Usage:
    python3 scripts/peripherals_test.py --led-test
    python3 scripts/peripherals_test.py --read-sensor
    python3 scripts/peripherals_test.py --auto-fan --threshold 35

"""

import time
import argparse
import sys

# Try to import RPi.GPIO, fallback to dummy if not available
try:
    import RPi.GPIO as GPIO
    HW_GPIO = True
except Exception:
    HW_GPIO = False

# Import smbus for direct I2C access
try:
    import smbus2 as smbus
except ImportError:
    import smbus


# GPIO pin mapping
PIN_R = 23
PIN_G = 22
PIN_B = 27
PIN_FAN = 17


def setup_gpio():
    if not HW_GPIO:
        print("RPi.GPIO not available. GPIO functions will be simulated.")
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_R, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_G, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_B, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_FAN, GPIO.OUT, initial=GPIO.LOW)


def cleanup_gpio():
    if not HW_GPIO:
        return
    GPIO.output(PIN_R, GPIO.LOW)
    GPIO.output(PIN_G, GPIO.LOW)
    GPIO.output(PIN_B, GPIO.LOW)
    GPIO.output(PIN_FAN, GPIO.LOW)
    GPIO.cleanup()


def set_led(r=False, g=False, b=False):
    if not HW_GPIO:
        print(f"[SIM] LED -> R={r} G={g} B={b}")
        return
    GPIO.output(PIN_R, GPIO.HIGH if r else GPIO.LOW)
    GPIO.output(PIN_G, GPIO.HIGH if g else GPIO.LOW)
    GPIO.output(PIN_B, GPIO.HIGH if b else GPIO.LOW)


def fan_on():
    if not HW_GPIO:
        print("[SIM] Fan ON")
        return
    print("🌀 Fan ON (GPIO17 HIGH)")
    GPIO.output(PIN_FAN, GPIO.HIGH)


def fan_off():
    if not HW_GPIO:
        print("[SIM] Fan OFF")
        return
    print("🛑 Fan OFF (GPIO17 LOW)")
    GPIO.output(PIN_FAN, GPIO.LOW)


def led_test(cycle_delay=0.8, cycles=3):
    print("Starting LED test...")
    setup_gpio()
    try:
        for _ in range(cycles):
            set_led(True, False, False)  # Red
            time.sleep(cycle_delay)
            set_led(False, True, False)  # Green
            time.sleep(cycle_delay)
            set_led(False, False, True)  # Blue
            time.sleep(cycle_delay)
            set_led(True, True, False)   # Yellow
            time.sleep(cycle_delay)
            set_led(True, False, True)   # Magenta
            time.sleep(cycle_delay)
            set_led(False, True, True)   # Cyan
            time.sleep(cycle_delay)
            set_led(True, True, True)    # White
            time.sleep(cycle_delay)
            set_led(False, False, False) # Off
            time.sleep(cycle_delay)
    finally:
        cleanup_gpio()
        print("LED test complete")


def read_sht3x_once(bus_num=1, address=0x44):
    """Read SHT3x directly (not via multiplexer)"""
    try:
        bus = smbus.SMBus(bus_num)
        
        # Send measurement command (high repeatability)
        bus.write_i2c_block_data(address, 0x2C, [0x06])
        time.sleep(0.015)  # Wait for measurement
        
        # Read 6 bytes (temp + humidity with CRC)
        data = bus.read_i2c_block_data(address, 0x00, 6)
        
        # Convert temperature
        temp_raw = data[0] * 256 + data[1]
        temperature = -45 + (175 * temp_raw / 65535.0)
        
        # Convert humidity
        hum_raw = data[3] * 256 + data[4]
        humidity = 100 * hum_raw / 65535.0
        
        print(f"📊 SHT3x (direct at 0x{address:02x}) -> Temperature: {temperature:.2f} °C, Humidity: {humidity:.2f} %")
        return temperature, humidity
    except Exception as e:
        print(f"❌ Error reading SHT3x: {e}")
        return None


def auto_fan_monitor(threshold=30.0, poll_interval=5.0):
    print(f"Starting auto fan monitor (threshold={threshold}°C)...")
    print(f"Fan control pin: GPIO{PIN_FAN}")
    setup_gpio()
    try:
        while True:
            res = read_sht3x_once()
            if res is None:
                print("Sensor read failed; keeping fan off")
                fan_off()
            else:
                temp, hum = res
                if temp >= threshold:
                    print(f"🔥 Temp {temp:.2f}°C >= {threshold}°C -> Activating fan")
                    fan_on()
                    set_led(True, False, False)  # Red when hot
                else:
                    print(f"✅ Temp {temp:.2f}°C < {threshold}°C -> Fan stays off")
                    fan_off()
                    set_led(False, True, False)  # Green when ok
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\nStopping auto fan monitor")
    finally:
        cleanup_gpio()


def fan_manual_test():
    """Manual fan on/off test"""
    print("Manual fan test...")
    print(f"Fan control pin: GPIO{PIN_FAN}")
    setup_gpio()
    try:
        print("Turning fan ON for 3 seconds...")
        fan_on()
        time.sleep(3)
        print("Turning fan OFF for 2 seconds...")
        fan_off()
        time.sleep(2)
        print("Turning fan ON for 2 seconds...")
        fan_on()
        time.sleep(2)
        print("Turning fan OFF...")
        fan_off()
        print("✅ Fan test complete")
    finally:
        cleanup_gpio()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Peripherals test (RGB LED, Fan, SHT3x)')
    parser.add_argument('--led-test', action='store_true', help='Cycle LED colors')
    parser.add_argument('--fan-test', action='store_true', help='Manual fan on/off test')
    parser.add_argument('--read-sensor', action='store_true', help='Read SHT3x once')
    parser.add_argument('--auto-fan', action='store_true', help='Run auto fan monitor')
    parser.add_argument('--threshold', type=float, default=30.0, help='Temperature threshold for fan (°C)')
    parser.add_argument('--bus', type=int, default=1, help='I2C bus number')
    parser.add_argument('--address', type=lambda x: int(x, 0), default=0x44, help='SHT3x address')
    args = parser.parse_args()

    if args.led_test:
        led_test()
        sys.exit(0)

    if args.fan_test:
        fan_manual_test()
        sys.exit(0)

    if args.read_sensor:
        read_sht3x_once(bus_num=args.bus, address=args.address)
        sys.exit(0)

    if args.auto_fan:
        auto_fan_monitor(threshold=args.threshold)
        sys.exit(0)

    parser.print_help()
