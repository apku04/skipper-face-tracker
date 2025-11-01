# Systemd Services for Skipper

This directory contains systemd services for the Skipper robot system.

## Available Services

### 1. boot-diagnostics.service (RECOMMENDED)
**Purpose:** Run comprehensive boot diagnostics and display status via RGB LED.

**Features:**
- Checks WiFi connectivity
- Tests Klipper/Moonraker connection
- Verifies camera availability
- Checks speaker/microphone
- Monitors CPU temperature
- Displays status via RGB LED
- Saves diagnostic logs

**LED Status Indicators:**
- 🟡 **Blinking Yellow** → Running diagnostics (on boot)
- 🟢 **Solid Green** → All systems OK
- 🟡 **Blinking Yellow** → Minor issues detected (camera, audio, etc.)
- 🔴 **Blinking Red** → Critical issues (WiFi down, hardware failure)
- 🔴 **Solid Red** → Temperature CRITICAL (>80°C)

**Hardware:**
- RGB LED connected to GPIO 23 (Red), GPIO 22 (Green), GPIO 27 (Blue)

**Status:** Ready to install

---

### 2. boot-status-led.service (DEPRECATED)
**Purpose:** Simple yellow LED on boot indicator.

**Note:** Use `boot-diagnostics.service` instead for full diagnostic capabilities.

---

## Quick Install

### Boot Diagnostics Service (Recommended)

```bash
cd /home/pi/work/skipper/services
chmod +x install_boot_diagnostics.sh
./install_boot_diagnostics.sh
```

This will automatically replace the old boot-status-led service.

### Boot Status LED Service (Legacy)

```bash
cd /home/pi/work/skipper/services
chmod +x install_boot_led.sh
./install_boot_led.sh
```

---

## Using Boot Diagnostics

### Understanding LED Status

The boot diagnostics service runs checks on every boot and displays the highest priority issue via the RGB LED:

| LED Pattern | Meaning | Priority | Action Needed |
|------------|---------|----------|---------------|
| 🟡 Fast Blinking Yellow | Running diagnostics | - | Wait ~5 seconds |
| 🟢 Solid Green | All systems OK | Lowest | None - system healthy |
| 🟡 Slow Blinking Yellow | Minor issues | Medium | Check logs for warnings |
| 🟡 Blinking Yellow | Warnings detected | Medium-High | Check diagnostics log |
| 🔴 Blinking Red | Critical issues | High | WiFi down or hardware failure |
| 🔴 Solid Red | Temperature CRITICAL | Highest | Shutdown and cool system |

### Viewing Diagnostic Results

**Check the latest diagnostic log:**
```bash
cat logs/boot_diagnostics_*.log | tail -20
```

**View live service logs:**
```bash
journalctl -u boot-diagnostics.service -f
```

**View logs since last boot:**
```bash
journalctl -u boot-diagnostics.service -b
```

**Check current service status:**
```bash
sudo systemctl status boot-diagnostics.service
```

### Re-running Diagnostics

To re-run diagnostics without rebooting:

```bash
sudo systemctl restart boot-diagnostics.service
```

Watch the LED cycle through diagnostics and show the new status.

### Troubleshooting Issues

#### Yellow Blinking - Minor Issues

Common causes:
- Speaker not detected
- Microphone not detected  
- Camera not found
- Klipper not accessible

**Action:** Check the diagnostic log to see which component failed:
```bash
cat logs/boot_diagnostics_*.log
```

#### Red Blinking - Critical Issues

**WiFi Down:**
```bash
# Check WiFi status
nmcli device status

# Reconnect WiFi
nmcli device wifi rescan
nmcli device wifi connect "YOUR_SSID" password "YOUR_PASSWORD"
```

#### Red Solid - Temperature Critical

**Immediate action required:**
```bash
# Check temperature
vcgencmd measure_temp

# If above 80°C, shutdown immediately
sudo shutdown -h now
```

