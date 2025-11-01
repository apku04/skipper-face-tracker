#!/bin/bash
# Install boot diagnostics service

set -e

SERVICE_NAME="boot-diagnostics.service"
SERVICE_FILE="/home/pi/work/skipper/services/${SERVICE_NAME}"
SYSTEMD_PATH="/etc/systemd/system/${SERVICE_NAME}"

echo "Installing Boot Diagnostics Service..."
echo ""

# Make Python script executable
chmod +x /home/pi/work/skipper/services/boot_diagnostics.py
echo "✓ Made boot_diagnostics.py executable"

# Stop and disable old boot-status-led service if it exists
if systemctl is-active --quiet boot-status-led.service; then
    sudo systemctl stop boot-status-led.service
    echo "✓ Stopped old boot-status-led service"
fi

if systemctl is-enabled --quiet boot-status-led.service 2>/dev/null; then
    sudo systemctl disable boot-status-led.service
    echo "✓ Disabled old boot-status-led service"
fi

# Copy service file to systemd
sudo cp "${SERVICE_FILE}" "${SYSTEMD_PATH}"
echo "✓ Copied service file to ${SYSTEMD_PATH}"

# Reload systemd
sudo systemctl daemon-reload
echo "✓ Reloaded systemd daemon"

# Enable service (start on boot)
sudo systemctl enable ${SERVICE_NAME}
echo "✓ Enabled ${SERVICE_NAME}"

# Start service now
sudo systemctl start ${SERVICE_NAME}
echo "✓ Started ${SERVICE_NAME}"

# Wait a moment for diagnostics to run
echo ""
echo "Running diagnostics (this takes ~5 seconds)..."
sleep 6

# Show status
echo ""
echo "Service Status:"
sudo systemctl status ${SERVICE_NAME} --no-pager -l

echo ""
echo "✅ Installation complete!"
echo ""
echo "LED Status Indicators:"
echo "  🟡 Blinking Yellow → Running diagnostics (on boot)"
echo "  🟢 Solid Green     → All systems OK"
echo "  🟡 Blinking Yellow → Minor issues detected"
echo "  🔴 Blinking Red    → Critical issues (WiFi, etc)"
echo "  🔴 Solid Red       → Temperature CRITICAL"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status ${SERVICE_NAME}   # Check status"
echo "  sudo systemctl restart ${SERVICE_NAME}  # Re-run diagnostics"
echo "  journalctl -u ${SERVICE_NAME} -f        # View logs"
echo "  cat logs/boot_diagnostics_*.log         # View diagnostic results"
