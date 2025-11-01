# Skipper v2.0 - Quick Reference

## 🚀 Running the System

### Face Tracking
```bash
# Dual camera tracking with face recognition
python3 main.py

# Single camera mode
python3 main.py --single-camera 0

# Without face recognition
python3 main.py --no-recognition

# Without motor following
python3 main.py --no-following
```

### Direct Module Access
```bash
# Face tracking (original script)
sudo python3 vision/virtual_tracking_dual.py
sudo python3 vision/virtual_tracking_dual.py --single-camera 0

# Sensor monitoring
python3 sensors/read_multiplexed_sensors.py
python3 sensors/read_multiplexed_sensors.py --continuous

# Motor calibration
python3 motors/calibrate_motors.py

# Motor testing
python3 motors/test_motors.py
python3 motors/test_motor_directions.py
```

## 🎯 Face Enrollment

### Capture Photos
```bash
# CSI camera enrollment
sudo python3 scripts/capture_enrollment_photos.py --name "Person" --camera 0

# USB webcam enrollment
sudo python3 scripts/capture_enrollment_photos_usb.py --name "Person"

# Open browser: http://localhost:5000
# Press ENTER to capture, 'done' when finished
```

### Enroll Faces
```bash
# Enroll captured photos
python3 scripts/enroll_hailo.py --name "Person" --images data/enrollment/Person_*.jpg

# Face database stored in: models/face_db/faces_db.pkl
```

## 🔧 Hardware Testing

### Camera Tests
```bash
# Test Hailo face detection
python3 vision/test_hailo_face.py

# Test dual camera
python3 vision/test_dual_camera_hailo.py

# Test Picamera2 + Hailo
python3 vision/test_picam2_hailo.py
```

### Motor Tests
```bash
# Test motor directions
python3 motors/test_motor_directions.py

# Test motor movements
python3 motors/test_motors.py

# Calibrate motor limits
python3 motors/calibrate_motors.py
```

### Sensor Tests
```bash
# Test I2C multiplexer
python3 sensors/test_tca9548a.py

# Read all sensors once
python3 sensors/read_multiplexed_sensors.py

# Continuous monitoring
python3 sensors/read_multiplexed_sensors.py --continuous
```

## ⚙️ Configuration

### Main Config: `config/default.yaml`
```yaml
app:
  name: "Skipper Face Tracker"
  log:
    level: "INFO"
  paths:
    face_db: "models/face_db/faces_db.pkl"

web:
  host: "0.0.0.0"
  port: 5000
```

### Camera: `config/camera.yaml`
```yaml
camera:
  resolution:
    width: 1640
    height: 1232
  framerate: 30
  dual_mode: true
  cameras: [0, 1]
```

### Motors: `config/motors.yaml`
```yaml
motors:
  klipper:
    host: "localhost"
    port: 7125
  pan:
    limits: [-180, 180]
    speed: 50
  tilt:
    limits: [-90, 90]
    speed: 40
```

### Sensors: `config/sensors.yaml`
```yaml
sensors:
  multiplexer:
    address: 0x70
  sht3x:
    channel: 0
    address: 0x44
  bmp280:
    channel: 1
    address: 0x76
```

## 📁 Key File Locations

### Python Modules
```
vision/virtual_tracking_dual.py    # Main tracking app
motors/klipper_motors.py            # Klipper client
motors/face_follow_manager.py       # Face following
sensors/read_multiplexed_sensors.py # Sensor reader
core/config.py                      # Config loader
```

### Configuration
```
config/default.yaml    # App settings
config/camera.yaml     # Camera config
config/motors.yaml     # Motor config
config/sensors.yaml    # Sensor config
config/printer.cfg     # Klipper config (example)
```

### Data & Models
```
models/face_db/faces_db.pkl       # Face recognition database
models/hailo/*.hef                # Hailo model files
data/enrollment/*.jpg             # Enrollment photos
data/logs/skipper.log             # Application logs
```

### Documentation
```
README.md                   # Project overview
docs/ARCHITECTURE.md        # Architecture guide
docs/MIGRATION_V2.md        # Migration summary
docs/KLIPPER_SETUP.md       # Klipper installation
docs/DEPENDENCIES.md        # Dependencies list
```

