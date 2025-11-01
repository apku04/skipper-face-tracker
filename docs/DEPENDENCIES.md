# Skipper Dependencies

## Required Python Packages

### Core System
```bash
pip3 install luma.core luma.oled pillow sounddevice numpy opencv-python flask requests
```

- **luma.core, luma.oled** - OLED display support (SH1107)
- **pillow** - Image processing for display
- **sounddevice** - Audio I/O
- **numpy** - Numerical computing
- **opencv-python** - Computer vision & face detection
- **flask** - Web server for video streaming
- **requests** - HTTP client for Ollama API

### Optional But Recommended
```bash
pip3 install vosk mediapipe
```

- **vosk** - Offline speech recognition (alternative: whisper)
- **mediapipe** - Facial expression & gesture detection

### For Whisper STT (alternative to Vosk)
```bash
pip3 install openai-whisper
```

## System-Level Dependencies

### Ollama (LLM Server)
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.2

# Start the service
systemctl --user enable ollama
systemctl --user start ollama
```

### Piper TTS (Text-to-Speech)
```bash
# Download Piper
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
tar xzf piper_arm64.tar.gz
cd piper

# Download a voice model
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx.json
```

### Klipper & Moonraker (Motor Control)
```bash
# Install Klipper
cd ~
git clone https://github.com/Klipper3d/klipper
./klipper/scripts/install-octopi.sh

# Install Moonraker
cd ~
git clone https://github.com/Arksine/moonraker
./moonraker/scripts/install-moonraker.sh

# Configure printer.cfg (see printer.cfg.example)
cp ~/work/skipper/printer.cfg.example ~/printer_data/config/printer.cfg

# Start services
sudo systemctl start klipper moonraker
```

## Hardware Requirements

### Minimum (Voice Only)
- Raspberry Pi 3/4/5
- USB microphone
- Audio output (3.5mm or USB)

### Full System
- Raspberry Pi 5 (recommended)
- USB webcam (face tracking)
- USB microphone (voice input)
- Audio output device
- 2x stepper motors with drivers
- Klipper-compatible control board (e.g., BTT Octopus, SKR)
- RGB LED (optional - GPIO pins 22, 17, 27)
- SH1107 OLED display (optional - I2C)

## Verifying Installation

```bash
# Check Python packages
python3 -c "import luma.core, cv2, flask, requests, numpy, sounddevice; print('✓ Core packages OK')"
python3 -c "import vosk; print('✓ Vosk OK')" || echo "⚠ Vosk not installed"
python3 -c "import mediapipe; print('✓ MediaPipe OK')" || echo "⚠ MediaPipe not installed"

# Test OLED display
cd /home/pi/work/skipper
python3 test_display.py

# Check I2C devices
i2cdetect -y 1
# Should show device at 0x3c

# Check system services
systemctl status ollama --user
systemctl status klipper
systemctl status moonraker

# Check Ollama
curl http://localhost:11434/api/tags

# Check Klipper/Moonraker
curl http://localhost:7125/printer/info

# Check Piper
~/piper/piper --help
```

## Quick Install Script

```bash
#!/bin/bash
# install_dependencies.sh

echo "Installing Python packages..."
pip3 install luma.core luma.oled pillow sounddevice numpy opencv-python flask requests vosk mediapipe

echo "Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl https://ollama.ai/install.sh | sh
    ollama pull llama3.2
else
    echo "✓ Ollama already installed"
fi

echo "Checking Piper..."
if [ ! -f ~/piper/piper ]; then
    echo "Downloading Piper..."
    cd ~
    wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
    tar xzf piper_arm64.tar.gz
    cd piper
    wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx
    wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx.json
else
    echo "✓ Piper already installed"
fi

echo ""
echo "✓ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure Klipper (see KLIPPER_SETUP.md)"
echo "2. Update config.py with your settings"
echo "3. Run: cd /home/pi/work && python3 -m skipper.main"
```

## Troubleshooting

### ImportError: No module named 'X'
```bash
# Install the missing module
pip3 install <module_name>

# Or install all at once
pip3 install -r requirements.txt  # if you create one
```

### OSError: [Errno 121] Remote I/O error (OLED display)
```bash
# Test if display is detected
i2cdetect -y 1
# Should show device at 0x3c

# Test display independently
cd /home/pi/work/skipper
python3 test_display.py

# If test passes but main.py fails:
# - Display should now work (timing fix added)
# - System will gracefully disable display and continue if error persists
```

If display test fails:
- Check power connections (3.3V, GND)
- Check I2C connections (SDA to GPIO2, SCL to GPIO3)
- Verify I2C is enabled: `sudo raspi-config` → Interface Options → I2C
- Try rebooting

### RGB LED warnings
Normal if LED is not connected. Configure LED pins in config.py or disable LED support.

### Vosk/Whisper not found
```bash
# For Vosk
pip3 install vosk
# Download model: https://alphacephei.com/vosk/models

# For Whisper
pip3 install openai-whisper
```

### Ollama connection refused
```bash
# Start Ollama
systemctl --user start ollama

# Or check if running on different host (update config.py)
```

### Klipper/Moonraker not responding
```bash
sudo systemctl status klipper moonraker
sudo systemctl start klipper moonraker

# Check logs
tail -f /tmp/klippy.log
journalctl -u moonraker -f
```
