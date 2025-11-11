#!/usr/bin/env python3
"""
Test Face Recognition - Debug Mode
===================================

Shows real-time recognition scores to help tune threshold.
"""

import cv2
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vision.identity.deep_person_manager import DeepPersonManager
from picamera2 import Picamera2

def main():
    print("=" * 60)
    print("Face Recognition Debug Test")
    print("=" * 60)
    
    # Initialize manager
    print("\nInitializing DeepPersonManager...")
    manager = DeepPersonManager()
    
    people = manager.get_all_people()
    print(f"Enrolled people: {people}")
    
    # Initialize camera
    print("\nInitializing camera...")
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()
    
    print("\n✓ Camera started")
    print("\nTesting recognition every 2 seconds...")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    import time
    
    try:
        while True:
            # Capture frame
            frame = picam2.capture_array()
            
            print("\n" + "=" * 60)
            print("Testing recognition...")
            
            # Test with different thresholds
            thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
            
            for threshold in thresholds:
                name, score = manager.identify_with_score(frame, threshold=threshold)
                
                if name:
                    print(f"  Threshold {threshold:.1f}: ✓ Recognized as '{name}' (score: {score:.3f})")
                else:
                    print(f"  Threshold {threshold:.1f}: ✗ Not recognized (score: {score:.3f})")
            
            print("=" * 60)
            
            # Wait 2 seconds before next test
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    picam2.stop()
    print("\nStopped")

if __name__ == "__main__":
    main()
