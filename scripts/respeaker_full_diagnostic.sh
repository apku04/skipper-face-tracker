#!/bin/bash
# Complete ReSpeaker 2-Mic HAT Diagnostic

echo "==================================="
echo "ReSpeaker 2-Mic HAT Diagnostic"
echo "==================================="
echo ""

echo "1. Checking I2C codec (should be at 0x1a)..."
i2cdetect -y 1 | grep "1a" && echo "   ✓ Codec detected at 0x1a" || echo "   ✗ Codec NOT detected"
echo ""

echo "2. Checking ALSA devices..."
echo "   Playback devices:"
aplay -l | grep sndrpigooglevoi && echo "   ✓ ReSpeaker playback found" || echo "   ✗ ReSpeaker playback NOT found"
echo ""
echo "   Capture devices:"
arecord -l | grep sndrpigooglevoi && echo "   ✓ ReSpeaker capture found" || echo "   ✗ ReSpeaker capture NOT found"
echo ""

echo "3. Checking boot configuration..."
if grep -q "dtoverlay=googlevoicehat-soundcard" /boot/firmware/config.txt; then
    echo "   ✓ googlevoicehat-soundcard overlay enabled"
else
    echo "   ✗ googlevoicehat-soundcard overlay NOT found"
fi

if grep -q "dtoverlay=i2s-mmap" /boot/firmware/config.txt; then
    echo "   ✓ i2s-mmap overlay enabled"
else
    echo "   ✗ i2s-mmap overlay NOT found"
fi
echo ""

echo "4. Testing speaker output (card 1, 440Hz tone for 2 seconds)..."
speaker-test -D plughw:1,0 -c 1 -t sine -f 440 -l 1 2>&1 | tail -3
echo ""

echo "5. Recording 3-second mic sample..."
arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 3 /tmp/respeaker_test.wav 2>&1
echo ""

echo "6. Analyzing recording..."
if [ -f /tmp/respeaker_test.wav ]; then
    size=$(stat -c%s /tmp/respeaker_test.wav)
    echo "   Recording size: $size bytes"
    if [ "$size" -gt 1000 ]; then
        echo "   ✓ Recording created (size looks reasonable)"
    else
        echo "   ✗ Recording too small (mic may not be working)"
    fi
else
    echo "   ✗ Recording failed"
fi
echo ""

echo "==================================="
echo "Summary"
echo "==================================="
echo ""
echo "Common issues:"
echo "  - Speaker not working:"
echo "    * Check if speaker connected to HAT's 3.5mm jack (NOT Pi's jack)"
echo "    * GPIO 12 may need to be enabled for amplifier"
echo "    * Try: gpioset gpiochip4 12=1"
echo ""
echo "  - Microphone not working:"
echo "    * Keyestudio/Seeed ReSpeaker uses different codec than Google AIY"
echo "    * May need different device tree overlay"
echo "    * Check dmesg for codec initialization errors"
echo ""
echo "Next steps:"
echo "  1. Try enabling GPIO 12: sudo gpioset gpiochip4 12=1"
echo "  2. Check kernel messages: dmesg | grep -i 'audio\|codec\|i2s'"
echo "  3. Verify physical connections"
echo ""
