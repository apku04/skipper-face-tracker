# Skipper Face Tracker - Hailo + Klipper Integration# Skipper - AI Voice Assistant Robot with Face Tracking



**AI-powered face tracking system** with Raspberry Pi 5 + Hailo-8L HAT for real-time face detection, recognition, and motor control via Klipper.**Complete AI-powered robot assistant** featuring:

- 🤖 **LLM Integration** - Ollama-powered conversational AI (Llama 3.2)

## 🎯 Core Features- 🎤 **Speech-to-Text** - Vosk/Whisper for voice recognition

- 🔊 **Text-to-Speech** - Piper TTS with voice effects

- **🤖 Hailo-8L Acceleration** - Hardware-accelerated face detection (SCRFD model)- 👁️ **Face Tracking** - Real-time face following with Klipper motor control

- **👁️ Face Recognition** - Template matching with face embeddings- 🧠 **Face Recognition** - Hailo-accelerated person identification

- **📸 Face Enrollment** - Capture and enroll faces for recognition- 😊 **Behavior Analysis** - MediaPipe mood & gesture detection

- **🔄 Face Following** - Real-time motor tracking via Klipper- 💾 **Conversation Memory** - Context-aware responses

- **🎚️ Motor Calibration** - Configure stepper motor limits and speeds- 📊 **System Diagnostics** - Self-monitoring and reporting

- **🌡️ Environmental Sensors** - TCA9548A I2C multiplexer with SHT3x & BMP280

## ⚡ Quick Start

---

### Running the Dual Camera Face Tracker with Recognition

## 🚀 Quick Start

```bash

### 1. Face Tracking with Recognition# Run dual camera tracking with Hailo face detection and recognition

sudo python3 virtual_tracking_dual.py

```bash

# Run dual camera face tracking (Hailo-accelerated)# Or run with SINGLE camera only (lower CPU usage, no stereo depth)

sudo python3 virtual_tracking_dual.pysudo python3 virtual_tracking_dual.py --single-camera 0



# Single camera mode (lower CPU usage)# Custom camera selection

sudo python3 virtual_tracking_dual.py --single-camera 0sudo python3 virtual_tracking_dual.py --cameras 0 1  # dual camera

sudo python3 virtual_tracking_dual.py --cameras 1    # camera 1 only

# Open browser: http://localhost:5000

# View live face detection + name recognition# Then open browser to view: http://localhost:5000

```# Shows camera(s) with face tracking and name recognition

```

### 2. Enroll New Faces

### Enrolling People for Face Recognition

**Step 1: Capture Photos**

```bash**Step 1: Capture Photos**

# Capture enrollment photos with live preview```bash

sudo python3 scripts/capture_enrollment_photos.py --name "PersonName" --camera 0# Capture enrollment photos with live browser preview

sudo python3 scripts/capture_enrollment_photos.py --name "PersonName" --camera 0

# Open http://localhost:5000 to see live feed

# Position face at different angles (front, left, right, up, down)# Open http://localhost:5000 to see yourself

# Press ENTER to capture each photo (capture 5-10 photos)# Position face in different angles (front, left, right, up, down)

# Type 'done' when finished# Press ENTER to capture each photo (take 5-10 photos)

```# Type 'done' when finished

```

**Step 2: Enroll Photos into Database**

```bash**Step 2: Enroll the Photos**

# Process captured photos and create face templates```bash

python3 scripts/enroll_hailo.py --name "PersonName" --images enrollment_photos/PersonName_*.jpg# Enroll captured photos into face recognition database

python3 scripts/enroll_hailo.py --name "PersonName" --images enrollment_photos/PersonName_*.jpg

# Face templates stored in faces_db_hailo.pkl

```# The system uses Hailo-accelerated template matching for fast recognition

```

### 3. Calibrate Motors

**Bonus: Manage Enrolled People**

```bash```bash

# Run interactive motor calibration# List all enrolled people

python3 calibrate_motors.pypython3 scripts/enroll_hailo.py --list



# Test motor directions# View enrolled people and template counts

python3 test_motor_directions.py```



# Test individual motors### Running the Voice Assistant

python3 test_motors.py

``````bash

# METHOD 1: Run as Python module (RECOMMENDED)

### 4. Read Environmental Sensorscd /home/pi/work

python3 -m skipper.main

```bash

# Single reading from SHT3x and BMP280 via TCA9548A# METHOD 2: Use the wrapper script

