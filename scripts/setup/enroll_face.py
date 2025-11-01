#!/usr/bin/env python3
"""
Face Enrollment Tool
====================

Enroll a person by taking photos from the camera or loading from files.
Photos are processed and face embeddings are stored in the database.

Usage:
    # Enroll from image files
    python3 enroll_face.py --name "Alice" --images alice1.jpg alice2.jpg alice3.jpg
    
    # Enroll from live camera (interactive - press 's' to save, 'q' to quit)
    python3 enroll_face.py --name "Alice" --camera 0
    
    # List enrolled people
    python3 enroll_face.py --list
"""

import sys
import os
import argparse
import cv2

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from identity.person_manager import PersonManager


def enroll_from_images(pm: PersonManager, name: str, image_paths: list):
    """Enroll a person from image files"""
    print(f"\nEnrolling '{name}' from {len(image_paths)} image(s)...")
    
    success_count = 0
    for i, img_path in enumerate(image_paths, 1):
        if not os.path.exists(img_path):
            print(f"  [{i}/{len(image_paths)}] ❌ File not found: {img_path}")
            continue
        
        # Load image (OpenCV loads as BGR)
        img_bgr = cv2.imread(img_path)
        if img_bgr is None:
            print(f"  [{i}/{len(image_paths)}] ❌ Failed to load: {img_path}")
            continue
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # Add to database
        if pm.add_person_from_image(name, img_rgb):
            print(f"  [{i}/{len(image_paths)}] ✓ Added from: {img_path}")
            success_count += 1
        else:
            print(f"  [{i}/{len(image_paths)}] ❌ No face detected in: {img_path}")
    
    print(f"\n✓ Successfully enrolled {success_count}/{len(image_paths)} images for '{name}'")
    return success_count > 0


def enroll_from_camera(pm: PersonManager, name: str, camera_id: int = 0):
    """Enroll a person from live camera (interactive)"""
    print(f"\nEnrolling '{name}' from camera {camera_id}...")
    print("Controls:")
    print("  's' = Save current frame")
    print("  'q' = Quit")
    print("\nPosition your face at different angles and lighting conditions,")
    print("then press 's' to capture each one.\n")
    
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"❌ Failed to open camera {camera_id}")
        return False
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read frame")
            break
        
        # Convert BGR to RGB for display info
        display_frame = frame.copy()
        
        # Show instructions
        cv2.putText(display_frame, f"Enrolling: {name}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_frame, f"Saved: {saved_count} image(s)", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_frame, "Press 's' to save, 'q' to quit", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow('Face Enrollment', display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('s'):
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            if pm.add_person_from_image(name, frame_rgb):
                saved_count += 1
                print(f"  ✓ Saved image {saved_count}")
            else:
                print(f"  ❌ No face detected, try again")
        
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if saved_count > 0:
        print(f"\n✓ Successfully enrolled {saved_count} image(s) for '{name}'")
        return True
    else:
        print(f"\n❌ No images were enrolled for '{name}'")
        return False


def list_people(pm: PersonManager):
    """List all enrolled people"""
    if not hasattr(pm, '_data') or not pm._data:
        print("\n📋 No people enrolled yet")
        return
    
    print("\n📋 Enrolled people:")
    for name, embeddings in pm._data.items():
        print(f"  • {name}: {len(embeddings)} image(s)")


def main():
    parser = argparse.ArgumentParser(
        description='Enroll faces for recognition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--name', type=str, help='Name of the person to enroll')
    parser.add_argument('--images', nargs='+', help='Image file paths')
    parser.add_argument('--camera', type=int, help='Camera ID for live enrollment')
    parser.add_argument('--list', action='store_true', help='List enrolled people')
    parser.add_argument('--db', type=str, default='faces_db.pkl',
                       help='Database file path (default: faces_db.pkl)')
    
    args = parser.parse_args()
    
    # Initialize person manager
    pm = PersonManager(db_path=args.db)
    
    # List mode
    if args.list:
        list_people(pm)
        return
    
    # Enrollment mode - require name
    if not args.name:
        print("❌ Error: --name is required for enrollment")
        parser.print_help()
        sys.exit(1)
    
    # Enroll from images
    if args.images:
        enroll_from_images(pm, args.name, args.images)
    
    # Enroll from camera
    elif args.camera is not None:
        enroll_from_camera(pm, args.name, args.camera)
    
    else:
        print("❌ Error: Either --images or --camera is required")
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
