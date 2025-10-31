"""
Stereo Depth Calculator
=======================

Calculates 3D depth from dual camera face positions.
Handles camera calibration and triangulation.
"""

import numpy as np
from typing import Optional, Tuple


class StereoDepthCalculator:
    """Calculate depth using stereo triangulation"""
    
    def __init__(self, baseline_cm: float = 10.0, focal_length_px: float = 800.0):
        """
        Initialize stereo depth calculator
        
        Args:
            baseline_cm: Distance between camera centers in cm
            focal_length_px: Approximate focal length in pixels (calibrated from camera specs)
        """
        self.baseline_cm = baseline_cm
        self.focal_length_px = focal_length_px
        
        # Calibration offset (if cameras aren't perfectly aligned)
        self.vertical_offset_px = 0.0  # Y offset between cameras
        
        # Average human face width for sanity checking
        self.avg_face_width_cm = 15.0  # Average human face width
    
    def calibrate_from_known_distance(self, 
                                     face_width_px: float, 
                                     known_distance_cm: float):
        """
        Calibrate focal length from a known distance measurement
        
        Args:
            face_width_px: Detected face width in pixels
            known_distance_cm: Actual measured distance in cm
        """
        # focal_length = (object_width_px * distance) / real_width
        self.focal_length_px = (face_width_px * known_distance_cm) / self.avg_face_width_cm
        print(f"📐 Calibrated focal length: {self.focal_length_px:.1f} px")
    
    def calculate_depth(self, 
                       x1: float, y1: float, w1: float, h1: float,  # Camera 0 face box
                       x2: float, y2: float, w2: float, h2: float   # Camera 1 face box
                       ) -> Optional[Tuple[float, float, float]]:
        """
        Calculate 3D position (X, Y, Z) from dual camera face detections
        
        Args:
            x1, y1, w1, h1: Face bounding box from camera 0 (x, y, width, height)
            x2, y2, w2, h2: Face bounding box from camera 1 (x, y, width, height)
        
        Returns:
            (x_cm, y_cm, z_cm): 3D position relative to camera center
                x_cm: horizontal position (negative=left, positive=right)
                y_cm: vertical position (negative=up, positive=down)
                z_cm: depth/distance from cameras
            Returns None if calculation fails
        """
        # Calculate face centers
        center_x1 = x1 + w1 / 2
        center_y1 = y1 + h1 / 2
        center_x2 = x2 + w2 / 2
        center_y2 = y2 + h2 / 2
        
        # Calculate disparity (horizontal difference between face positions)
        # If cameras are side-by-side, closer objects appear more separated
        disparity = abs(center_x1 - center_x2)
        
        # Avoid division by zero
        if disparity < 1.0:
            return None
        
        # Calculate depth using triangulation
        # Z = (focal_length * baseline) / disparity
        z_cm = (self.focal_length_px * self.baseline_cm) / disparity
        
        # Sanity check: typical range for face tracking is 30-300 cm
        if z_cm < 20 or z_cm > 500:
            # Try alternative calculation using face size
            avg_face_width_px = (w1 + w2) / 2
            if avg_face_width_px > 10:
                z_cm = (self.avg_face_width_cm * self.focal_length_px) / avg_face_width_px
            else:
                return None
        
        # Calculate X position (horizontal, relative to center)
        # Average the X positions from both cameras
        avg_x_px = (center_x1 + center_x2) / 2
        # Convert to cm using similar triangles: x_cm / z_cm = x_px / focal_length
        x_cm = (avg_x_px * z_cm) / self.focal_length_px
        
        # Calculate Y position (vertical, relative to center)
        # Account for any vertical misalignment
        avg_y_px = ((center_y1 + center_y2) / 2) - self.vertical_offset_px
        y_cm = (avg_y_px * z_cm) / self.focal_length_px
        
        return (x_cm, y_cm, z_cm)
    
    def estimate_depth_from_face_size(self, face_width_px: float) -> float:
        """
        Estimate depth from single camera face size (fallback method)
        
        Args:
            face_width_px: Detected face width in pixels
        
        Returns:
            Estimated depth in cm
        """
        if face_width_px < 10:
            return 100.0  # Default guess
        
        # depth = (real_width * focal_length) / pixel_width
        depth_cm = (self.avg_face_width_cm * self.focal_length_px) / face_width_px
        
        return depth_cm
    
    def format_position(self, x_cm: float, y_cm: float, z_cm: float) -> str:
        """
        Format 3D position as readable string
        
        Returns:
            Formatted string like "50cm away, 5cm right, 2cm up"
        """
        # Distance (depth)
        dist_str = f"{z_cm:.0f}cm away"
        
        # Horizontal position
        if abs(x_cm) < 2:
            horiz_str = "centered"
        elif x_cm > 0:
            horiz_str = f"{abs(x_cm):.0f}cm right"
        else:
            horiz_str = f"{abs(x_cm):.0f}cm left"
        
        # Vertical position
        if abs(y_cm) < 2:
            vert_str = "level"
        elif y_cm > 0:
            vert_str = f"{abs(y_cm):.0f}cm down"
        else:
            vert_str = f"{abs(y_cm):.0f}cm up"
        
        return f"{dist_str}, {horiz_str}, {vert_str}"
    
    def get_distance_color(self, z_cm: float) -> Tuple[int, int, int]:
        """
        Get color based on distance (for visualization)
        
        Returns:
            (B, G, R) color tuple for OpenCV
        """
        if z_cm < 40:
            return (0, 0, 255)  # Red - too close
        elif z_cm < 80:
            return (0, 255, 0)  # Green - good distance
        elif z_cm < 150:
            return (0, 255, 255)  # Yellow - getting far
        else:
            return (255, 165, 0)  # Blue - far away