python3 scripts/read_multiplexed_sensors.pycd /home/pi/work/skipper

./run_assistant.py

# Continuous monitoring mode

python3 scripts/read_multiplexed_sensors.py --continuous# METHOD 3: Run standalone face tracking only

```cd /home/pi/work/skipper

python3 follow_face.py

---

# Or use the startup script:

## 📁 Repository Structure./start_face_tracking.sh

```

```

skipper/### First Time Setup

├── virtual_tracking_dual.py      # Main face tracking application

├── virtual_tracking_hailo.py     # Hailo-specific tracking```bash

├── face_follow_manager.py        # Face following logic# 1. Install Python dependencies

├── follow_face.py                # Face follow coordinatorpip3 install luma.core luma.oled pillow sounddevice numpy opencv-python flask requests

├── enroll_face.py                # Face enrollment interface

├── klipper_motors.py             # Klipper motor control# 2. Install optional dependencies

├── calibrate_motors.py           # Motor calibration toolpip3 install vosk mediapipe  # For voice recognition and behavior analysis

├── config.py                     # System configuration

├── system_utils.py               # Utility functions# 3. Install system-level tools

│# - Ollama (for LLM)

├── scripts/# - Piper TTS (for speech synthesis)

│   ├── capture_enrollment_photos.py    # CSI camera enrollment# - Klipper & Moonraker (for motor control)

│   ├── capture_enrollment_photos_usb.py # USB webcam enrollment

│   ├── enroll_hailo.py                  # Hailo face enrollment# 4. Configure environment (see Configuration section below)

│   ├── read_multiplexed_sensors.py     # TCA9548A sensor reader

│   ├── test_tca9548a.py                # I2C multiplexer test# 5. Run the assistant

│   ├── fan_controller.py               # Temperature-based fan controlcd /home/pi/work

│   └── temperature_sensor.py           # BME680 sensor readerpython3 -m skipper.main

│```

├── test_*.py                     # Hardware test scripts

├── printer.cfg.example           # Klipper configuration template**Note:** If you don't have hardware components (OLED display, RGB LED, etc.), the system will run in limited mode with warnings but should still work for voice interaction.

├── KLIPPER_SETUP.md              # Klipper installation guide

├── DEPENDENCIES.md               # System dependencies## 🎯 What's New - Klipper Integration

└── faces_db_hailo.pkl            # Face recognition database

```The face tracking motors have been **converted from GPIO control to Klipper**:



---- ✅ **Smoother motion** - Klipper's motion planning

- ✅ **Better precision** - Hardware-timed stepping

## 🛠️ Hardware Requirements- ✅ **Network control** - Via Moonraker API

- ✅ **More flexible** - Easy configuration changes

### Core Components1

- **Raspberry Pi 5** (8GB recommended)### Files Changed

- **Hailo-8L HAT** (AI accelerator, 26 TOPS)

- **IMX708 CSI Cameras** (2x for stereo, or 1x for single mode)- `follow_face.py` - Now uses Klipper motor control

- **Stepper Motors** (2x for pan/tilt)- `config.py` - Added `KLIPPER_URL` configuration

- **Klipper-compatible MCU** (e.g., SKR Mini E3 V3.0)- `klipper_motors.py` - Motor control interface module

- `main.py` - Voice assistant integrates with face tracking

### Environmental Sensors (Optional)

- **TCA9548A I2C Multiplexer** (1-to-8 channel)## 📋 Requirements

- **SHT3x** - Temperature & Humidity sensor (0x44)

- **BMP280** - Temperature & Pressure sensor (0x76)**See `DEPENDENCIES.md` for complete installation instructions.**



### Power & Connections### Hardware

- **5V/5A USB-C Power Supply** (for Pi 5)- Raspberry Pi (tested on Pi 5)

- **12V Power Supply** (for stepper motors)- USB webcam (face tracking + behavior analysis)

- **CSI Ribbon Cables** (15-pin, 22-pin for Pi 5)- USB microphone (voice input)

- Audio output device (TTS playback)

---- 2x stepper motors (azimuth + altitude for face tracking)

- Klipper-compatible board (BTT Octopus, SKR, etc.)

## 📦 Software Dependencies- RGB LED (optional - status indicators)

- OLED display (optional - SH1107, 128x128)

### System Packages

