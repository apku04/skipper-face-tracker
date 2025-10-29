#!/usr/bin/env python3
"""
Pre-flight check utility for Klipper face tracking system.
Run this before starting face tracking to verify everything is configured correctly.
"""

import sys
import subprocess
import urllib.request
import json
import os
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_check(name, passed, message=""):
    status = f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"
    print(f"{status} {name:<45} {message}")
    return passed


def check_system_service(service_name):
    """Check if a systemd service is running."""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout.strip() == 'active'
    except Exception:
        return False


def check_klipper_api(url):
    """Check Klipper/Moonraker API connection."""
    try:
        with urllib.request.urlopen(f"{url}/printer/info", timeout=5) as response:
            data = json.loads(response.read().decode())
            state = data.get('result', {}).get('state', 'unknown')
            return True, state
    except Exception as e:
        return False, str(e)


def check_python_module(module_name):
    """Check if a Python module is installed."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def check_camera(device_path="/dev/video0"):
    """Check if camera device exists."""
    return Path(device_path).exists()


def check_file_exists(filepath):
    """Check if a file exists."""
    return Path(filepath).exists()


def main():
    print_header("KLIPPER FACE TRACKING - PRE-FLIGHT CHECK")
    
    all_passed = True
    warnings = []
    errors = []

    # 1. System Services
    print(f"\n{Colors.BOLD}[1/7] System Services{Colors.END}")
    
    klipper_ok = check_system_service('klipper')
    all_passed &= print_check(
        "Klipper service",
        klipper_ok,
        "running" if klipper_ok else "not running!"
    )
    if not klipper_ok:
        errors.append("Start with: sudo systemctl start klipper")
    
    moonraker_ok = check_system_service('moonraker')
    all_passed &= print_check(
        "Moonraker service",
        moonraker_ok,
        "running" if moonraker_ok else "not running!"
    )
    if not moonraker_ok:
        errors.append("Start with: sudo systemctl start moonraker")

    # 2. Klipper API Connection
    print(f"\n{Colors.BOLD}[2/7] Klipper API Connection{Colors.END}")
    
    klipper_url = os.getenv('KLIPPER_URL', 'http://localhost:7125')
    api_ok, state = check_klipper_api(klipper_url)
    
    all_passed &= print_check(
        f"Moonraker API at {klipper_url}",
        api_ok,
        f"state: {state}" if api_ok else f"failed: {state}"
    )
    
    if api_ok and state != 'ready':
        warnings.append(f"Klipper state is '{state}' (expected 'ready')")
        warnings.append("  You may need to initialize or home Klipper first")
    elif not api_ok:
        errors.append(f"Cannot connect to Moonraker at {klipper_url}")
        errors.append("  Check KLIPPER_URL environment variable")

    # 3. Python Dependencies
    print(f"\n{Colors.BOLD}[3/7] Python Dependencies{Colors.END}")
    
    deps = {
        'cv2': ('OpenCV', True),
        'flask': ('Flask', True),
        'numpy': ('NumPy', True),
        'mediapipe': ('MediaPipe', False),  # Optional
    }
    
    for module, (name, required) in deps.items():
        installed = check_python_module(module)
        if required:
            all_passed &= print_check(
                f"{name} ({module})",
                installed,
                "installed" if installed else "MISSING!"
            )
            if not installed:
                errors.append(f"Install with: pip3 install {module if module != 'cv2' else 'opencv-python'}")
        else:
            print_check(
                f"{name} ({module}) [optional]",
                installed,
                "installed" if installed else "not installed"
            )
            if not installed:
                warnings.append(f"{name} not installed (optional - disables behavior analysis)")

    # 4. Camera Device
    print(f"\n{Colors.BOLD}[4/7] Camera Device{Colors.END}")
    
    camera_ok = check_camera("/dev/video0")
    all_passed &= print_check(
        "Camera at /dev/video0",
        camera_ok,
        "found" if camera_ok else "not found!"
    )
    
    if not camera_ok:
        # Check for other video devices
        video_devices = list(Path('/dev').glob('video*'))
        if video_devices:
            warnings.append(f"Camera not at /dev/video0, but found: {', '.join(str(d) for d in video_devices)}")
            warnings.append("  Update CAP_INDEX in follow_face.py")
        else:
            errors.append("No camera devices found!")
            errors.append("  Check camera connection and drivers")

    # 5. Configuration Files
    print(f"\n{Colors.BOLD}[5/7] Configuration Files{Colors.END}")
    
    config_files = {
        'follow_face.py': True,
        'klipper_motors.py': True,
        'config.py': False,
    }
    
    for filename, required in config_files.items():
        exists = check_file_exists(filename)
        if required:
            all_passed &= print_check(
                filename,
                exists,
                "found" if exists else "MISSING!"
            )
            if not exists:
                errors.append(f"Missing required file: {filename}")
        else:
            print_check(
                f"{filename} [optional]",
                exists,
                "found" if exists else "not found"
            )

    # 6. Klipper Printer Config
    print(f"\n{Colors.BOLD}[6/7] Klipper Configuration{Colors.END}")
    
    printer_cfg = Path.home() / "printer_data/config/printer.cfg"
    cfg_exists = printer_cfg.exists()
    
    print_check(
        "printer.cfg",
        cfg_exists,
        f"found at {printer_cfg}" if cfg_exists else "not found!"
    )
    
    if not cfg_exists:
        warnings.append("No printer.cfg found!")
        warnings.append(f"  Copy example: cp printer.cfg.example {printer_cfg}")
        warnings.append("  Then edit with your board's pin configuration")

    # Check for stepper_x and stepper_y sections
    if cfg_exists:
        try:
            content = printer_cfg.read_text()
            has_stepper_x = '[stepper_x]' in content
            has_stepper_y = '[stepper_y]' in content
            
            print_check(
                "  [stepper_x] section",
                has_stepper_x,
                "configured" if has_stepper_x else "MISSING!"
            )
            print_check(
                "  [stepper_y] section",
                has_stepper_y,
                "configured" if has_stepper_y else "MISSING!"
            )
            
            if not (has_stepper_x and has_stepper_y):
                errors.append("printer.cfg missing required stepper sections!")
                errors.append("  See printer.cfg.example for reference")
        except Exception as e:
            warnings.append(f"Could not read printer.cfg: {e}")

    # 7. Environment Variables
    print(f"\n{Colors.BOLD}[7/7] Environment Variables{Colors.END}")
    
    env_vars = {
        'KLIPPER_URL': ('http://localhost:7125', False),
        'KLIPPER_ENABLED': ('true', False),
    }
    
    for var, (default, required) in env_vars.items():
        value = os.getenv(var)
        is_set = value is not None
        display_val = value if value else f"(default: {default})"
        
        print_check(
            var,
            is_set or not required,
            display_val
        )

    # Summary
    print_header("SUMMARY")
    
    if all_passed and not errors:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL CHECKS PASSED!{Colors.END}")
        print(f"\nYou can now run: {Colors.BOLD}python3 follow_face.py{Colors.END}")
        print(f"Or use the startup script: {Colors.BOLD}./start_face_tracking.sh{Colors.END}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ SOME CHECKS FAILED{Colors.END}")
        print(f"\n{Colors.RED}Errors that must be fixed:{Colors.END}")
        for error in errors:
            print(f"  • {error}")
    
    if warnings:
        print(f"\n{Colors.YELLOW}Warnings (may affect functionality):{Colors.END}")
        for warning in warnings:
            print(f"  • {warning}")
    
    print("\n" + "="*70 + "\n")
    
    if errors:
        print(f"{Colors.BOLD}Next steps:{Colors.END}")
        print("1. Fix the errors listed above")
        print("2. Re-run this check: python3 preflight_check.py")
        print("3. See KLIPPER_SETUP.md for detailed instructions")
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCheck interrupted by user.")
        sys.exit(130)
