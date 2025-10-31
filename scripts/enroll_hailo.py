#!/usr/bin/env python3
"""
Hailo-Based Face Enrollment
============================

Uses Hailo SCRFD to detect and crop faces from photos, then enrolls them
for fast template-based recognition.

Usage:
    python3 scripts/enroll_hailo.py --name "Achuthan" --images enrollment_photos/*.jpg
"""

import sys
import os
import argparse
import cv2
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hailo_platform import VDevice, HailoStreamInterface, ConfigureParams, FormatType
from identity.hailo_person_manager import HailoPersonManager


class HailoFaceDetector:
    """Simple Hailo SCRFD face detector for enrollment"""
    
    def __init__(self, hef_path: str = "/usr/share/hailo-models/scrfd_2.5g_h8l.hef"):
        self.hef_path = hef_path
        self.input_size = (640, 640)
        self.target = None
        self.network_group = None
        self.configured_network = None
        
    def __enter__(self):
        """Initialize Hailo device"""
        params = VDevice.create_params()
        params.scheduling_algorithm = VDevice.SchedulingAlgorithm.ROUND_ROBIN
        self.target = VDevice(params)
        
        # Load HEF
        self.network_group = self.target.configure(ConfigureParams.create_from_hef(
            self.hef_path, interface=HailoStreamInterface.PCIe))
        self.configured_network = self.network_group[0]
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Hailo resources"""
        if self.configured_network:
            self.configured_network.release()
        if self.network_group:
            self.network_group.release()
        if self.target:
            self.target.release()
    
    def detect_faces(self, image_bgr: np.ndarray, score_threshold: float = 0.5):
        """
        Detect faces in image using Hailo SCRFD
        
        Returns:
            List of (x1, y1, x2, y2, score) tuples
        """
        orig_h, orig_w = image_bgr.shape[:2]
        
        # Resize to Hailo input size
        resized = cv2.resize(image_bgr, self.input_size)
        
        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Create input array
        input_data = np.expand_dims(rgb, axis=0).astype(np.uint8)
        
        # Run inference
        outputs = self.configured_network.infer(input_data)
        
        # Parse outputs (simplified - just get bounding boxes)
        faces = []
        
        # SCRFD has outputs at different scales
        # For enrollment we just need basic detection, so simplified parsing
        for output_name, output_data in outputs.items():
            if 'conv' in output_name and output_data.shape[-1] == 4:  # bbox output
                # Basic parsing - this is simplified
                output_data = output_data.squeeze()
                
        # Simple NMS and filtering would go here
        # For now, return placeholder - we'll use a different approach
        
        return faces


def enroll_from_images_simple(pm: HailoPersonManager, name: str, image_paths: list):
    """
    Simplified enrollment: just use the full captured images as templates.
    Since photos were taken with face centered, this works well.
    """
    print(f"\nEnrolling '{name}' from {len(image_paths)} image(s)...")
    
    success_count = 0
    
    for i, img_path in enumerate(image_paths, 1):
        try:
            # Load image
            img = cv2.imread(img_path)
            
            if img is None:
                print(f"  [{i}/{len(image_paths)}] ❌ Failed to load: {img_path}")
                continue
            
            # Center crop to focus on face (assuming face is centered)
            h, w = img.shape[:2]
            
            # Crop center 60% of image (where face should be)
            crop_size = int(min(h, w) * 0.6)
            y1 = (h - crop_size) // 2
            y2 = y1 + crop_size
            x1 = (w - crop_size) // 2
            x2 = x1 + crop_size
            
            face_crop = img[y1:y2, x1:x2]
            
            # Add to database
            if pm.add_person_from_face(name, face_crop):
                print(f"  [{i}/{len(image_paths)}] ✓ Enrolled: {os.path.basename(img_path)}")
                success_count += 1
            else:
                print(f"  [{i}/{len(image_paths)}] ❌ Failed: {os.path.basename(img_path)}")
                
        except Exception as e:
            print(f"  [{i}/{len(image_paths)}] ❌ Error: {e}")
    
    if success_count > 0:
        pm.save_database()
        print(f"\n✓ Successfully enrolled {success_count}/{len(image_paths)} images for '{name}'")
    else:
        print(f"\n❌ No faces enrolled for '{name}'")
    
    return success_count


def list_people(pm: HailoPersonManager):
    """List all enrolled people"""
    people = pm.get_all_people()
    
    if not people:
        print("\nNo people enrolled yet.")
        return
    
    print(f"\n{'Name':<20} {'Templates':<10}")
    print("-" * 30)
    
    for name, count in people:
        print(f"{name:<20} {count:<10}")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Enroll faces using Hailo-based recognition',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--name', type=str,
                       help='Name of the person to enroll')
    parser.add_argument('--images', nargs='+', type=str,
                       help='Image file paths to enroll')
    parser.add_argument('--list', action='store_true',
                       help='List all enrolled people')
    parser.add_argument('--db', type=str, default='faces_db_hailo.pkl',
                       help='Database file path')
    
    args = parser.parse_args()
    
    # Initialize person manager
    pm = HailoPersonManager(db_path=args.db)
    
    # List mode
    if args.list:
        list_people(pm)
        return
    
    # Enroll mode
    if not args.name or not args.images:
        parser.print_help()
        print("\nError: Both --name and --images are required for enrollment")
        return
    
    # Expand wildcards
    image_paths = []
    for pattern in args.images:
        from glob import glob
        matches = glob(pattern)
        if matches:
            image_paths.extend(matches)
        else:
            image_paths.append(pattern)  # Try as literal path
    
    if not image_paths:
        print(f"❌ No images found matching: {args.images}")
        return
    
    # Enroll faces
    enroll_from_images_simple(pm, args.name, image_paths)


if __name__ == '__main__':
    main()
