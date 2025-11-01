"""
Alarms module for Skipper robot system

Provides alarm configuration management and LED status indicators
"""

from .alarm_manager import AlarmManager, load_alarm_config

__all__ = ['AlarmManager', 'load_alarm_config']
