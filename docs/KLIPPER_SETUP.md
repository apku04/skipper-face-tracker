# Klipper Motor Control Setup Guide

This guide explains how to set up Klipper-based motor control for the **Skipper AI Voice Assistant Robot's face tracking system**.

## Overview

Skipper is a complete AI-powered voice assistant robot featuring:
- 🤖 **Voice interaction** - LLM (Ollama), STT (Vosk/Whisper), TTS (Piper)
- 👁️ **Face tracking** - Real-time face following with camera
- 😊 **Mood detection** - MediaPipe behavioral analysis
- 🎯 **Motor control** - Klipper-based smooth motion (this guide)

This document focuses on the **Klipper motor control** component, which has been converted from direct GPIO control to Klipper for:

- **Smoother motion** - Klipper handles acceleration and velocity profiles
- **Better precision** - Klipper's advanced motion planning
- **Easier configuration** - Change motor settings without code changes
- **Remote control** - Can control motors over network
- **More flexibility** - Support for complex motion systems

## Prerequisites

1. **Klipper installed** on your system (e.g., on an Octopus board or similar)
2. **Moonraker API** running (default: `http://localhost:7125`)
3. **Python dependencies**:
   - OpenCV (`cv2`)
   - Flask
   - NumPy
   - MediaPipe (optional, for behavior analysis)

## Klipper Configuration

You need to configure Klipper with two stepper axes for azimuth (pan) and altitude (tilt). Add this to your `printer.cfg`:

```ini
# Face tracking steppers
[stepper_x]
step_pin: PF13          # Adjust to your board pins
dir_pin: PF12           # Adjust to your board pins
enable_pin: !PF14       # Adjust to your board pins
microsteps: 16
rotation_distance: 1.8  # 1.8 degrees per step (200 steps/rev stepper)
endstop_pin: ^PG6       # Optional: endstop for homing
position_endstop: 0
position_min: -180      # Allow ±180 degrees rotation
position_max: 180
homing_speed: 50

[stepper_y]
step_pin: PG0           # Adjust to your board pins
dir_pin: PG1            # Adjust to your board pins
enable_pin: !PF15       # Adjust to your board pins
microsteps: 16
rotation_distance: 1.8  # 1.8 degrees per step (200 steps/rev stepper)
endstop_pin: ^PG9       # Optional: endstop for homing
position_endstop: 0
position_min: -90       # Tilt range (adjust as needed)
position_max: 90
homing_speed: 50

# Disable kinematics check (we're not using standard 3D printer kinematics)
[force_move]
enable_force_move: True
```

### Pin Configuration

Update the pin numbers in the configuration above to match your specific board:

- **BTT Octopus**: Use pin names like `PF13`, `PG0`, etc.
- **SKR boards**: Use pin names like `P2.0`, `P0.5`, etc.
- **Other boards**: Consult your board's pinout diagram

Refer to the Klipper documentation for your specific board's pin mapping.

## Environment Variables

Configure the system using environment variables:

```bash
# Klipper/Moonraker connection
export KLIPPER_URL="http://localhost:7125"  # Change if Moonraker is on different host/port

# Enable/disable Klipper control
export KLIPPER_ENABLED="true"

# Face detector models (optional)
export YUNET_ONNX="/usr/share/opencv4/face_detection_yunet_2023mar.onnx"
export DNN_PROTO="/usr/share/opencv4/deploy.prototxt"
export DNN_MODEL="/usr/share/opencv4/res10_300x300_ssd_iter_140000.caffemodel"
export HAAR_XML="/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"

# Behavior analysis (optional)
export FF_BEHAVIOR="true"
export FF_BEHAVIOR_INTERVAL="0.6"
```

## How It Works

### Architecture

```
follow_face.py
    ↓
AxisControl (azimuth/altitude)
    ↓
KlipperMotorController
    ↓
Moonraker API (HTTP)
    ↓
Klipper Firmware
    ↓
Stepper Motors (stepper_x, stepper_y)
```

### Motion Control

1. **Face Detection**: OpenCV detects faces and calculates pixel error from center
2. **Rate Calculation**: Error is converted to movement rate (Hz) and direction
3. **Position Update**: `AxisControl` converts rate to small incremental position changes
4. **G-code Commands**: Sent to Klipper via Moonraker API:
   - `G0 X<degrees> F<feedrate>` for azimuth
   - `G0 Y<degrees> F<feedrate>` for altitude
5. **Smooth Movement**: Klipper handles acceleration/deceleration

### Key Changes from GPIO Control

| Aspect | GPIO Control | Klipper Control |
|--------|--------------|-----------------|
| **Interface** | Direct pin toggling | HTTP API calls |
| **Threading** | StepperWorker threads | Klipper firmware handles timing |
| **Speed Control** | Step frequency (Hz) | Feedrate (deg/min) |
| **Position** | Relative steps | Absolute degrees |
| **Smoothing** | Software PWM | Hardware motion planning |

## Running the System

### 1. Start Klipper and Moonraker

```bash
# Make sure Klipper is running
sudo systemctl status klipper

# Make sure Moonraker is running
sudo systemctl status moonraker
```

