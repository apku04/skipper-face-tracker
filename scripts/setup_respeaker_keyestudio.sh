#!/bin/bash
# Setup script for Keyestudio/Seeed ReSpeaker 2-Mic HAT V1.0
# This HAT uses WM8960 codec, NOT Google VoiceHAT codec

echo "==================================="
echo "ReSpeaker 2-Mic HAT Setup"
echo "Keyestudio/Seeed Version"
echo "==================================="
echo ""

CONFIG_FILE="/boot/firmware/config.txt"

echo "Current overlay: googlevoicehat-soundcard"
echo "This is designed for Google AIY VoiceHAT, not Keyestudio ReSpeaker"
echo ""
echo "The Keyestudio ReSpeaker 2-Mic HAT V1.0 uses:"
echo "  - WM8960 audio codec at I2C address 0x1a"
echo "  - I2S interface for audio"
echo "  - 2x MEMS microphones"
echo "  - 3.5mm audio jack for speaker output"
echo ""

echo "Available options:"
echo ""
echo "Option 1: Use seeed-2mic-voicecard driver (recommended)"
echo "  - Download from: https://github.com/respeaker/seeed-voicecard"
echo "  - Provides proper WM8960 support"
echo ""

echo "Option 2: Try alternative overlay (simpler but may not work)"
echo "  - Use 'wm8960-soundcard' overlay if available"
echo ""

echo "Option 3: Keep current googlevoicehat-soundcard (limited)"
echo "  - Already configured"
echo "  - May work partially (speaker/mic issues expected)"
echo ""

read -p "Install seeed-voicecard driver? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Installing seeed-voicecard driver..."
    cd /tmp
    if [ -d "seeed-voicecard" ]; then
        rm -rf seeed-voicecard
    fi
    git clone https://github.com/respeaker/seeed-voicecard
    cd seeed-voicecard
    sudo ./install.sh
    echo ""
    echo "Installation complete!"
    echo "Please reboot: sudo reboot"
else
    echo ""
    echo "Skipping installation."
    echo ""
    echo "Manual testing options:"
    echo ""
    echo "1. Test mic with recording:"
    echo "   arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav"
    echo "   aplay test.wav  # Play through USB to hear if mic worked"
    echo ""
    echo "2. Check if codec responds:"
    echo "   i2cdetect -y 1  # Should see device at 0x1a"
    echo ""
    echo "3. View kernel messages:"
    echo "   dmesg | grep -i wm8960"
    echo "   dmesg | grep -i voicehat"
fi
