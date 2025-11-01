# Logs Directory

**ALL logs for the Skipper project are stored in this central directory.**

This includes:
- Application logs
- Temperature monitoring data
- Face tracking events
- Motor calibration results
- Sensor readings
- System diagnostics
- Error logs

## Using the Logging System

### Python Modules

Import the central logging configuration:

```python
from utils.logging_config import get_logger, get_data_log_path

# Get a logger for your module
logger = get_logger(__name__)
logger.info("Starting module")
logger.error("Error occurred")

# Get a path for data files (CSV, JSON, etc.)
log_file = get_data_log_path("temperature", extension="csv")
with open(log_file, 'w') as f:
    f.write("timestamp,value\n")
```

All logs will automatically be placed in the `logs/` directory.

## Log Files

### Application Logs

Files: `<module_name>.log`, `skipper.log`

Standard Python logging format:
```
2025-11-01 19:38:16 - module.name - INFO - Message here
```

### Temperature Monitor Logs

Files: `temperature_YYYYMMDD_HHMMSS.csv`

CSV format with columns:
- `timestamp` - ISO 8601 timestamp
- `ambient_temp_c` - SHT3x ambient temperature in Celsius
- `cpu_temp_c` - Raspberry Pi CPU temperature in Celsius
- `humidity_percent` - SHT3x relative humidity percentage
- `delta_temp_c` - Temperature difference (CPU - Ambient) in Celsius

Example:
```csv
timestamp,ambient_temp_c,cpu_temp_c,humidity_percent,delta_temp_c
2025-11-01T19:32:05.123456,31.10,46.85,41.78,15.75
2025-11-01T19:32:07.234567,31.20,46.30,41.42,15.10
```

## Log Management

Logs are automatically created with timestamps and are not automatically deleted.

### Clean Old Logs

```bash
# Remove logs older than 7 days
find logs/ -name "*.log" -mtime +7 -delete
find logs/ -name "*.csv" -mtime +7 -delete

# Remove specific log types
rm logs/temperature_*.csv
rm logs/skipper.log

# Archive logs
tar -czf logs_archive_$(date +%Y%m%d).tar.gz logs/*.log logs/*.csv
```

### Monitor Disk Usage

```bash
# Check logs directory size
du -sh logs/

# List largest log files
du -h logs/* | sort -h -r | head -10
```

## Future Log Types

As the project grows, all new logs will be placed here:

- **Face tracking events:** `face_tracking_YYYYMMDD_HHMMSS.log`
- **Motor calibration:** `calibration_YYYYMMDD_HHMMSS.csv`
- **Sensor readings:** `sensors_YYYYMMDD_HHMMSS.csv`
- **System diagnostics:** `diagnostics_YYYYMMDD_HHMMSS.log`
- **Error reports:** `errors_YYYYMMDD_HHMMSS.log`

## Best Practices

1. **Always use the central logging configuration** from `utils/logging_config.py`
2. **Use timestamped filenames** for data files to avoid overwriting
3. **Use CSV format** for numerical data (easier to analyze)
4. **Use .log format** for text logs
5. **Clean old logs regularly** to avoid filling disk space
6. **Document new log types** in this README