## 🔍 Troubleshooting

### Camera Issues
```bash
# Check camera
vcgencmd get_camera

# Check device tree
dmesg | grep imx708

# List cameras
libcamera-hello --list-cameras
```

### Klipper Issues
```bash
# Check Klipper status
sudo systemctl status klipper

# View logs
tail -f /tmp/klippy.log

# Restart Klipper
sudo systemctl restart klipper
```

### I2C Sensor Issues
```bash
# Scan I2C bus
i2cdetect -y 1

# Test multiplexer
python3 sensors/test_tca9548a.py

# Check sensor readings
python3 sensors/read_multiplexed_sensors.py
```

### Hailo HAT Issues
```bash
# Check Hailo device
hailortcli scan

# Monitor temperature
hailortcli monitor

# Check driver
lsmod | grep hailo
```

## 📦 Installation

### Development Mode
```bash
# Install in editable mode
pip3 install -e .

# Use CLI commands
skipper
skipper-enroll
skipper-calibrate
skipper-sensors
```

### Production Mode
```bash
# Install package
pip3 install .

# Or from requirements
pip3 install -r requirements.txt
```

## 🌐 Web Interface

```bash
# Start web interface
python3 main.py --mode web --port 5000

# Open browser
http://localhost:5000

# Or from external device
http://<raspberry-pi-ip>:5000
```

## 📊 Module Structure

```
skipper/
├── core/          # App orchestration
├── vision/        # Face tracking (ACTIVE)
├── motors/        # Klipper control (ACTIVE)
├── sensors/       # Environmental sensors (ACTIVE)
├── ai/            # LLM integration (FUTURE)
├── audio/         # Voice features (FUTURE)
├── utils/         # Utilities
├── config/        # YAML configs
├── models/        # ML models & DBs
├── data/          # Runtime data
├── tests/         # Unit tests
├── scripts/       # Utilities
├── docs/          # Documentation
└── web/           # Web interface
```

## 🎯 Common Tasks

### Add New Person
```bash
# 1. Capture photos
sudo python3 scripts/capture_enrollment_photos.py --name "NewPerson" --camera 0

# 2. Enroll photos
python3 scripts/enroll_hailo.py --name "NewPerson" --images data/enrollment/NewPerson_*.jpg

# 3. Test recognition
python3 main.py --single-camera 0
```

### Change Motor Limits
```bash
# Edit config/motors.yaml
nano config/motors.yaml

# Recalibrate
python3 motors/calibrate_motors.py
```

### Add New Sensor
```bash
# 1. Connect to TCA9548A channel
# 2. Update config/sensors.yaml
# 3. Add sensor class in sensors/
# 4. Update sensors/read_multiplexed_sensors.py
```

### View Logs
```bash
# Real-time logs
tail -f data/logs/skipper.log

# Filter by level
grep ERROR data/logs/skipper.log
grep WARNING data/logs/skipper.log
```

## 🔮 Future Features (Planned)

### LLM Integration (`ai/` module)
```bash
# Chat about what robot sees
skipper --mode chat

# Natural language queries
"Who is in front of me?"
"What's the temperature?"
"When did I last see John?"
```

### Voice Commands (`audio/` module)
```bash
# Enable voice control
skipper --mode voice

# Wake word + command
"Hey Skipper, who is that?"
"Hey Skipper, follow that face"
```

### Advanced Web UI (`web/` module)
- Live camera streams
- Face recognition dashboard
- Sensor graphs
- Motor control panel
- LLM chat interface

---

## 📚 Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Complete architecture guide
- **[MIGRATION_V2.md](docs/MIGRATION_V2.md)** - Migration summary
- **[KLIPPER_SETUP.md](docs/KLIPPER_SETUP.md)** - Klipper installation
- **[DEPENDENCIES.md](docs/DEPENDENCIES.md)** - Dependencies

## 🆘 Need Help?

1. Check documentation in `docs/`
2. View logs in `data/logs/`
3. Test hardware with `test_*.py` scripts
4. Check configuration in `config/`

---

**Version:** 2.0.0
**Last Updated:** November 2025
