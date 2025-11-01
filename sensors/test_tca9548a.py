#!/usr/bin/env python3
"""
Simple test script for the TCA9548A / PCA9548A 8-channel I2C multiplexer.

The script iterates through all channels, selects each one on the multiplexer,
and scans for downstream devices. It reports which I2C addresses respond on
each channel so you can quickly confirm wiring and device presence.

Usage:
    python3 scripts/test_tca9548a.py

Optional CLI arguments let you override the I2C bus number or the multiplexer
address if your hardware is configured differently.
"""

import argparse
import sys
import time

try:
    from smbus2 import SMBus
except ImportError as exc:
    sys.exit("smbus2 is required (pip install smbus2).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan devices behind a TCA9548A/PCA9548A I2C multiplexer."
    )
    parser.add_argument(
        "--bus",
        type=int,
        default=1,
        help="Linux I2C bus number (default: 1 for Raspberry Pi).",
    )
    parser.add_argument(
        "--address",
        type=lambda value: int(value, 0),
        default=0x70,
        help="I2C address of the multiplexer (default: 0x70).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.01,
        help="Delay in seconds after selecting a channel (default: 0.01).",
    )
    return parser.parse_args()


def select_channel(bus: SMBus, mux_address: int, channel: int, delay: float) -> None:
    if not 0 <= channel <= 7:
        raise ValueError("Channel must be between 0 and 7.")
    mask = 1 << channel
    bus.write_byte(mux_address, mask)
    time.sleep(delay)


def disable_all_channels(bus: SMBus, mux_address: int) -> None:
    bus.write_byte(mux_address, 0x00)


def scan_i2c_bus(bus: SMBus) -> list[int]:
    found = []
    for address in range(0x03, 0x78):
        try:
            bus.write_byte(address, 0)
            found.append(address)
        except OSError:
            continue
    return found


def main() -> int:
    args = parse_args()
    print(f"Opening I2C bus {args.bus} (multiplexer at 0x{args.address:02X})")

    try:
        with SMBus(args.bus) as bus:
            for channel in range(8):
                try:
                    select_channel(bus, args.address, channel, args.delay)
                except OSError as err:
                    print(
                        f"[CH{channel}] Could not select channel: {err}",
                        file=sys.stderr,
                    )
                    continue

                devices = scan_i2c_bus(bus)
                if devices:
                    addresses = ", ".join(f"0x{addr:02X}" for addr in devices)
                    print(f"[CH{channel}] Devices found at {addresses}")
                else:
                    print(f"[CH{channel}] No devices detected")

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

    print("Scan complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