```bash### Software - Python Packages

sudo apt update && sudo apt install -y \```bash

    python3-pip \# Required

    python3-picamera2 \pip3 install luma.core luma.oled pillow sounddevice numpy opencv-python flask requests

    python3-opencv \

    python3-numpy \# Optional but recommended

    python3-flask \pip3 install vosk mediapipe

    python3-smbus2 \```

    i2c-tools

```### Software - System Services

- **Ollama** - LLM server (local or remote)

### Python Packages  - Models: Llama 3.2, Llama 3.1, etc.

```bash- **Piper TTS** - Text-to-speech synthesis

pip3 install -r requirements.txt- **Klipper + Moonraker** - Motor control firmware

- **Vosk/Whisper** - Speech recognition

# Key dependencies:

# - hailo-platform (Hailo SDK)## 🔧 Setup Instructions

# - picamera2 (camera control)

# - opencv-python (image processing)### 1. Configure Klipper

# - flask (web interface)

# - smbus2 (I2C communication)Copy the example configuration:

```

```bash

### Klipper Setupcp printer.cfg.example ~/printer_data/config/printer.cfg

See [KLIPPER_SETUP.md](KLIPPER_SETUP.md) for complete installation guide.```



---Edit `~/printer_data/config/printer.cfg` and update:

- MCU serial port

## ⚙️ Configuration- Stepper pin assignments for your board

- Motor current settings (if using TMC drivers)

### Camera Configuration- Position limits (mechanical range)

Edit `config.py`:

```python**See `KLIPPER_SETUP.md` for detailed configuration guide.**

# Single or dual camera mode

CAMERA_INDICES = [0, 1]  # Dual camera### 2. Install Python Dependencies

# CAMERA_INDICES = [0]    # Single camera

```bash

# Camera resolutionpip3 install opencv-python flask numpy

CAMERA_WIDTH = 1640# Optional for behavior analysis:

CAMERA_HEIGHT = 1232pip3 install mediapipe

``````



### Motor Configuration### 3. Configure Environment

Edit `printer.cfg`:

```ini```bash

[stepper_x]  # Pan motorexport KLIPPER_URL="http://localhost:7125"  # Moonraker API

step_pin: PB13export KLIPPER_ENABLED="true"

dir_pin: !PB12```

enable_pin: !PB14

microsteps: 16Add to `~/.bashrc` to make permanent.

rotation_distance: 40

position_min: -180### 4. Test Klipper Connection

position_max: 180

homing_speed: 50```bash

# Check Klipper status

[stepper_y]  # Tilt motorcurl http://localhost:7125/printer/info

step_pin: PB10

dir_pin: !PB2# Should return JSON with "state": "ready"

enable_pin: !PB11```

microsteps: 16

rotation_distance: 40### 5. Run Face Tracking

position_min: -90

position_max: 90```bash

homing_speed: 50python3 follow_face.py

``````



### I2C Sensor ConfigurationAccess video stream: `http://<pi-ip>:5000`

Sensors configured in `scripts/read_multiplexed_sensors.py`:

```python## 🎮 Usage

# TCA9548A Multiplexer

MULTIPLEXER_ADDR = 0x70### Main Voice Assistant



# Sensors```bash

SENSOR_SHT3X_CHANNEL = 0# Start the full AI assistant

SENSOR_SHT3X_ADDR = 0x44python3 main.py



SENSOR_BMP280_CHANNEL = 1# Talk to the robot

SENSOR_BMP280_ADDR = 0x76# - Say "hey robot" or similar wake phrase

```# - Ask questions, request diagnostics, run scripts

# - Robot responds with TTS and follows your face

---

# Example interactions:

## 🔍 Testing & Verification# "What's the temperature?"

# "Run diagnostics"

### Camera Detection# "Tell me about yourself"

```bash# "Execute fan control script"

# Test Hailo face detection```

python3 test_hailo_face.py

### Standalone Face Tracking

# Test dual camera setup

python3 test_dual_camera_hailo.py```bash

# Run just face tracking (no voice assistant)

# Test Picamera2 + Hailo integration./start_face_tracking.sh

python3 test_picam2_hailo.py

```# View stream

# http://<pi-ip>:5000

### Motor Testing```

```bash

# Test motor directions### Voice Assistant Components

python3 test_motor_directions.py

```python

# Test motor movements# In your code

python3 test_motors.pyfrom voice_assistant.main import VoiceAssistant

from voice_assistant.face_follow_manager import FaceFollowManager

# Calibrate motor limitsfrom voice_assistant.ollama_client import chat_once

