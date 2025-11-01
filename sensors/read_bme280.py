#!/usr/bin/env python3
"""
Read temperature, pressure, and humidity from a BME280 (or BMP280) sensor that is
attached behind a TCA9548A / PCA9548A I2C multiplexer channel.

Example:
    python3 scripts/read_bme280.py --channel 2

If you omit --channel the script will probe every channel until it finds a
sensor at the requested I2C address.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass

try:
    from smbus2 import SMBus
except ImportError:
    sys.exit("smbus2 is required (pip install smbus2).")


@dataclass
class BME280Calibration:
    dig_T1: int
    dig_T2: int
    dig_T3: int
    dig_P1: int
    dig_P2: int
    dig_P3: int
    dig_P4: int
    dig_P5: int
    dig_P6: int
    dig_P7: int
    dig_P8: int
    dig_P9: int
    dig_H1: int
    dig_H2: int
    dig_H3: int
    dig_H4: int
    dig_H5: int
    dig_H6: int


class BME280:
    """Minimal BME280 reader that applies compensation using factory data."""

    REG_CTRL_HUM = 0xF2
    REG_STATUS = 0xF3
    REG_CTRL_MEAS = 0xF4
    REG_CONFIG = 0xF5
    REG_PRESS_MSB = 0xF7
    REG_CHIP_ID = 0xD0

    CHIP_IDS = {0x60: "BME280", 0x58: "BMP280"}

    def __init__(self, bus: SMBus, address: int) -> None:
        self.bus = bus
        self.address = address
        self.calibration = self._read_calibration()
        self.t_fine = 0

    @staticmethod
    def _u16(msb: int, lsb: int) -> int:
        return (msb << 8) | lsb

    @staticmethod
    def _s16(msb: int, lsb: int) -> int:
        value = BME280._u16(msb, lsb)
        if value & 0x8000:
            value -= 0x10000
        return value

    @staticmethod
    def _s8(value: int) -> int:
        return value - 0x100 if value & 0x80 else value

    def _read_calibration(self) -> BME280Calibration:
        data = self.bus.read_i2c_block_data(self.address, 0x88, 24)
        dig_T1 = self._u16(data[1], data[0])
        dig_T2 = self._s16(data[3], data[2])
        dig_T3 = self._s16(data[5], data[4])
        dig_P1 = self._u16(data[7], data[6])
        dig_P2 = self._s16(data[9], data[8])
        dig_P3 = self._s16(data[11], data[10])
        dig_P4 = self._s16(data[13], data[12])
        dig_P5 = self._s16(data[15], data[14])
        dig_P6 = self._s16(data[17], data[16])
        dig_P7 = self._s16(data[19], data[18])
        dig_P8 = self._s16(data[21], data[20])
        dig_P9 = self._s16(data[23], data[22])

        dig_H1 = self.bus.read_byte_data(self.address, 0xA1)

        data = self.bus.read_i2c_block_data(self.address, 0xE1, 7)
        dig_H2 = self._s16(data[1], data[0])
        dig_H3 = data[2]
        dig_H4 = (data[3] << 4) | (data[4] & 0x0F)
        dig_H5 = (data[4] >> 4) | (data[5] << 4)
        dig_H6 = self._s8(data[6])

        return BME280Calibration(
            dig_T1=dig_T1,
            dig_T2=dig_T2,
            dig_T3=dig_T3,
            dig_P1=dig_P1,
            dig_P2=dig_P2,
            dig_P3=dig_P3,
            dig_P4=dig_P4,
            dig_P5=dig_P5,
            dig_P6=dig_P6,
            dig_P7=dig_P7,
            dig_P8=dig_P8,
            dig_P9=dig_P9,
            dig_H1=dig_H1,
            dig_H2=dig_H2,
            dig_H3=dig_H3,
            dig_H4=dig_H4,
            dig_H5=dig_H5,
            dig_H6=dig_H6,
        )

    def read_chip_id(self) -> int:
        return self.bus.read_byte_data(self.address, self.REG_CHIP_ID)

    def configure(self) -> None:
        # Set humidity oversampling x1, pressure x1, temperature x1.
        self.bus.write_byte_data(self.address, self.REG_CTRL_HUM, 0x01)
        self.bus.write_byte_data(self.address, self.REG_CONFIG, 0x00)

    def _trigger_measurement(self) -> None:
        # osrs_t=1, osrs_p=1, forced mode
        self.bus.write_byte_data(self.address, self.REG_CTRL_MEAS, 0x25)

    def _wait_for_measurement(self, timeout: float = 0.2) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self.bus.read_byte_data(self.address, self.REG_STATUS)
            if status & 0x08 == 0:
                return
            time.sleep(0.005)
        raise TimeoutError("Timed out waiting for BME280 measurement to finish.")

    def _read_raw_data(self) -> tuple[int, int, int]:
        raw = self.bus.read_i2c_block_data(self.address, self.REG_PRESS_MSB, 8)
        adc_p = (raw[0] << 12) | (raw[1] << 4) | (raw[2] >> 4)
        adc_t = (raw[3] << 12) | (raw[4] << 4) | (raw[5] >> 4)
        adc_h = (raw[6] << 8) | raw[7]
        return adc_t, adc_p, adc_h

    def read_environmental_data(self) -> tuple[float, float, float]:
        self._trigger_measurement()
        self._wait_for_measurement()
        adc_t, adc_p, adc_h = self._read_raw_data()
        temperature_c = self._compensate_temperature(adc_t)
        pressure_pa = self._compensate_pressure(adc_p)
        humidity_rh = self._compensate_humidity(adc_h)
        return temperature_c, pressure_pa, humidity_rh

    def _compensate_temperature(self, adc_t: int) -> float:
        cal = self.calibration
        var1 = (adc_t / 16384.0 - cal.dig_T1 / 1024.0) * cal.dig_T2
        var2 = ((adc_t / 131072.0 - cal.dig_T1 / 8192.0) ** 2) * cal.dig_T3
        self.t_fine = var1 + var2
        temperature = (self.t_fine * 5 + 128) / 256
        return temperature / 100.0

    def _compensate_pressure(self, adc_p: int) -> float:
        cal = self.calibration
        var1 = self.t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * cal.dig_P6 / 32768.0
        var2 += var1 * cal.dig_P5 * 2.0
        var2 = var2 / 4.0 + cal.dig_P4 * 65536.0
        var1 = (
            cal.dig_P3 * var1 * var1 / 524288.0 + cal.dig_P2 * var1
        ) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * cal.dig_P1
        if var1 == 0:
            return 0.0
        pressure = 1048576.0 - adc_p
        pressure = (pressure - var2 / 4096.0) * 6250.0 / var1
        var1 = cal.dig_P9 * pressure * pressure / 2147483648.0
        var2 = pressure * cal.dig_P8 / 32768.0
        pressure += (var1 + var2 + cal.dig_P7) / 16.0
        return pressure

    def _compensate_humidity(self, adc_h: int) -> float:
        cal = self.calibration
        var_h = self.t_fine - 76800.0
        if var_h == 0:
            return 0.0
        var_h = (
            adc_h
            - (cal.dig_H4 * 64.0 + cal.dig_H5 / 16384.0 * var_h)
        ) * (
            cal.dig_H2
            / 65536.0
            * (
                1.0
                + cal.dig_H6 / 67108864.0 * var_h * (1.0 + cal.dig_H3 / 67108864.0 * var_h)
            )
        )
        var_h = var_h * (1.0 - cal.dig_H1 * var_h / 524288.0)
        var_h = max(0.0, min(var_h, 419430400.0))
        return var_h / 4096.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read data from a BME280/BMP280 behind a TCA9548A multiplexer."
    )
    parser.add_argument(
        "--bus",
        type=int,
        default=1,
        help="Linux I2C bus number (default: 1).",
    )
    parser.add_argument(
        "--address",
        type=lambda value: int(value, 0),
        default=0x70,
        help="I2C address of the multiplexer (default: 0x70).",
    )
    parser.add_argument(
        "--sensor-address",
        type=lambda value: int(value, 0),
        default=0x76,
        help="I2C address of the BME/BMP sensor (default: 0x76).",
    )
    parser.add_argument(
        "--channel",
        type=int,
        help="Multiplexer channel (0-7). If omitted, probe channels automatically.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of readings to capture (default: 1).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Delay between readings in seconds when --count > 1 (default: 2.0).",
    )
    return parser.parse_args()


def select_channel(bus: SMBus, mux_address: int, channel: int, delay: float = 0.01) -> None:
    if not 0 <= channel <= 7:
        raise ValueError("Channel must be between 0 and 7.")
    mask = 1 << channel
    bus.write_byte(mux_address, mask)
    time.sleep(delay)


def disable_all_channels(bus: SMBus, mux_address: int) -> None:
    bus.write_byte(mux_address, 0x00)


def find_sensor_channel(bus: SMBus, mux_address: int, channel_hint: int | None, sensor_address: int) -> int:
    candidates = [channel_hint] if channel_hint is not None else range(8)
    for channel in candidates:
        try:
            select_channel(bus, mux_address, channel)
            chip_id = bus.read_byte_data(sensor_address, BME280.REG_CHIP_ID)
        except OSError:
            continue
        if chip_id in BME280.CHIP_IDS:
            print(
                f"Selected channel {channel} with detected sensor {BME280.CHIP_IDS[chip_id]} "
                f"(chip ID 0x{chip_id:02X})"
            )
            return channel
    raise RuntimeError("Unable to locate a BME280/BMP280 on the multiplexer.")


def main() -> int:
    args = parse_args()

    try:
        with SMBus(args.bus) as bus:
            channel = find_sensor_channel(bus, args.address, args.channel, args.sensor_address)
            sensor = BME280(bus, args.sensor_address)
            sensor.configure()

            try:
                for reading in range(args.count):
                    temperature_c, pressure_pa, humidity_rh = sensor.read_environmental_data()
                    pressure_hpa = pressure_pa / 100.0
                    print(
                        f"Reading {reading + 1}: "
                        f"{temperature_c:.2f} °C, {pressure_hpa:.2f} hPa, {humidity_rh:.2f} %RH"
                    )
                    if reading + 1 < args.count:
                        time.sleep(args.interval)
            finally:
                disable_all_channels(bus, args.address)
    except FileNotFoundError:
        print(
            f"I2C bus {args.bus} not found. Ensure i2c-dev is enabled.",
            file=sys.stderr,
        )
        return 1
    except PermissionError:
        print(
            "Permission denied when accessing the I2C bus. "
            "Try running with sudo or adjust permissions.",
            file=sys.stderr,
        )
        return 1
    except RuntimeError as err:
        print(err, file=sys.stderr)
        return 1
    except TimeoutError as err:
        print(err, file=sys.stderr)
        return 1
    except OSError as err:
        print(f"I2C communication error: {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
