#!/bin/bash
# ReSpeaker 2-Mic Pi HAT Setup Script
# For Raspberry Pi 5

echo "=================================="
echo "ReSpeaker 2-Mic Pi HAT Setup"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

echo ""
echo "Step 1: Enabling I2S audio in config.txt..."

# Backup config
cp /boot/firmware/config.txt /boot/firmware/config.txt.backup.$(date +%Y%m%d_%H%M%S)

# Check if already configured
if grep -q "dtoverlay=i2s-mmap" /boot/firmware/config.txt; then
    echo "  ✓ i2s-mmap already configured"
else
    echo "dtoverlay=i2s-mmap" >> /boot/firmware/config.txt
    echo "  ✓ Added i2s-mmap overlay"
fi

if grep -q "dtoverlay=googlevoicehat-soundcard" /boot/firmware/config.txt; then
    echo "  ✓ googlevoicehat-soundcard already configured"
else
    echo "dtoverlay=googlevoicehat-soundcard" >> /boot/firmware/config.txt
    echo "  ✓ Added googlevoicehat-soundcard overlay"
fi

echo ""
echo "Step 2: Installing required packages..."
apt-get update
apt-get install -y alsa-utils i2c-tools

echo ""
echo "Step 3: Checking I2C devices..."
i2cdetect -y 1

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Reboot your Pi: sudo reboot"
echo "2. After reboot, run test script: bash scripts/test_respeaker.sh"
echo ""