Check cooling:
- Is the fan working?
- Are vents blocked?
- Is the heatsink properly mounted?

### Customizing Diagnostic Checks

Edit the alarm configuration to enable/disable checks:

```bash
nano alarms/alarm_config.yaml
```

To disable a diagnostic (e.g., speaker check):
```yaml
diagnostics:
  speaker:
    enabled: false  # Changed from true
```

Then restart the service:
```bash
sudo systemctl restart boot-diagnostics.service
```

### Adding Custom Diagnostics

See `alarms/README.md` for detailed instructions on:
- Adding new diagnostic checks
- Creating new alarm patterns
- Adjusting priority levels
- Customizing LED patterns

---

## Manual Installation (Generic Process)

This process works for any systemd service:

### Step 1: Create Python Service Script
Create your service script (e.g., `my_service.py`):

```python
#!/usr/bin/env python3
import signal
import sys
import time

def cleanup(signum, frame):
    """Handle shutdown gracefully"""
    print("Shutting down...")
    # Your cleanup code here
    sys.exit(0)

def main():
    # Setup signal handlers
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    
    print("Service started")
    
    # Your service logic here
    try:
        while True:
            # Do work
            time.sleep(60)
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == "__main__":
    main()
```

**Key Requirements:**
- Handle SIGTERM and SIGINT signals for graceful shutdown
- Use infinite loop or blocking operation to keep service alive
- Clean up resources on exit
- Make executable: `chmod +x my_service.py`

### Step 2: Create Systemd Unit File
Create `my-service.service`:

```ini
[Unit]
Description=My Service Description
After=multi-user.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /home/pi/work/skipper/services/my_service.py
WorkingDirectory=/home/pi/work/skipper
Restart=on-failure
RestartSec=5s
TimeoutStopSec=10
KillMode=mixed
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
```

**Configuration Notes:**
- `After=multi-user.target` - Start after basic system is ready
- `User=root` - Required for GPIO access (use `pi` if GPIO not needed)
- `ExecStart` - Full path to Python and your script
- `Restart=on-failure` - Auto-restart if service crashes
- `KillSignal=SIGTERM` - Send SIGTERM for graceful shutdown

### Step 3: Install Service

```bash
# Copy service file to systemd directory
sudo cp services/my-service.service /etc/systemd/system/

# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable my-service.service

# Start service now (without reboot)
sudo systemctl start my-service.service

# Check status
sudo systemctl status my-service.service
```

### Step 4: Verify and Test

```bash
# View real-time logs
journalctl -u my-service.service -f

# Check if service is enabled
systemctl is-enabled my-service.service

# Check if service is running
systemctl is-active my-service.service

# Test restart
sudo systemctl restart my-service.service

# Test reboot behavior
sudo reboot
# After reboot, check:
sudo systemctl status my-service.service
```

---

## Service Management Commands

### Status and Logs
```bash
# Check service status
sudo systemctl status <service-name>

# View logs (last 50 lines)
journalctl -u <service-name> -n 50

# Follow logs in real-time
journalctl -u <service-name> -f

# View logs since last boot
journalctl -u <service-name> -b
```

### Start/Stop/Restart
```bash
# Start service
sudo systemctl start <service-name>

# Stop service
sudo systemctl stop <service-name>

# Restart service
sudo systemctl restart <service-name>

# Reload configuration
sudo systemctl reload <service-name>
```

### Enable/Disable Autostart
```bash
# Enable autostart on boot
sudo systemctl enable <service-name>

# Disable autostart
sudo systemctl disable <service-name>

# Check if enabled
systemctl is-enabled <service-name>
```

### Troubleshooting
```bash
# Reload systemd after editing service file
sudo systemctl daemon-reload

# Reset failed state
sudo systemctl reset-failed <service-name>

# Check for errors
systemctl --failed

# View full configuration
systemctl cat <service-name>

# Check service dependencies
systemctl list-dependencies <service-name>
```

---

