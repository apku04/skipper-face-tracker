# Alarms System

This directory contains the alarm configuration and management system for Skipper.

## Overview

The alarm system manages diagnostic checks, LED status indicators, and priority-based alerts for the robot system.

## Files

- **`alarm_config.yaml`** - Main configuration file for all alarms and diagnostics
- **`alarm_manager.py`** - Python module to load and manage alarm configurations

## Alarm Configuration

### Structure

```yaml
alarms:
  alarm_name:
    priority: 100          # Higher = higher priority (0-100)
    check: "check_name"    # Which diagnostic to monitor
    condition: "error"     # Condition to match (ok, warning, error, critical)
    led_pattern: "red_solid"
    led_color: [255, 0, 0] # RGB values
    blink: true            # Solid or blinking
    blink_rate: 0.5        # Seconds per blink
    message: "Error message"
    critical: true         # Is this a critical alarm?
    enabled: true          # Enable/disable this alarm
```

### Priority Levels

- **90-100**: Critical alarms (temperature critical, WiFi down)
- **50-89**: Warning alarms (high temp, hardware issues)
- **1-49**: Info alarms (all OK)

### Current Alarms

1. **temperature_critical** (Priority 100)
   - Solid RED
   - CPU > 80°C
   
2. **wifi_down** (Priority 90)
   - Blinking RED
   - WiFi not connected
   
3. **temperature_warning** (Priority 80)
   - Blinking YELLOW
   - CPU 70-80°C
   
4. **klipper_down** (Priority 70)
   - Blinking YELLOW
   - Klipper not accessible
   
5. **camera_error** (Priority 60)
   - Blinking YELLOW
   - Camera not detected
   
6. **speaker_error** (Priority 55)
   - Blinking YELLOW
   - Speaker not detected
   
7. **microphone_error** (Priority 54)
   - Blinking YELLOW
   - Microphone not detected
   
8. **all_ok** (Priority 1)
   - Solid GREEN
   - All systems operational

## Usage

### Python

```python
from alarms.alarm_manager import AlarmManager

# Load alarm configuration
manager = AlarmManager()

# Check if diagnostic is enabled
if manager.is_diagnostic_enabled('wifi'):
    # Run WiFi check
    pass

# Get temperature thresholds
warning_temp, critical_temp = manager.get_temperature_thresholds()

# Determine highest priority alarm from diagnostic results
results = {
    'wifi': {'status': 'error', 'message': 'Not connected'},
    'temperature': {'status': 'ok', 'message': '45°C'},
}
alarm_name, alarm_config = manager.get_highest_priority_alarm(results)

# Get LED pattern for alarm
if alarm_config:
    led = manager.get_led_pattern(alarm_config)
    # led = {'pattern': 'red_blink', 'color': (255, 0, 0), 'blink': True, 'blink_rate': 0.5}
```

### Command Line

```bash
# View alarm configuration summary
python3 alarms/alarm_manager.py
```

## Adding New Alarms

1. Edit `alarm_config.yaml`
2. Add new alarm under `alarms:` section
3. Set appropriate priority (higher = more important)
4. Configure LED pattern and color
5. Add corresponding diagnostic check if needed

Example:

```yaml
alarms:
  disk_full:
    priority: 85
    check: "disk_space"
    condition: "critical"
    led_pattern: "red_blink"
    led_color: [255, 0, 0]
    blink: true
    blink_rate: 0.5
    message: "CRITICAL: Disk space low"
    critical: true
    enabled: true

diagnostics:
  disk_space:
    enabled: true
    critical_threshold: 90  # percent full
    warning_threshold: 80
```

## Configuration Sections

### `alarms`
Defines all alarm conditions and their LED patterns.

### `diagnostics`
Configuration for diagnostic checks (thresholds, timeouts, etc.).

### `gpio`
GPIO pin assignments for RGB LED.

### `boot`
Boot behavior configuration (blink rates, durations).

### `future_alarms`
Placeholder for future alarms (disabled by default).

## LED Patterns

- **Solid Color**: Steady light (e.g., solid green = all OK)
- **Blinking**: Flashing light (e.g., blinking red = critical error)
- **Colors**:
  - 🔴 RED: Critical issues
  - 🟡 YELLOW: Warnings
  - 🟢 GREEN: All OK

## Priority System

The system always displays the **highest priority** active alarm. For example:

- If WiFi is down (priority 90) AND camera error (priority 60)
- → Display: Blinking RED (WiFi down)

- If temperature is 75°C (priority 80) AND microphone error (priority 54)
- → Display: Blinking YELLOW (temperature warning)

## Maintenance

### Changing Priorities

Edit the `priority` value in `alarm_config.yaml`. Higher numbers = higher priority.

### Disabling Alarms

Set `enabled: false` in the alarm configuration.

### Changing LED Colors

Modify `led_color: [R, G, B]` values (0-255 for each channel).

### Adding Diagnostic Checks

1. Add configuration to `diagnostics:` section
2. Implement check function in boot diagnostics script
3. Add corresponding alarm in `alarms:` section

## Future Enhancements

Planned alarms (see `future_alarms` in config):
- Disk space monitoring
- Hailo AI accelerator check
- Face database validation
- Network bandwidth monitoring
- Motor calibration status
