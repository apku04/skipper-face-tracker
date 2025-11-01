#!/bin/bash
# Test ReSpeaker 2-Mic Pi HAT
# Tests microphone recording and speaker playback

echo "=================================="
echo "ReSpeaker 2-Mic Pi HAT Test"
echo "=================================="
echo ""

# List audio devices
echo "Available Playback Devices:"
aplay -l
echo ""

echo "Available Capture Devices:"
arecord -l
echo ""

# Find the sound card
CARD=$(aplay -l | grep -i "seeed\|voice" | head -1 | grep -oP 'card \K[0-9]+')

if [ -z "$CARD" ]; then
    echo "❌ ReSpeaker HAT not found!"
    echo "   Make sure you've run setup_respeaker.sh and rebooted."
    exit 1
fi

echo "✓ Found ReSpeaker on card $CARD"
echo ""

# Test 1: Speaker test with tone
echo "=================================="
echo "Test 1: Speaker Test (3-second tone)"
echo "=================================="
echo "You should hear a tone from the speaker..."
speaker-test -c2 -t wav -l 1 -D plughw:$CARD,0

echo ""
echo "Did you hear the test sound? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "✓ Speaker working!"
else
    echo "⚠ Speaker test failed. Check connections."
fi

echo ""
echo "=================================="
echo "Test 2: Microphone Test (5-second recording)"
echo "=================================="
echo "Recording from microphones for 5 seconds..."
echo "Speak into the microphone now!"

TESTFILE="/tmp/respeaker_test_$(date +%s).wav"
arecord -D plughw:$CARD,0 -f cd -t wav -d 5 -r 16000 -c 2 "$TESTFILE"

echo ""
echo "✓ Recording complete: $TESTFILE"
echo ""
echo "Playing back recording..."
aplay -D plughw:$CARD,0 "$TESTFILE"

echo ""
echo "Did you hear your recording? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "✓ Microphone working!"
else
    echo "⚠ Microphone test failed. Check microphone position."
fi

echo ""
echo "=================================="
echo "Test 3: Volume Levels"
echo "=================================="
echo "Checking mixer settings..."
amixer -c $CARD contents

echo ""
echo "=================================="
echo "Test Complete!"
echo "=================================="
echo ""
echo "ALSA device strings for your apps:"
echo "  Playback:  plughw:$CARD,0  or  hw:$CARD,0"
echo "  Capture:   plughw:$CARD,0  or  hw:$CARD,0"
echo ""
echo "Recorded test file saved to: $TESTFILE"
echo "You can delete it with: rm $TESTFILE"
echo ""
