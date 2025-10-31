#!/bin/bash
# Quick start script for Klipper-based face tracking

set -e

echo "================================================"
echo "Klipper Face Tracking - Startup Script"
echo "================================================"
echo ""

# Check if Klipper is running
echo "[1/5] Checking Klipper status..."
if systemctl is-active --quiet klipper; then
    echo "✓ Klipper is running"
else
    echo "✗ Klipper is not running!"
    echo "  Start it with: sudo systemctl start klipper"
    exit 1
fi

# Check if Moonraker is running
echo "[2/5] Checking Moonraker status..."
if systemctl is-active --quiet moonraker; then
    echo "✓ Moonraker is running"
else
    echo "✗ Moonraker is not running!"
    echo "  Start it with: sudo systemctl start moonraker"
    exit 1
fi

# Test Moonraker API connection
echo "[3/5] Testing Moonraker API..."
KLIPPER_URL="${KLIPPER_URL:-http://localhost:7125}"
if curl -s "${KLIPPER_URL}/printer/info" > /dev/null; then
    STATE=$(curl -s "${KLIPPER_URL}/printer/info" | python3 -c "import sys, json; print(json.load(sys.stdin)['result']['state'])" 2>/dev/null || echo "unknown")
    echo "✓ Moonraker API responding (state: $STATE)"
    
    if [ "$STATE" != "ready" ]; then
        echo "⚠ Warning: Klipper state is '$STATE' (expected 'ready')"
        echo "  You may need to home or initialize Klipper first"
    fi
else
    echo "✗ Cannot connect to Moonraker at $KLIPPER_URL"
    echo "  Check KLIPPER_URL environment variable"
    exit 1
fi

# Check Python dependencies
echo "[4/5] Checking Python dependencies..."
python3 -c "import cv2" 2>/dev/null && echo "✓ OpenCV (cv2) installed" || echo "✗ OpenCV missing - install with: pip3 install opencv-python"
python3 -c "import flask" 2>/dev/null && echo "✓ Flask installed" || echo "✗ Flask missing - install with: pip3 install flask"
python3 -c "import numpy" 2>/dev/null && echo "✓ NumPy installed" || echo "✗ NumPy missing - install with: pip3 install numpy"
python3 -c "import mediapipe" 2>/dev/null && echo "✓ MediaPipe installed (optional)" || echo "⚠ MediaPipe not installed (optional - disables behavior analysis)"

# Check camera
echo "[5/5] Checking camera..."
if [ -c /dev/video0 ]; then
    echo "✓ Camera device found at /dev/video0"
else
    echo "⚠ No camera found at /dev/video0"
    echo "  Available video devices:"
    ls -la /dev/video* 2>/dev/null || echo "  None found"
fi

echo ""
echo "================================================"
echo "Pre-flight checks complete!"
echo "================================================"
echo ""

# Ask if user wants to start
read -p "Start face tracking now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting face tracking..."
    echo "Press Ctrl+C to stop"
    echo ""
    echo "View stream at: http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    sleep 2
    
    cd "$(dirname "$0")"
    python3 follow_face.py
else
    echo ""
    echo "To start manually, run:"
    echo "  cd $(dirname "$0")"
    echo "  python3 follow_face.py"
    echo ""
    echo "View stream at: http://$(hostname -I | awk '{print $1}'):5000"
fi
