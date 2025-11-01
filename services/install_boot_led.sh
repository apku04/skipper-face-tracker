#!/bin/bash
# Install boot status LED service

set -e

SERVICE_NAME="boot-status-led.service"
SERVICE_FILE="/home/pi/work/skipper/services/${SERVICE_NAME}"
SYSTEMD_PATH="/etc/systemd/system/${SERVICE_NAME}"

echo "Installing Boot Status LED Service..."
echo ""

# Make Python script executable
chmod +x /home/pi/work/skipper/services/boot_status_led.py
echo "✓ Made boot_status_led.py executable"

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

# Show status
echo ""
echo "Service Status:"
sudo systemctl status ${SERVICE_NAME} --no-pager -l

echo ""
echo "✅ Installation complete!"
echo ""
echo "Yellow LED should now be ON"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status ${SERVICE_NAME}   # Check status"
echo "  sudo systemctl stop ${SERVICE_NAME}     # Stop service"
echo "  sudo systemctl start ${SERVICE_NAME}    # Start service"
echo "  sudo systemctl restart ${SERVICE_NAME}  # Restart service"
echo "  sudo systemctl disable ${SERVICE_NAME}  # Disable autostart"
echo "  journalctl -u ${SERVICE_NAME} -f        # View logs"
