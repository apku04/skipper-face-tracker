#!/bin/bash
# Test USB Audio Adapter

echo "=== Checking for USB Audio Device ==="
lsusb | grep -i "audio\|AB13X"

echo ""
echo "=== Available Audio Cards ==="
cat /proc/asound/cards

echo ""
echo "=== Trying to play test sound on all available cards ==="

# Try each card
for card in 0 1 2 3; do
    if aplay -l 2>/dev/null | grep -q "card $card"; then
        echo ""
        echo "Testing card $card..."
        speaker-test -D plughw:$card,0 -c 2 -r 48000 -F S16_LE -t sine -f 440 -l 1 2>&1 | head -10 &
        pid=$!
        sleep 2
        kill $pid 2>/dev/null
        wait $pid 2>/dev/null
    fi
done

echo ""
echo "=== If you heard sound, note which card worked! ==="
