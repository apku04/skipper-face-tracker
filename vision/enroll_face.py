#!/usr/bin/env python3
"""
Face Enrollment Script
======================
Captures your face and creates a face profile for recognition.
"""

import cv2
import face_recognition
import pickle
import numpy as np
from picamera2 import Picamera2
import time

def capture_face_samples(num_samples=10):
    """Capture multiple face samples from camera"""
    print("=" * 60)
    print("Face Enrollment - Capture Your Face")
    print("=" * 60)
    print(f"\nWe'll capture {num_samples} photos of your face.")
    print("Position yourself in front of the camera.")
    print("Press SPACE to capture each photo, or 'q' to quit.\n")
    
    # Initialize camera
    picam2 = Picamera2(0)  # Use camera 0
    config = picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()
    
    print("Camera started. Press SPACE to capture...")
    time.sleep(2)  # Let camera settle
    
    encodings = []
    samples_captured = 0
    
    try:
        while samples_captured < num_samples:
            # Capture frame
            frame = picam2.capture_array()
            
            # Convert to BGR for display
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Detect faces in current frame
            face_locations = face_recognition.face_locations(frame)
            
            # Draw rectangles around faces
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame_bgr, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Show status
            status = f"Captured: {samples_captured}/{num_samples} - Press SPACE to capture"
            cv2.putText(frame_bgr, status, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Display
            cv2.imshow('Face Enrollment', frame_bgr)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' '):  # Space bar
                if len(face_locations) == 0:
                    print("  ❌ No face detected! Try again.")
                elif len(face_locations) > 1:
                    print("  ❌ Multiple faces detected! Only one person at a time.")
                else:
                    # Extract encoding
                    encodings_list = face_recognition.face_encodings(frame, face_locations)
                    if encodings_list:
                        encodings.append(encodings_list[0])
                        samples_captured += 1
                        print(f"  ✓ Sample {samples_captured} captured!")
                    else:
                        print("  ❌ Could not extract face encoding. Try again.")
            
            elif key == ord('q'):
                print("\nEnrollment cancelled.")
                break
        
        if samples_captured == num_samples:
            print(f"\n✓ Successfully captured {num_samples} samples!")
            return encodings
        else:
            return None
            
    finally:
        picam2.stop()
        cv2.destroyAllWindows()


def save_face_profile(encodings, name="User"):
    """Save face encodings to file"""
    if not encodings:
        print("No encodings to save!")
        return False
    
    # Average the encodings for better accuracy
    avg_encoding = np.mean(encodings, axis=0)
    
    profile = {
        'name': name,
        'encoding': avg_encoding,
        'samples': len(encodings)
    }
    
    filename = 'face_profile.pkl'
    with open(filename, 'wb') as f:
        pickle.dump(profile, f)
    
    print(f"\n✓ Face profile saved to {filename}")
    print(f"  Name: {name}")
    print(f"  Samples: {len(encodings)}")
    return True


def main():
    print("\nFace Enrollment for Skipper Robot")
    print("=" * 60)
    
    name = input("\nEnter your name: ").strip()
    if not name:
        name = "User"
    
    print(f"\nEnrolling face for: {name}")
    
    # Capture face samples
    encodings = capture_face_samples(num_samples=10)
    
    if encodings:
        # Save profile
        if save_face_profile(encodings, name):
            print("\n✅ Enrollment complete!")
            print("You can now use face recognition in the tracker.")
        else:
            print("\n❌ Failed to save profile.")
    else:
        print("\n❌ Enrollment failed. Not enough samples captured.")


if __name__ == '__main__':
    main()