python3 calibrate_motors.pyfrom voice_assistant.piper_tts import PiperTTS

```

# Initialize components

### Sensor Testingface_manager = FaceFollowManager()

```bashtts = PiperTTS()

# Test I2C multiplexer and scan all channels

python3 scripts/test_tca9548a.py# Start face tracking

face_manager.start()

# Read SHT3x and BMP280 sensors

python3 scripts/read_multiplexed_sensors.py# Get LLM response

```response = chat_once(

    messages=[{"role": "user", "content": "Hello"}],

---    model="llama3.2"

)

## 📊 Face Recognition Quality

# Speak response

For best recognition accuracy:tts.speak(response)

- **10+ enrollment photos** per person

- **Varied angles**: front, left, right, up, down# Get behavior state (mood, hand gestures)

- **Consistent lighting**: avoid harsh shadowsbehavior = face_manager.get_latest_behavior()

- **Different expressions**: neutral, smiling```

- **Clear focus**: avoid motion blur

## ⚙️ Configuration

### Re-enrollment Example

```bash### Core System (config.py)

# Capture new photos

sudo python3 scripts/capture_enrollment_photos.py --name "Person" --camera 0```python

# Ollama LLM settings

# Enroll with better qualitypc_ollama_url = "http://192.168.1.6:11434/api/chat"  # Remote server

python3 scripts/enroll_hailo.py --name "Person" --images enrollment_photos/Person_*.jpgpi_ollama_url = "http://localhost:11434/api/chat"     # Local

```default_model = "llama3.2"



---# Piper TTS

piper_model = "/home/pi/piper-tts/piper/voices/en_US-joe-medium.onnx"

## 🔧 Troubleshootingrobot_preset = "metallic"  # Voice effect preset



### Camera Not Detected# Speech-to-Text

```bashstt_backend = "vosk"  # or "whisper"

# Check camera connectionvosk_model_dir = "/path/to/vosk-model"

vcgencmd get_camerawhisper_model_name = "small"



# Check device tree# Hardware

dmesg | grep imx708mic_alsa = "plughw:CARD=U0x46d0x821,DEV=0"

alsa_dev = "plughw:0,0"

# Reseat CSI ribbon cable firmlyred_pin, green_pin, blue_pin = 22, 17, 27  # RGB LED

``````



### Klipper Connection Issues### Environment Variables

```bash

# Check Klipper service| Variable | Default | Description |

sudo systemctl status klipper|----------|---------|-------------|

| **Voice Assistant** |||

# View Klipper logs| `STT_BACKEND` | `vosk` | Speech recognition backend |

tail -f /tmp/klippy.log| `WHISPER_MODEL` | `small` | Whisper model size |

| `PIPER_MODEL` | path | TTS voice model |

# Restart Klipper| `ROBOT_PRESET` | `metallic` | TTS voice effect |

sudo systemctl restart klipper| `MIC_DEV` | auto | ALSA microphone device |

```| **Face Tracking** |||

| `KLIPPER_URL` | `http://localhost:7125` | Moonraker API endpoint |

### I2C Sensor Issues| `KLIPPER_ENABLED` | `true` | Enable/disable Klipper control |

```bash| `FF_BEHAVIOR` | `true` | Enable MediaPipe behavior analysis |

# Scan I2C bus 1| `FF_BEHAVIOR_INTERVAL` | `0.6` | Behavior update interval (seconds) |

i2cdetect -y 1| **Perception LLM** |||

| `PERCEPTION_LLM` | `true` | Enable mood interpretation |

# Check multiplexer| `PERCEPTION_LLM_MODEL` | `llama3.2` | Model for perception |

python3 scripts/test_tca9548a.py| `PERCEPTION_LLM_COOLDOWN` | `3.0` | Cooldown between interpretations |



# Verify sensor addresses (0x44, 0x76, 0x70)### Tuning Parameters

```

Edit `follow_face.py`:

### Hailo HAT Issues

```bash```python

# Check Hailo device# Control tuning

hailortcli scanDEADBAND_PX = 16        # Dead zone (pixels)

K_P = 3.0               # Proportional gain

# Monitor Hailo temperatureMIN_RATE_HZ = 40        # Min speed

hailortcli monitorMAX_RATE_HZ = 1200      # Max speed

SMOOTHING = 0.35        # Motion smoothing (0-1)

# Check Hailo driver```

