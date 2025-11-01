"""
Alarm Manager - Load and manage alarm configurations
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any

class AlarmManager:
    """Manages alarm configurations and priorities"""
    
    def __init__(self, config_path=None):
        """
        Initialize alarm manager
        
        Args:
            config_path: Path to alarm config YAML file
        """
        if config_path is None:
            config_path = Path(__file__).parent / "alarm_config.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.led_patterns = self.config.get('led_patterns', {})
        self.alarms = self.config.get('alarms', {})
        self.diagnostics_config = self.config.get('diagnostics', {})
        self.gpio_config = self.config.get('gpio', {})
        self.boot_config = self.config.get('boot', {})
    
    def _load_config(self) -> Dict:
        """Load alarm configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading alarm config: {e}")
            return {}
    
    def get_enabled_alarms(self) -> Dict[str, Dict]:
        """Get all enabled alarms"""
        return {
            name: alarm 
            for name, alarm in self.alarms.items() 
            if alarm.get('enabled', True)
        }
    
    def get_alarm_by_check(self, check: str, condition: str) -> Dict:
        """
        Get alarm configuration for a specific check and condition
        
        Args:
            check: Diagnostic check name (e.g., 'wifi', 'temperature')
            condition: Condition status (e.g., 'ok', 'error', 'critical')
        
        Returns:
            Alarm configuration dict or None
        """
        for name, alarm in self.get_enabled_alarms().items():
            if alarm.get('check') == check and alarm.get('condition') == condition:
                return alarm
        return None
    
    def get_highest_priority_alarm(self, diagnostic_results: Dict) -> tuple:
        """
        Determine highest priority alarm based on diagnostic results
        
        Args:
            diagnostic_results: Dict of diagnostic check results
                Format: {'wifi': {'status': 'error', ...}, ...}
        
        Returns:
            Tuple of (alarm_name, alarm_config) or (None, None)
        """
        highest_priority = 0
        highest_alarm = None
        highest_name = None
        
        # Check each diagnostic result against alarm conditions
        for check_name, result in diagnostic_results.items():
            status = result.get('status', 'unknown')
            
            # Find matching alarm
            alarm = self.get_alarm_by_check(check_name, status)
            if alarm:
                priority = alarm.get('priority', 0)
                if priority > highest_priority:
                    highest_priority = priority
                    highest_alarm = alarm
                    highest_name = f"{check_name}_{status}"
        
        # If no specific alarm found, check for "all ok"
        if highest_alarm is None:
            all_ok = self.get_alarm_by_check('all', 'ok')
            if all_ok:
                highest_alarm = all_ok
                highest_name = 'all_ok'
        
        return highest_name, highest_alarm
    
    def get_led_pattern(self, alarm: Dict) -> Dict:
        """
        Extract LED pattern information from alarm config
        Resolves pattern reference to actual LED pattern configuration
        
        Returns:
            Dict with keys: pattern, color (RGB tuple), blink, blink_rate
        """
        # Get pattern name from alarm
        pattern_name = alarm.get('pattern', 'ok_solid')
        
        # Look up pattern definition
        pattern_def = self.led_patterns.get(pattern_name, {})
        
        # Return resolved pattern with defaults
        return {
            'pattern': pattern_name,
            'color': tuple(pattern_def.get('color', [0, 255, 0])),
            'blink': pattern_def.get('blink', False),
            'blink_rate': pattern_def.get('blink_rate', 0.5),
            'description': pattern_def.get('description', '')
        }
    
    def get_boot_pattern(self) -> Dict:
        """
        Get LED pattern for boot diagnostic phase
        
        Returns:
            Dict with LED pattern configuration
        """
        pattern_name = self.boot_config.get('diagnostic_pattern', 'diagnostic_blink')
        pattern_def = self.led_patterns.get(pattern_name, {})
        
        return {
            'pattern': pattern_name,
            'color': tuple(pattern_def.get('color', [255, 255, 0])),
            'blink': pattern_def.get('blink', True),
            'blink_rate': pattern_def.get('blink_rate', 0.3)
        }
    
    def get_diagnostic_config(self, check_name: str) -> Dict:
        """Get configuration for a specific diagnostic check"""
        return self.diagnostics_config.get(check_name, {})
    
    def is_diagnostic_enabled(self, check_name: str) -> bool:
        """Check if a diagnostic is enabled"""
        return self.get_diagnostic_config(check_name).get('enabled', True)
    
    def get_gpio_pins(self) -> Dict[str, int]:
        """Get GPIO pin configuration"""
        return self.gpio_config
    
    def get_boot_config(self) -> Dict:
        """Get boot behavior configuration"""
        return self.boot_config
    
    def get_temperature_thresholds(self) -> tuple:
        """Get temperature warning and critical thresholds"""
        temp_config = self.get_diagnostic_config('temperature')
        return (
            temp_config.get('warning_threshold', 70.0),
            temp_config.get('critical_threshold', 80.0)
        )
    
    def list_alarms_by_priority(self) -> List[tuple]:
        """
        Get list of all enabled alarms sorted by priority (highest first)
        
        Returns:
            List of (alarm_name, alarm_config) tuples
        """
        alarms = self.get_enabled_alarms()
        return sorted(
            alarms.items(),
            key=lambda x: x[1].get('priority', 0),
            reverse=True
        )
    
    def print_alarm_summary(self):
        """Print a summary of all configured alarms"""
        print("=" * 70)
        print("ALARM CONFIGURATION SUMMARY")
        print("=" * 70)
        print()
        
        print("LED Patterns:")
        for pattern_name, pattern_def in self.led_patterns.items():
            color = pattern_def.get('color', [0, 0, 0])
            blink = "Blinking" if pattern_def.get('blink') else "Solid"
            desc = pattern_def.get('description', '')
            print(f"  {pattern_name:20s} → {blink:8s} RGB{tuple(color)} - {desc}")
        print()
        
        print("GPIO Configuration:")
        for pin_name, pin_num in self.get_gpio_pins().items():
            print(f"  {pin_name.upper():6s}: GPIO {pin_num}")
        print()
        
        print("Alarms (by priority):")
        for name, alarm in self.list_alarms_by_priority():
            priority = alarm.get('priority', 0)
            pattern = alarm.get('pattern', 'unknown')
            message = alarm.get('message', '')
            critical = "CRITICAL" if alarm.get('critical') else "WARNING"
            print(f"  [{priority:3d}] {name:25s} → {pattern:20s} ({critical})")
            print(f"        {message}")
        print()
        
        print("Diagnostic Checks:")
        for check_name, config in self.diagnostics_config.items():
            enabled = "✓" if config.get('enabled', True) else "✗"
            print(f"  {enabled} {check_name}")
        print("=" * 70)

# Convenience function
def load_alarm_config(config_path: str = None) -> AlarmManager:
    """Load alarm configuration and return AlarmManager instance"""
    return AlarmManager(config_path)

if __name__ == "__main__":
    # Test the alarm manager
    manager = AlarmManager()
    manager.print_alarm_summary()