### 2. Run the Full Voice Assistant (Recommended)

```bash
cd /home/pi/work/skipper
python3 main.py

# The voice assistant will automatically:
# - Initialize face tracking with Klipper motors
# - Start listening for voice commands
# - Follow your face while conversing
# - Display status on OLED and LED
```

### 3. Run Face Tracking Only (Testing/Standalone)

```bash
cd /home/pi/work/skipper
python3 follow_face.py

# Or use the startup script:
./start_face_tracking.sh
```

Expected output:
```
Initializing Klipper motor controller...
✓ Klipper motors initialized
[detector] Using: yunet
Face-follow running. Ctrl+C to stop.
Stream at http://0.0.0.0:5000 (use the Pi's IP if 0.0.0.0)
Face dx=+12 dy=-8 AZ:+150.0 Hz ALT:-120.0 Hz
```

### 4. Access the Video Stream

Open a browser and navigate to:
```
http://<raspberry-pi-ip>:5000/
```

You'll see the live camera feed with face detection overlay.

## Troubleshooting

### Cannot Connect to Klipper

**Error**: `ERROR: Could not connect to Klipper. Make sure Moonraker is running.`

**Solutions**:
1. Check Moonraker is running: `sudo systemctl status moonraker`
2. Check the URL: `curl http://localhost:7125/printer/info`
3. Update `KLIPPER_URL` environment variable if different
4. Check firewall settings

### Motors Not Moving

**Possible causes**:
1. **Klipper not ready**: Check `printer/info` endpoint shows `state: "ready"`
2. **Motors disabled**: Check Klipper logs for motor disable messages
3. **Position limits**: Face may be centered (no error = no movement)
4. **Configuration**: Verify `rotation_distance` in printer.cfg

### Jerky Motion

**Solutions**:
1. Increase `SMOOTHING` value in `follow_face.py` (default: 0.35)
2. Adjust Klipper's `max_accel` and `max_velocity` settings
3. Tune PID constants: `K_P`, `MIN_RATE_HZ`, `MAX_RATE_HZ`

### Face Not Detected

**Solutions**:
1. Check lighting conditions (face detectors need good lighting)
2. Verify camera is working: `ls /dev/video*`
3. Try different detector: Set model paths via environment variables
4. Check MJPEG stream at http://localhost:5000 to see what camera sees

## Integration with Main Voice Assistant

The face tracking is automatically integrated into the main voice assistant system:

```python
# In main.py - face tracking runs automatically
from face_follow_manager import FaceFollowManager

# The voice assistant starts face tracking on boot
face_follow = FaceFollowManager()
face_follow.start()  # Automatically uses Klipper motors

# Face tracking runs in background while robot talks to you
# Robot follows your face during conversation
# Behavioral data (mood, gestures) feeds into LLM context

# Example: Robot detects you're smiling while it's speaking
# LLM can incorporate this into its responses
```

### Behavior Integration

The face tracking system can detect:
- **Facial mood** - Happy, sad, neutral, surprised, etc.
- **Hand gestures** - Open palm, closed fist, pointing, thumbs up, etc.
- **Presence** - Whether face is detected or not

This data is fed to the LLM via the `BehaviorMonitor` for context-aware responses:

```python
# Example LLM prompt with behavior context:
# "The user is smiling and waving their right hand. 
#  They seem happy. Respond appropriately."
```

## Performance Tuning

### Control Parameters

Edit these in `follow_face.py`:

```python
# Deadband - no movement if error is small
DEADBAND_PX = 16

# Proportional gain - higher = more aggressive tracking
K_P = 3.0

# Speed limits
MIN_RATE_HZ = 40
MAX_RATE_HZ = 1200

# Smoothing - higher = smoother but slower response
SMOOTHING = 0.35
```

### Klipper Settings

In `printer.cfg`:

```ini
[stepper_x]
# Increase for faster motion (but may be jerky)
max_velocity: 100

# Increase for more aggressive acceleration
max_accel: 1000

# Increase for smoother motion (but slower response)
square_corner_velocity: 5.0
```

## Safety

- **Power off motors** when not in use (system auto-disables after timeout)
- **Set position limits** in Klipper config to prevent mechanical damage
- **Emergency stop**: Press Ctrl+C or use Klipper's `M112` command
- **Test carefully** before leaving unattended

## Files Modified

- `follow_face.py` - Updated to use Klipper motor control
- `config.py` - Added Klipper URL settings
- `klipper_motors.py` - Motor control interface (already existed)

## Advanced: Custom Motor Speeds

To customize speed mapping, edit the `AxisControl.set()` method in `follow_face.py`:

```python
# Map rate_hz (0-1200) to speed (10-100 deg/s)
self._speed_dps = 10 + (self._rate_hz / MAX_RATE_HZ) * 90
```

Adjust the formula to suit your needs.

## Support

For issues:
1. Check Klipper logs: `tail -f /tmp/klippy.log`
2. Check Moonraker logs: `journalctl -u moonraker -f`
3. Check application output for errors
4. Verify Klipper configuration with `SAVE_CONFIG`
