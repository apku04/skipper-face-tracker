#!/usr/bin/env python3
"""
Stable Face Enrollment
=======================

Enroll faces using face_recognition (dlib-based, CPU, very stable).
No ONNX crashes, 100% reliable.

Usage:
    # Enroll from photos
    python3 scripts/setup/enroll_stable.py --name "Achuthan" --images enrollment_photos/Achuthan_*.jpg
    
    # List enrolled people
    python3 scripts/setup/enroll_stable.py --list
    
    # Remove someone
    python3 scripts/setup/enroll_stable.py --remove "OldName"
"""

import argparse
import sys
import glob
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from vision.identity.stable_person_manager import StablePersonManager


def main():
    parser = argparse.ArgumentParser(description="Enroll faces using stable face_recognition (dlib)")
    parser.add_argument('--name', type=str, help='Person name to enroll')
    parser.add_argument('--images', type=str, nargs='+', help='Image paths (supports wildcards)')
    parser.add_argument('--list', action='store_true', help='List all enrolled people')
    parser.add_argument('--remove', type=str, help='Remove a person from database')
    parser.add_argument('--threshold', type=float, default=0.6, 
                       help='Recognition threshold (0.5-0.7, default=0.6)')
    
    args = parser.parse_args()
    
    # Initialize manager
    print("=" * 60)
    print("Stable Face Enrollment (face_recognition / dlib)")
    print("=" * 60)
    manager = StablePersonManager()
    
    # List mode
    if args.list:
        people = manager.get_all_people()
        if not people:
            print("\n❌ No people enrolled yet")
        else:
            print(f"\n✓ Enrolled people ({len(people)}):")
            for name, count in people:
                print(f"  - {name}: {count} embeddings")
        return
    
    # Remove mode
    if args.remove:
        if manager.remove_person(args.remove):
            print(f"✓ Removed {args.remove}")
        else:
            print(f"❌ Person '{args.remove}' not found")
        return
    
    # Enroll mode
    if not args.name or not args.images:
        parser.print_help()
        print("\n❌ Error: Both --name and --images are required for enrollment")
        sys.exit(1)
    
    # Expand wildcards and collect all image paths
    image_paths = []
    for pattern in args.images:
        expanded = glob.glob(pattern)
        image_paths.extend(expanded)
    
    if not image_paths:
        print(f"❌ No images found matching: {args.images}")
        sys.exit(1)
    
    print(f"\nEnrolling '{args.name}' from {len(image_paths)} images...")
    print(f"Threshold: {args.threshold} (for testing)")
    print("-" * 60)
    
    # Enroll all images
    count = manager.add_person_from_images(args.name, image_paths)
    
    print("-" * 60)
    if count > 0:
        print(f"✅ SUCCESS: Enrolled {count}/{len(image_paths)} images for '{args.name}'")
        print(f"\nDatabase: {manager.db_path}")
        print(f"\nRecommendations:")
        print(f"  - {count} embeddings is {'good' if count >= 5 else 'minimal'}")
        print(f"  - For best accuracy, enroll 10-20 photos with varied:")
        print(f"    * Lighting (bright, dim, natural, artificial)")
        print(f"    * Angles (front, slight left/right, up/down)")
        print(f"    * Expressions (neutral, smile, serious)")
        print(f"    * Distances (close-up, medium distance)")
    else:
        print(f"❌ FAILED: Could not enroll any images")
        print(f"   Check that images contain clear, visible faces")


if __name__ == "__main__":
    main()