lsmod | grep hailo

```## 📖 Documentation



---- **`README.md`** (this file) - Project overview and quick start

- **`DEPENDENCIES.md`** - Complete installation guide for all dependencies

## 📚 Related Documentation- **`KLIPPER_SETUP.md`** - Detailed Klipper motor control setup

- **`printer.cfg.example`** - Example Klipper configuration

- **[KLIPPER_SETUP.md](KLIPPER_SETUP.md)** - Complete Klipper installation guide- **`MIGRATION_SUMMARY.md`** - Technical details of GPIO→Klipper conversion

- **[DEPENDENCIES.md](DEPENDENCIES.md)** - Detailed dependency list- **`QUICK_REFERENCE.txt`** - One-page command reference

- **[update_printer_cfg.md](update_printer_cfg.md)** - Klipper config updates- **`start_face_tracking.sh`** - Automated face tracking startup script

- **[follow_face_klipper.patch](follow_face_klipper.patch)** - Klipper face follow patch

## 🔍 Troubleshooting

---

### Cannot Connect to Klipper

## 🎯 Project Focus```bash

# Check services

This repository is specifically for:sudo systemctl status klipper moonraker

1. **Hailo-accelerated face detection & recognition**

2. **Klipper motor control for face tracking**# Test API

3. **Face enrollment and sample capture**curl http://localhost:7125/printer/info

4. **Motor calibration tools**```

5. **Environmental sensor integration (TCA9548A)**

### Motors Not Moving

**Voice assistant features** (TTS, STT, OLED, LED, Ollama) moved to:- Check Klipper state is "ready"

`../skipper-voice-assistant/`- Verify motor pins in `printer.cfg`

- Check `rotation_distance` setting

---- Look for errors: `tail -f /tmp/klippy.log`



## 📝 License### Face Not Detected

- Check lighting (detectors need good light)

MIT License - See LICENSE file for details.- Verify camera: `ls /dev/video*`

- View stream to see camera output

## 🤝 Contributing- Try different detector models



This is a focused hardware integration project. Contributions welcome for:### Jerky Motion

- Face tracking algorithm improvements- Increase `SMOOTHING` value

- Motor control optimizations- Adjust Klipper `max_accel` and `max_velocity`

- Sensor integration enhancements- Tune PID parameters

- Hailo model optimizations

**See `KLIPPER_SETUP.md` for more troubleshooting tips.**

---

## 🏗️ System Architecture

## 🔗 Hardware Links

### Voice Assistant Flow

- [Raspberry Pi 5](https://www.raspberrypi.com/products/raspberry-pi-5/)```

