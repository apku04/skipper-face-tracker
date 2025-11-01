#!/usr/bin/env python3
"""
Skipper Face Tracker - Main Entry Point

Usage:
    python3 main.py                              # Run with default settings
    python3 main.py --mode tracking              # Face tracking mode
    python3 main.py --mode web                   # Web interface only
    python3 main.py --single-camera 0            # Single camera mode
    python3 main.py --cameras 0 1                # Dual camera mode
    python3 main.py --config config/custom.yaml  # Custom config
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def setup_logging(log_level="INFO", log_file=None):
    """Configure logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )


def main():
    parser = argparse.ArgumentParser(
        description='Skipper Face Tracker - AI-powered face tracking with Hailo + Klipper'
    )
    
    # Mode selection
    parser.add_argument(
        '--mode',
        choices=['tracking', 'web', 'sensors', 'calibrate'],
        default='tracking',
        help='Operation mode'
    )
    
    # Camera options
    parser.add_argument(
        '--cameras',
        type=int,
        nargs='+',
        default=[0, 1],
        help='Camera indices to use (default: 0 1 for dual camera)'
    )
    parser.add_argument(
        '--single-camera',
        type=int,
        metavar='INDEX',
        help='Use single camera mode (shorthand for --cameras INDEX)'
    )
    
    # Configuration
    parser.add_argument(
        '--config',
        type=str,
        default='config/default.yaml',
        help='Configuration file path'
    )
    
    # Web interface
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Web interface port (default: 5000)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Web interface host (default: 0.0.0.0)'
    )
    
    # Logging
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default='logs/skipper.log',
        help='Log file path'
    )
    
    # Features
    parser.add_argument(
        '--no-recognition',
        action='store_true',
        help='Disable face recognition'
    )
    parser.add_argument(
        '--no-following',
        action='store_true',
        help='Disable face following (motors)'
    )
    parser.add_argument(
        '--no-sensors',
        action='store_true',
        help='Disable environmental sensors'
    )
    
    args = parser.parse_args()
    
    # Handle single camera shorthand
    if args.single_camera is not None:
        args.cameras = [args.single_camera]
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger('skipper')
    
    logger.info("=" * 70)
    logger.info("Skipper Face Tracker v2.0.0")
    logger.info("=" * 70)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Cameras: {args.cameras}")
    logger.info(f"Config: {args.config}")
    
    try:
        if args.mode == 'tracking':
            logger.info("Starting face tracking mode...")
            # Import here to avoid loading unnecessary modules
            from vision.virtual_tracking_dual import main as tracking_main
            tracking_main()
            
        elif args.mode == 'web':
            logger.info(f"Starting web interface on {args.host}:{args.port}...")
            from web.app import create_app
            app = create_app()
            app.run(host=args.host, port=args.port, debug=False)
            
        elif args.mode == 'sensors':
            logger.info("Starting sensor monitoring mode...")
            from sensors.read_multiplexed_sensors import read_all_sensors
            read_all_sensors(continuous=True)
            
        elif args.mode == 'calibrate':
            logger.info("Starting motor calibration...")
            from motors.calibrate_motors import main as calibrate_main
            calibrate_main()
            
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
