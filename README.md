# Skipper - AI Voice Assistant Robot with Face Tracking

**Complete AI-powered robot assistant** featuring:
- 🤖 **LLM Integration** - Ollama-powered conversational AI (Llama 3.2)
- 🎤 **Speech-to-Text** - Vosk/Whisper for voice recognition
- 🔊 **Text-to-Speech** - Piper TTS with voice effects
- 👁️ **Face Tracking** - Real-time face following with Klipper motor control
- 😊 **Behavior Analysis** - MediaPipe mood & gesture detection
- 💾 **Conversation Memory** - Context-aware responses
- 📊 **System Diagnostics** - Self-monitoring and reporting

## ⚡ Quick Start

### Running the Voice Assistant

```bash
# METHOD 1: Run as Python module (RECOMMENDED)
cd /home/pi/work
python3 -m skipper.main

# METHOD 2: Use the wrapper script
cd /home/pi/work/skipper
./run_assistant.py

# METHOD 3: Run standalone face tracking only
cd /home/pi/work/skipper
python3 follow_face.py

# Or use the startup script:
./start_face_tracking.sh
```

### First Time Setup

```bash
# 1. Install Python dependencies
pip3 install luma.core luma.oled pillow sounddevice numpy opencv-python flask requests

# 2. Install optional dependencies
pip3 install vosk mediapipe  # For voice recognition and behavior analysis

# 3. Install system-level tools
# - Ollama (for LLM)
# - Piper TTS (for speech synthesis)
# - Klipper & Moonraker (for motor control)

# 4. Configure environment (see Configuration section below)

# 5. Run the assistant
cd /home/pi/work
python3 -m skipper.main
```

**Note:** If you don't have hardware components (OLED display, RGB LED, etc.), the system will run in limited mode with warnings but should still work for voice interaction.

## 🎯 What's New - Klipper Integration

The face tracking motors have been **converted from GPIO control to Klipper**:

- ✅ **Smoother motion** - Klipper's motion planning
- ✅ **Better precision** - Hardware-timed stepping
- ✅ **Network control** - Via Moonraker API
- ✅ **More flexible** - Easy configuration changes

### Files Changed

- `follow_face.py` - Now uses Klipper motor control
- `config.py` - Added `KLIPPER_URL` configuration
- `klipper_motors.py` - Motor control interface module
- `main.py` - Voice assistant integrates with face tracking

## 📋 Requirements

**See `DEPENDENCIES.md` for complete installation instructions.**

### Hardware
- Raspberry Pi (tested on Pi 5)
- USB webcam (face tracking + behavior analysis)
- USB microphone (voice input)
- Audio output device (TTS playback)
- 2x stepper motors (azimuth + altitude for face tracking)
- Klipper-compatible board (BTT Octopus, SKR, etc.)
- RGB LED (optional - status indicators)
- OLED display (optional - SH1107, 128x128)

### Software - Python Packages
```bash
# Required
pip3 install luma.core luma.oled pillow sounddevice numpy opencv-python flask requests

# Optional but recommended
pip3 install vosk mediapipe
```

### Software - System Services
- **Ollama** - LLM server (local or remote)
  - Models: Llama 3.2, Llama 3.1, etc.
- **Piper TTS** - Text-to-speech synthesis
- **Klipper + Moonraker** - Motor control firmware
- **Vosk/Whisper** - Speech recognition

## 🔧 Setup Instructions

### 1. Configure Klipper

Copy the example configuration:

```bash
cp printer.cfg.example ~/printer_data/config/printer.cfg
```

Edit `~/printer_data/config/printer.cfg` and update:
- MCU serial port
- Stepper pin assignments for your board
- Motor current settings (if using TMC drivers)
- Position limits (mechanical range)

**See `KLIPPER_SETUP.md` for detailed configuration guide.**

### 2. Install Python Dependencies

```bash
pip3 install opencv-python flask numpy
# Optional for behavior analysis:
pip3 install mediapipe
```

### 3. Configure Environment

```bash
export KLIPPER_URL="http://localhost:7125"  # Moonraker API
export KLIPPER_ENABLED="true"
```

Add to `~/.bashrc` to make permanent.

### 4. Test Klipper Connection

```bash
# Check Klipper status
curl http://localhost:7125/printer/info

# Should return JSON with "state": "ready"
```

### 5. Run Face Tracking

```bash
python3 follow_face.py
```

Access video stream: `http://<pi-ip>:5000`

## 🎮 Usage

### Main Voice Assistant

```bash
# Start the full AI assistant
python3 main.py

# Talk to the robot
# - Say "hey robot" or similar wake phrase
# - Ask questions, request diagnostics, run scripts
# - Robot responds with TTS and follows your face

# Example interactions:
# "What's the temperature?"
# "Run diagnostics"
# "Tell me about yourself"
# "Execute fan control script"
```

