# Printer.cfg Update for Smooth Motion

You need to reduce the acceleration values in your printer.cfg to make movements smooth.

## Current Problem:
```
accel: 1000  ← TOO HIGH! Causes jerky, aggressive movements
```

## Solution:
Edit `~/printer_data/config/printer.cfg` and change BOTH steppers:

```cfg
# ---- MOTOR0 (Azimuth/Pan) ----
[manual_stepper stepper_0]
step_pin: PF13
dir_pin: PF12
enable_pin: !PF14
microsteps: 16
rotation_distance: 8
velocity: 30          # Reduced from 50
accel: 100            # Reduced from 1000 - MUCH smoother!
endstop_pin: ^PG6

# ---- MOTOR1 (Altitude/Tilt) ----
[manual_stepper stepper_1]
step_pin: PG0
dir_pin: PG1
enable_pin: !PF15
microsteps: 16
rotation_distance: 8
velocity: 20          # Reduced from 50 - slower for altitude
accel: 50             # Reduced from 1000 - VERY smooth for tilt
endstop_pin: ^PG9
```

## After editing:
1. Save the file
2. Restart Klipper: `sudo systemctl restart klipper`
3. Or via API: `curl -X POST "http://localhost:7125/printer/gcode/script?script=FIRMWARE_RESTART"`

## Explanation:
- **accel: 100/50** instead of 1000 = 10-20x slower acceleration
- **velocity: 30/20** instead of 50 = max speed reduced
- Altitude gets even lower values (50) because it's more sensitive
- This eliminates the sudden starts/stops that cause shaking
