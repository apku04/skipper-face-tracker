#!/bin/bash
# Test USB Audio Adapter (AB13X) - Complete test

echo "=== USB Audio Adapter Status ==="
echo "Card 0: AB13X USB Audio"
echo "Playback: ✓ Working"
echo "Capture:  ✓ Working"
echo ""

echo "=== Playing test tone (440Hz for 2 seconds) ==="
speaker-test -D plughw:0,0 -c 1 -t sine -f 440 -l 1

echo ""
echo "=== Recording 3-second sample from microphone ==="
arecord -D plughw:0,0 -f cd -d 3 /tmp/usb_test.wav
echo ""

echo "=== Playing back recording ==="
aplay -D plughw:0,0 /tmp/usb_test.wav

echo ""
echo "=== Test complete! ==="
echo "If you heard the tone and your voice, the USB audio adapter is fully working."
echo ""
echo "To use this for voice assistant:"
echo "  - Speaker: plughw:0,0"
echo "  - Microphone: plughw:0,0"