### Standalone Face Tracking

```bash
# Run just face tracking (no voice assistant)
./start_face_tracking.sh

# View stream
# http://<pi-ip>:5000
```

### Voice Assistant Components

```python
# In your code
from voice_assistant.main import VoiceAssistant
from voice_assistant.face_follow_manager import FaceFollowManager
from voice_assistant.ollama_client import chat_once
from voice_assistant.piper_tts import PiperTTS

# Initialize components
face_manager = FaceFollowManager()
tts = PiperTTS()

# Start face tracking
face_manager.start()

# Get LLM response
response = chat_once(
    messages=[{"role": "user", "content": "Hello"}],
    model="llama3.2"
)

# Speak response
tts.speak(response)

# Get behavior state (mood, hand gestures)
behavior = face_manager.get_latest_behavior()
```

## ⚙️ Configuration

### Core System (config.py)

```python
# Ollama LLM settings
pc_ollama_url = "http://192.168.1.6:11434/api/chat"  # Remote server
pi_ollama_url = "http://localhost:11434/api/chat"     # Local
default_model = "llama3.2"

# Piper TTS
piper_model = "/home/pi/piper-tts/piper/voices/en_US-joe-medium.onnx"
robot_preset = "metallic"  # Voice effect preset

# Speech-to-Text
stt_backend = "vosk"  # or "whisper"
vosk_model_dir = "/path/to/vosk-model"
whisper_model_name = "small"

# Hardware
mic_alsa = "plughw:CARD=U0x46d0x821,DEV=0"
alsa_dev = "plughw:0,0"
red_pin, green_pin, blue_pin = 22, 17, 27  # RGB LED
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| **Voice Assistant** |||
| `STT_BACKEND` | `vosk` | Speech recognition backend |
| `WHISPER_MODEL` | `small` | Whisper model size |
| `PIPER_MODEL` | path | TTS voice model |
| `ROBOT_PRESET` | `metallic` | TTS voice effect |
| `MIC_DEV` | auto | ALSA microphone device |
| **Face Tracking** |||
| `KLIPPER_URL` | `http://localhost:7125` | Moonraker API endpoint |
| `KLIPPER_ENABLED` | `true` | Enable/disable Klipper control |
| `FF_BEHAVIOR` | `true` | Enable MediaPipe behavior analysis |
| `FF_BEHAVIOR_INTERVAL` | `0.6` | Behavior update interval (seconds) |
| **Perception LLM** |||
| `PERCEPTION_LLM` | `true` | Enable mood interpretation |
| `PERCEPTION_LLM_MODEL` | `llama3.2` | Model for perception |
| `PERCEPTION_LLM_COOLDOWN` | `3.0` | Cooldown between interpretations |

### Tuning Parameters

Edit `follow_face.py`:

```python
# Control tuning
DEADBAND_PX = 16        # Dead zone (pixels)
K_P = 3.0               # Proportional gain
MIN_RATE_HZ = 40        # Min speed
MAX_RATE_HZ = 1200      # Max speed
SMOOTHING = 0.35        # Motion smoothing (0-1)
```

## 📖 Documentation

- **`README.md`** (this file) - Project overview and quick start
- **`DEPENDENCIES.md`** - Complete installation guide for all dependencies
- **`KLIPPER_SETUP.md`** - Detailed Klipper motor control setup
- **`printer.cfg.example`** - Example Klipper configuration
- **`MIGRATION_SUMMARY.md`** - Technical details of GPIO→Klipper conversion
- **`QUICK_REFERENCE.txt`** - One-page command reference
- **`start_face_tracking.sh`** - Automated face tracking startup script

## 🔍 Troubleshooting

### Cannot Connect to Klipper
```bash
# Check services
sudo systemctl status klipper moonraker

# Test API
curl http://localhost:7125/printer/info
```

### Motors Not Moving
- Check Klipper state is "ready"
- Verify motor pins in `printer.cfg`
- Check `rotation_distance` setting
- Look for errors: `tail -f /tmp/klippy.log`

### Face Not Detected
- Check lighting (detectors need good light)
- Verify camera: `ls /dev/video*`
- View stream to see camera output
- Try different detector models

### Jerky Motion
- Increase `SMOOTHING` value
- Adjust Klipper `max_accel` and `max_velocity`
- Tune PID parameters

**See `KLIPPER_SETUP.md` for more troubleshooting tips.**

## 🏗️ System Architecture

### Voice Assistant Flow
```
┌─────────────┐
│ Microphone  │ → STTManager (Vosk/Whisper)
└─────┬───────┘
      │
┌─────▼──────────┐
│ Voice Command  │
└─────┬──────────┘
      │
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

