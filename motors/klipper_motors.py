#!/usr/bin/env python3
"""
Klipper-based motor control for face tracking robot.
Replacement for gpiozero StepperWorker classes.

This module provides the same interface as the old stepper control
but uses Klipper + Octopus board instead of direct GPIO.
"""

import time
import threading
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Optional


class KlipperMotorController:
    """
    Drop-in replacement for gpiozero stepper control.
    Uses Klipper's stepper_x and stepper_y for smooth face tracking.
    """
    
    def __init__(self, base_url: str = "http://localhost:7125",
                 azimuth_min: float = -45, azimuth_max: float = 45,
                 altitude_min: float = -30, altitude_max: float = 30):
        self.base_url = base_url
        self.azimuth_pos = 0.0
        self.altitude_pos = 0.0
        self.lock = threading.Lock()
        
        # Motion limits (can be calibrated)
        self.azimuth_min = azimuth_min
        self.azimuth_max = azimuth_max
        self.altitude_min = altitude_min
        self.altitude_max = altitude_max
        
    def _send_gcode(self, command: str, timeout: int = 5) -> dict:
        """Send G-code command to Klipper."""
        url = f"{self.base_url}/printer/gcode/script"
        data = urllib.parse.urlencode({"script": command}).encode()
        
        try:
            with urllib.request.urlopen(url, data=data, timeout=timeout) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            # Silently fail for non-critical commands
            return {"error": str(e)}
    
    def initialize(self) -> bool:
        """Initialize Klipper connection and set home position."""
        try:
            url = f"{self.base_url}/printer/info"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                state = data.get("result", {}).get("state", "")
                
                if state == "ready":
                    # For manual steppers, enable them and set starting position
                    self._send_gcode("MANUAL_STEPPER STEPPER=stepper_0 ENABLE=1 SET_POSITION=0")
                    self._send_gcode("MANUAL_STEPPER STEPPER=stepper_1 ENABLE=1 SET_POSITION=0")
                    print("✓ Klipper motors initialized (manual steppers)")
                    return True
                else:
                    print(f"⚠ Klipper state: {state}")
                    return False
        except Exception as e:
            print(f"✗ Cannot connect to Klipper: {e}")
            return False
    
    def set_azimuth(self, degrees: float, speed: float = 30):
        """
        Move azimuth (pan) to position.
        
        Args:
            degrees: Target position in degrees
            speed: Speed in degrees/second (converted to mm/s for manual stepper)
        """
        with self.lock:
            # Clamp to limits
            degrees = max(self.azimuth_min, min(self.azimuth_max, degrees))
            
            # Manual stepper command: MANUAL_STEPPER STEPPER=stepper_0 MOVE=degrees SPEED=speed
            self._send_gcode(f"MANUAL_STEPPER STEPPER=stepper_0 MOVE={degrees} SPEED={speed}")
            self.azimuth_pos = degrees
    
    def set_altitude(self, degrees: float, speed: float = 3):
        """
        Move altitude (tilt) to position.
        
        Args:
            degrees: Target position in degrees
            speed: Speed in degrees/second (default 3 for extremely gentle movement)
        """
        with self.lock:
            # Clamp to limits (handle inverted range where min > max)
            if self.altitude_min > self.altitude_max:
                # Inverted: down is positive, up is negative
                degrees = min(self.altitude_min, max(self.altitude_max, degrees))
            else:
                # Normal: min < max
                degrees = max(self.altitude_min, min(self.altitude_max, degrees))
            
            # Manual stepper command: MANUAL_STEPPER STEPPER=stepper_1 MOVE=degrees SPEED=speed
            self._send_gcode(f"MANUAL_STEPPER STEPPER=stepper_1 MOVE={degrees} SPEED={speed}")
            self.altitude_pos = degrees
    
    def move_both(self, azimuth: float, altitude: float, speed: float = 30):
        """
        Move both axes simultaneously (coordinated motion).
        Note: Manual steppers move sequentially, not truly coordinated.
        
        Args:
            azimuth: Target azimuth in degrees
            altitude: Target altitude in degrees
            speed: Speed in degrees/second
        """
        with self.lock:
            # Clamp to limits
            azimuth = max(self.azimuth_min, min(self.azimuth_max, azimuth))
            
            # Handle inverted altitude range
            if self.altitude_min > self.altitude_max:
                altitude = min(self.altitude_min, max(self.altitude_max, altitude))
            else:
                altitude = max(self.altitude_min, min(self.altitude_max, altitude))
            
            # Move both manual steppers (they'll move one after the other)
            self._send_gcode(f"MANUAL_STEPPER STEPPER=stepper_0 MOVE={azimuth} SPEED={speed}")
            self._send_gcode(f"MANUAL_STEPPER STEPPER=stepper_1 MOVE={altitude} SPEED={speed}")
            self.azimuth_pos = azimuth
            self.altitude_pos = altitude
    
    def get_position(self):
        """Get current position (azimuth, altitude)."""
        with self.lock:
            return (self.azimuth_pos, self.altitude_pos)
    
    def stop(self):
        """Stop all motion."""
        self._send_gcode("M112")  # Emergency stop
    
    def disable_motors(self):
        """Disable motors (free movement)."""
        self._send_gcode("MANUAL_STEPPER STEPPER=stepper_0 ENABLE=0")
        self._send_gcode("MANUAL_STEPPER STEPPER=stepper_1 ENABLE=0")


class StepperController:
    """
    Compatibility class that mimics the old gpiozero stepper interface.
    Provides get_rate() and get_dir() methods for backward compatibility.
    """
    
    def __init__(self, name: str, motor_controller: KlipperMotorController, 
                 axis: str = "azimuth"):
        self.name = name
        self.motor = motor_controller
        self.axis = axis  # "azimuth" or "altitude"
        self.target = 0.0
        self.current = 0.0
        self.rate = 0
        self.direction = 0
        
    def set_target(self, position: float):
        """Set target position."""
        self.target = position
        
        # Calculate rate and direction (for compatibility)
        diff = position - self.current
        self.rate = abs(diff)
        self.direction = 1 if diff > 0 else -1
        
        # Move motor
        if self.axis == "azimuth":
            self.motor.set_azimuth(position)
        else:
            self.motor.set_altitude(position)
        
        self.current = position
    
    def get_rate(self):
        """Get current movement rate (for compatibility)."""
        return self.rate
    
    def get_dir(self):
        """Get current direction (for compatibility)."""
        return self.direction


# Global motor controller instance
_motor_controller = None


def get_motor_controller() -> KlipperMotorController:
    """Get or create the global motor controller."""
    global _motor_controller
    if _motor_controller is None:
        _motor_controller = KlipperMotorController()
        _motor_controller.initialize()
    return _motor_controller


def create_stepper_controllers():
    """
    Create azimuth and altitude stepper controllers.
    Returns tuple of (az_controller, alt_controller).
    """
    motor = get_motor_controller()
    az_ctrl = StepperController("Azimuth", motor, axis="azimuth")
    alt_ctrl = StepperController("Altitude", motor, axis="altitude")
    return az_ctrl, alt_ctrl