- [Hailo-8L HAT](https://hailo.ai/products/hailo-8l-ai-accelerator-hat/)┌─────────────┐

- [IMX708 Camera](https://www.raspberrypi.com/products/camera-module-3/)│ Microphone  │ → STTManager (Vosk/Whisper)

- [TCA9548A Multiplexer](https://learn.adafruit.com/adafruit-tca9548a-1-to-8-i2c-multiplexer-breakout)└─────┬───────┘

- [Klipper Firmware](https://www.klipper3d.org/)      │

┌─────▼──────────┐

---│ Voice Command  │

└─────┬──────────┘

**Last Updated:** November 2025      │

┌─────▼────────────┐
│ Ollama LLM       │ ← ConversationMemory (context)
│ (Llama 3.2)      │ ← DiagnosticsManager (system info)
└─────┬────────────┘ ← BehaviorMonitor (facial mood)
      │
┌─────▼────────┐
│ LLM Response │
└─────┬────────┘
      │
┌─────▼────────────┐
│ Piper TTS        │ → Audio Output
│ (Voice Synth)    │
└──────────────────┘
```

### Face Tracking Flow
```
┌─────────────────┐
│  USB Camera     │
└────────┬────────┘
         │
┌────────▼────────┐
│  follow_face.py │ ← OpenCV face detection
│  Face Detection │ ← MediaPipe behavior analysis
└────────┬────────┘
         │
┌────────▼────────┐
│  AxisControl    │ ← Converts pixel error → position
└────────┬────────┘
         │
┌────────▼────────────────┐
│ KlipperMotorController │ ← HTTP API interface
└────────┬────────────────┘
         │ G-code over HTTP
┌────────▼────────┐
│  Moonraker API  │
└────────┬────────┘
         │
┌────────▼────────┐
│ Klipper Firmware│ ← Motion planning
└────────┬────────┘
         │
┌────────▼────────┐
│ Stepper Motors  │ ← Pan/Tilt mechanism
└─────────────────┘
```

### Component Integration
```
┌──────────────────────────────────────────┐
│            main.py                       │
│        (Voice Assistant Core)            │
└───┬───────────┬──────────────┬───────────┘
    │           │              │
    ▼           ▼              ▼
┌────────┐ ┌─────────┐  ┌──────────────┐
│ STT    │ │ TTS     │  │ Face Follow  │
│Manager │ │ (Piper) │  │ Manager      │
└────────┘ └─────────┘  └──────┬───────┘
                               │
                        ┌──────▼────────┐
                        │ follow_face.py│
                        │ + Klipper     │
                        └───────────────┘
```

## 🚀 Performance

### Voice Assistant
- **STT Latency**: ~200-500ms (Vosk), ~1-2s (Whisper)
- **LLM Response**: 1-5s (depends on model & hardware)
- **TTS Generation**: ~100-300ms per sentence
- **Total Response Time**: 2-8s from speech to audio output

### Face Tracking
- **Face Detection**: 15-30 FPS (depends on detector)
- **Motor Update Rate**: ~100 Hz via Klipper
- **Tracking Latency**: ~50-100ms end-to-end
- **Stream Quality**: 640x480 MJPEG @ ~15 FPS
- **Behavior Analysis**: Updates every 0.6s (configurable)

## 📝 Features & Notes

### Voice Assistant
- ✅ **Conversation Memory** - Remembers context (20 messages)
- ✅ **Diagnostics** - `/diag` command for system checks
- ✅ **Script Execution** - Can run custom scripts via voice
- ✅ **Mood Awareness** - Interprets facial expressions via LLM
- ✅ **LED Feedback** - RGB LED shows status (idle/think/speak)
- ✅ **OLED Display** - Shows status and transcriptions

### Face Tracking
- ✅ **Auto-detect** - YuNet → DNN → Haar cascade fallback
- ✅ **Auto-disable** - Motors power down after 2s idle
- ✅ **Size Filtering** - Face must be >0.4% of frame
- ✅ **Smooth Motion** - EWMA smoothing + Klipper planning
- ✅ **Web Stream** - MJPEG stream for debugging
- ✅ **Emergency Stop** - `Ctrl+C` or Klipper `M112`

## 🎭 Example Interactions

```
User: "Hey robot, what's your status?"
Robot: [RGB turns blue] "All systems nominal. CPU at 45°C, uptime 3 days."
       [Face tracking follows you while speaking]

User: "Run a diagnostic"
Robot: [Checks system] "Memory usage 45%, disk 60% full, all services running."

User: "Tell me a joke"
Robot: [Face tracks you] "Why did the robot go to therapy? 
       It had too many bits to process!"

User: [Waves hand]
Robot: [Detects hand gesture via MediaPipe, interprets with LLM]
       "I see you waving! Hello there!"

User: [Frowns]
Robot: [Detects mood change] "You seem concerned. Is everything okay?"
```

## 🧩 Module Overview

| Module | Purpose |
|--------|---------|
| `main.py` | Voice assistant core loop |
| `ollama_client.py` | LLM communication |
| `piper_tts.py` | Text-to-speech synthesis |
| `stt_backends.py` | Speech recognition (Vosk/Whisper) |
| `follow_face.py` | Face tracking standalone |
| `face_follow_manager.py` | Face tracking integration |
| `klipper_motors.py` | Klipper motor control API |
| `led_manager.py` | RGB LED status indicators |
| `display_manager.py` | OLED display control |
| `memory_manager.py` | Conversation context |
| `diagnostics.py` | System diagnostics |
| `script_manager.py` | Execute custom scripts |
| `perception/` | Behavior & mood analysis |

## 🔗 Related Projects

- **Ollama** - Local LLM inference
- **Klipper** - 3D printer firmware (repurposed for robotics)
- **Piper TTS** - Fast neural TTS
- **Vosk** - Offline speech recognition
- **MediaPipe** - ML perception pipeline

## 📄 License

[Your license here]

## 🙏 Credits

- **Ollama** - LLM inference
- **Piper** - Text-to-speech
- **Vosk/Whisper** - Speech recognition
- **OpenCV** - Computer vision & face detection
- **Klipper** - Motion control firmware
- **MediaPipe** - Behavior & pose analysis