## Common Issues and Solutions

### 1. Service Fails to Start
```bash
# Check detailed error
sudo systemctl status <service-name> -l

# Check logs
journalctl -u <service-name> -n 100

# Common causes:
# - Wrong file paths in ExecStart
# - Missing execute permission: chmod +x script.py
# - Python import errors: check PYTHONPATH
# - GPIO access denied: change User to root
```

### 2. Service Starts but Exits Immediately
- Service script must not exit immediately
- Add infinite loop or blocking operation
- Check for exceptions in logs
- Make sure signal handlers are set up

### 3. GPIO Permission Denied
```bash
# Solution 1: Run as root
User=root

# Solution 2: Add user to gpio group
sudo usermod -a -G gpio pi
# Then reboot or use User=pi in service
```

### 4. Service Won't Stop
```bash
# Check if SIGTERM handler is implemented
# Check TimeoutStopSec value
# Force kill if necessary:
sudo systemctl kill -s SIGKILL <service-name>
```

### 5. Service Doesn't Start on Boot
```bash
# Check if enabled
systemctl is-enabled <service-name>

# If not, enable it
sudo systemctl enable <service-name>

# Check dependencies
systemctl list-dependencies <service-name>
```

---

## Service Best Practices

### 1. Logging
- Use Python's `logging` module
- Log to stdout/stderr (captured by systemd)
- Set appropriate log levels

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Service started")
```

### 2. Error Handling
- Wrap main loop in try/except
- Log all exceptions
- Don't let service crash silently

```python
try:
    while True:
        # Work
        time.sleep(1)
except Exception as e:
    logger.error(f"Error: {e}")
    raise
```

### 3. Resource Cleanup
- Always clean up GPIO, file handles, network connections
- Use signal handlers
- Test cleanup with `sudo systemctl stop`

### 4. Dependencies
- Use `After=` to ensure required services start first
- Common dependencies:
  - `network-online.target` - Network is up
  - `multi-user.target` - Basic system ready
  - `graphical.target` - GUI ready

### 5. Testing
- Test start: `sudo systemctl start <service>`
- Test stop: `sudo systemctl stop <service>`
- Test restart: `sudo systemctl restart <service>`
- Test reboot: `sudo reboot`
- Monitor logs during tests

---

## Creating a New Service Checklist

- [ ] Create Python script with signal handlers
- [ ] Test script manually: `python3 script.py`
- [ ] Make script executable: `chmod +x script.py`
- [ ] Create `.service` file
- [ ] Set correct User (root for GPIO, pi otherwise)
- [ ] Set correct ExecStart path
- [ ] Copy to `/etc/systemd/system/`
- [ ] Run `sudo systemctl daemon-reload`
- [ ] Run `sudo systemctl enable <service>`
- [ ] Run `sudo systemctl start <service>`
- [ ] Check status: `sudo systemctl status <service>`
- [ ] Check logs: `journalctl -u <service> -f`
- [ ] Test reboot: `sudo reboot`
- [ ] Verify autostart after reboot

---

## Future Services to Implement

### Auto Fan Control
Monitor temperature and control fan based on thresholds.

**Files needed:**
- `services/auto_fan.py` - Temperature monitoring loop
- `services/auto-fan.service` - Systemd unit file

### Face Tracking Autostart
Start face tracking automatically on boot.

**Files needed:**
- `services/face_tracking.py` - Launch wrapper for vision module
- `services/face-tracking.service` - Systemd unit file

### Sensor Logging
Log sensor data (temperature, humidity, pressure) to files.

**Files needed:**
- `services/sensor_logger.py` - Periodic sensor reads
- `services/sensor-logger.service` - Systemd unit file

---

## References

- [Systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Systemd Unit File Format](https://www.freedesktop.org/software/systemd/man/systemd.unit.html)
- [Python Signal Handling](https://docs.python.org/3/library/signal.html)
- [RPi.GPIO Documentation](https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/)
