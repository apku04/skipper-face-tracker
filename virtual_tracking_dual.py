#!/usr/bin/env python3
"""
Virtual Face Tracker with Dual Hailo Cameras
=============================================

Shows both cameras side-by-side with independent tracking overlays.
This demonstrates tracking logic WITHOUT moving motors.
Once this works, we'll connect to Klipper.

Each camera shows:
- Green box: Face detection boundary
- Red dot: Frame center (where we want face to be)
- Blue dot: Detected face center
- Circles: Deadband (inner) and damping (outer) zones
- Virtual motor angles: What the motors WOULD move to

"""

import cv2
import numpy as np
import time
import threading
from queue import Queue
from flask import Flask, Response, render_template_string
from picamera2 import Picamera2
from picamera2.devices import Hailo
from identity.hailo_person_manager import HailoPersonManager
from stereo_depth import StereoDepthCalculator

# === Configuration ===
CAMERA_WIDTH = 800
CAMERA_HEIGHT = 800  # Higher resolution for better quality, will resize for Hailo
CAMERA_FPS = 15  # Lower FPS for better quality

# Hailo expects 640x640
HAILO_WIDTH = 640
HAILO_HEIGHT = 640

# YuNet face detector model
YUNET_MODEL = "/usr/share/opencv4/face_detection_yunet_2023mar.onnx"

# Motor limits (degrees)
AZIMUTH_MIN = -13.0
AZIMUTH_MAX = 13.0
ALTITUDE_MIN = 4.0    # Inverted: positive = down
ALTITUDE_MAX = -4.0   # Inverted: negative = up

# Tracking parameters
PIXELS_PER_DEGREE = 50  # How many pixels = 1 degree
DEADBAND_RADIUS = 80    # Don't move within this radius
DAMPING_RADIUS = 160    # Progressive damping zone
BOX_MARGIN = 0.30       # 30% margin for box-based tracking


class SCRFDParser:
    """
    SCRFD face detection parser for Hailo output
    Implements proper post-processing with anchor generation and NMS
    """
    def __init__(self):
        self.input_size = (HAILO_WIDTH, HAILO_HEIGHT)
        self.score_threshold = 0.6  # Balanced threshold
        self.nms_threshold = 0.3  # Stricter NMS
        self.logged_output_info = False
        
        # SCRFD uses 3 feature pyramid scales with strides [8, 16, 32]
        self.fpn_strides = [8, 16, 32]
        self.num_anchors = 2  # 2 anchor points per location
    
    def _distance2bbox(self, points, distances, stride):
        """Convert distance predictions to bounding boxes"""
        x1 = points[:, 0] - distances[:, 0] * stride
        y1 = points[:, 1] - distances[:, 1] * stride
        x2 = points[:, 0] + distances[:, 2] * stride
        y2 = points[:, 1] + distances[:, 3] * stride
        return np.stack([x1, y1, x2, y2], axis=1)
    
    def _nms(self, boxes, scores):
        """Non-maximum suppression"""
        if len(boxes) == 0:
            return []
        
        x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            
            iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
            inds = np.where(iou <= self.nms_threshold)[0]
            order = order[inds + 1]
        
        return keep
    
    def parse(self, outputs):
        """Parse SCRFD outputs to face boxes"""
        # Log output structure once for debugging
        if outputs and not self.logged_output_info:
            print("\n=== Hailo SCRFD Output Structure ===")
            if isinstance(outputs, dict):
                for key, value in outputs.items():
                    if isinstance(value, np.ndarray):
                        print(f"  {key}: shape={value.shape}, dtype={value.dtype}")
            print("=====================================\n")
            self.logged_output_info = True
        
        if outputs is None or len(outputs) == 0:
            return []
        
        try:
            all_boxes = []
            all_scores = []
            
            # Parse each FPN level (stride 8, 16, 32)
            for stride_idx, stride in enumerate(self.fpn_strides):
                # Get feature map size for this stride
                feat_h = self.input_size[1] // stride
                feat_w = self.input_size[0] // stride
                
                # Get outputs for this stride
                if stride == 8:
                    bbox_pred = outputs['scrfd_2_5g/conv43']  # (80, 80, 8)
                    cls_score = outputs['scrfd_2_5g/conv42']  # (80, 80, 2)
                elif stride == 16:
                    bbox_pred = outputs['scrfd_2_5g/conv50']  # (40, 40, 8)
                    cls_score = outputs['scrfd_2_5g/conv49']  # (40, 40, 2)
                elif stride == 32:
                    bbox_pred = outputs['scrfd_2_5g/conv56']  # (20, 20, 8)
                    cls_score = outputs['scrfd_2_5g/conv55']  # (20, 20, 2)
                
                # Reshape: (H, W, C) -> (H*W*num_anchors, C/num_anchors)
                bbox_pred = bbox_pred.reshape(feat_h, feat_w, self.num_anchors, 4)
                cls_score = cls_score.reshape(feat_h, feat_w, self.num_anchors, 1)
                
                # Apply sigmoid to get probabilities
                scores = 1.0 / (1.0 + np.exp(-cls_score))
                scores = scores.reshape(-1)
                bbox_pred = bbox_pred.reshape(-1, 4)
                
                # Filter by score threshold
                valid_idx = scores > self.score_threshold
                if not np.any(valid_idx):
                    continue
                
                valid_scores = scores[valid_idx]
                valid_bboxes = bbox_pred[valid_idx]
                
                # Generate anchor points for valid detections
                anchor_centers = []
                valid_positions = np.where(valid_idx)[0]
                for pos in valid_positions:
                    anchor_idx = pos % self.num_anchors
                    grid_idx = pos // self.num_anchors
                    y = grid_idx // feat_w
                    x = grid_idx % feat_w
                    
                    cx = (x + 0.5) * stride
                    cy = (y + 0.5) * stride
                    anchor_centers.append([cx, cy])
                
                anchor_centers = np.array(anchor_centers, dtype=np.float32)
                
                # Decode bboxes from anchor deltas
                boxes = self._distance2bbox(anchor_centers, valid_bboxes, stride)
                
                all_boxes.append(boxes)
                all_scores.append(valid_scores)
            
            if len(all_boxes) == 0:
                return []
            
            # Concatenate all detections
            all_boxes = np.concatenate(all_boxes, axis=0)
            all_scores = np.concatenate(all_scores, axis=0)
            
            # Log detection info once
            if not hasattr(self, 'logged_detection_count'):
                print(f"SCRFD: Found {len(all_boxes)} raw detections before NMS (scores: {all_scores.min():.3f}-{all_scores.max():.3f})")
                self.logged_detection_count = True
            
            # Apply NMS
            keep = self._nms(all_boxes, all_scores)
            
            # Sort by score and keep only top 5 detections
            if len(keep) > 5:
                keep_scores = all_scores[keep]
                top_indices = np.argsort(keep_scores)[::-1][:5]
                keep = [keep[i] for i in top_indices]
            
            # Convert to (x, y, w, h) format and scale to camera resolution
            faces = []
            for idx in keep:
                x1, y1, x2, y2 = all_boxes[idx]
                score = all_scores[idx]
                
                # Scale from Hailo input size to camera resolution
                scale_x = CAMERA_WIDTH / HAILO_WIDTH
                scale_y = CAMERA_HEIGHT / HAILO_HEIGHT
                
                x = int(x1 * scale_x)
                y = int(y1 * scale_y)
                w = int((x2 - x1) * scale_x)
                h = int((y2 - y1) * scale_y)
                
                # Stricter sanity check with aspect ratio
                aspect_ratio = w / h if h > 0 else 0
                if (w >= 60 and h >= 60 and 
                    w <= 400 and h <= 400 and
                    0.6 <= aspect_ratio <= 1.5 and  # Faces should be roughly square
                    score > 0.65):  # Extra score filter
                    faces.append((x, y, w, h))
            
            return faces
            
        except Exception as e:
            # If parsing fails, return empty (will fall back to YuNet)
            import traceback
            if not hasattr(self, 'logged_parse_error'):
                print(f"SCRFD parse error: {e}")
                print(traceback.format_exc())
                self.logged_parse_error = True
            return []


class VirtualTracker:
    """
    Calculates what motor angles would be WITHOUT actually moving
    Uses same box-based tracking logic as the real system
    Also includes temporal smoothing to stabilize detections
    """
    
    def __init__(self, frame_width=CAMERA_WIDTH, frame_height=CAMERA_HEIGHT):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frame_center_x = frame_width // 2
        self.frame_center_y = frame_height // 2
        
        # Virtual motor positions (degrees)
        self.current_az = 0.0
        self.current_alt = 0.0
        
        # Temporal smoothing for stable tracking
        self.last_face_box = None
        self.frames_without_detection = 0
        self.max_frames_without_detection = 15  # Increased: Keep last box for 15 frames (~0.5s)
        self.box_smoothing = 0.4  # EMA smoothing factor (0.4 = more responsive, 0.2 = smoother)
        self.lost_track_frames = 0  # How many frames since we lost IoU match
        self.max_lost_track_frames = 20  # After this, accept any new face as reacquisition
        
    def _smooth_box(self, new_box, old_box):
        """Smooth face box using exponential moving average"""
        if old_box is None:
            return new_box
        
        x1, y1, w1, h1 = new_box
        x2, y2, w2, h2 = old_box
        
        alpha = self.box_smoothing
        x = int(alpha * x1 + (1 - alpha) * x2)
        y = int(alpha * y1 + (1 - alpha) * y2)
        w = int(alpha * w1 + (1 - alpha) * w2)
        h = int(alpha * h1 + (1 - alpha) * h2)
        
        return (x, y, w, h)
    
    def _iou(self, box1, box2):
        """Calculate Intersection over Union between two boxes"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Get box coordinates
        b1_x1, b1_y1, b1_x2, b1_y2 = x1, y1, x1 + w1, y1 + h1
        b2_x1, b2_y1, b2_x2, b2_y2 = x2, y2, x2 + w2, y2 + h2
        
        # Intersection area
        inter_x1 = max(b1_x1, b2_x1)
        inter_y1 = max(b1_y1, b2_y1)
        inter_x2 = min(b1_x2, b2_x2)
        inter_y2 = min(b1_y2, b2_y2)
        
        if inter_x2 < inter_x1 or inter_y2 < inter_y1:
            return 0.0
        
        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        
        # Union area
        b1_area = w1 * h1
        b2_area = w2 * h2
        union_area = b1_area + b2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def _box_distance(self, box1, box2):
        """Calculate center-to-center distance between two boxes"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Box centers
        c1_x = x1 + w1 / 2
        c1_y = y1 + h1 / 2
        c2_x = x2 + w2 / 2
        c2_y = y2 + h2 / 2
        
        # Euclidean distance
        dist = np.sqrt((c1_x - c2_x)**2 + (c1_y - c2_y)**2)
        return dist
        
    def update(self, face_box):
        """
        Update virtual motor positions based on face detection
        Uses temporal smoothing to keep boxes steady
        
        Args:
            face_box: (x, y, w, h) or None
            
        Returns:
            dict with tracking info
        """
        if face_box is None:
            self.frames_without_detection += 1
            self.lost_track_frames += 1
            
            # Use last known box for a few frames
            if self.last_face_box and self.frames_without_detection <= self.max_frames_without_detection:
                face_box = self.last_face_box
            else:
                self.last_face_box = None
                return {
                    'has_target': False,
                    'azimuth': self.current_az,
                    'altitude': self.current_alt,
                    'in_deadband': True
                }
        else:
            # Check if this detection matches our tracked face
            if self.last_face_box:
                iou = self._iou(face_box, self.last_face_box)
                distance = self._box_distance(face_box, self.last_face_box)
                
                # If we've lost track for a while, be more lenient about reacquisition
                if self.lost_track_frames > self.max_lost_track_frames:
                    # Accept any reasonable face as reacquisition
                    self.lost_track_frames = 0
                    face_box = self._smooth_box(face_box, self.last_face_box)
                elif iou < 0.2 and distance > 200:
                    # Face moved too far, might be false positive OR you moved a lot
                    # If we had good tracking recently, trust it's you
                    if self.lost_track_frames < 10:
                        # Gradually transition to new position
                        face_box = self._smooth_box(face_box, self.last_face_box)
                        self.lost_track_frames += 1
                    else:
                        # Been losing track, accept new detection
                        self.lost_track_frames = 0
                else:
                    # Good match, smooth the box position
                    face_box = self._smooth_box(face_box, self.last_face_box)
                    self.lost_track_frames = 0  # Reset lost track counter
            
            self.last_face_box = face_box
            self.frames_without_detection = 0
        
        x, y, w, h = face_box
        
        # Face center
        face_center_x = x + w // 2
        face_center_y = y + h // 2
        
        # Create inner box (shrink face box by margin)
        margin_x = int(w * BOX_MARGIN)
        margin_y = int(h * BOX_MARGIN)
        inner_x1 = x + margin_x
        inner_y1 = y + margin_y
        inner_x2 = x + w - margin_x
        inner_y2 = y + h - margin_y
        
        # Check if frame center is outside inner box
        if (self.frame_center_x < inner_x1 or self.frame_center_x > inner_x2 or
            self.frame_center_y < inner_y1 or self.frame_center_y > inner_y2):
            # Center is outside box - need to move
            error_x = face_center_x - self.frame_center_x
            error_y = face_center_y - self.frame_center_y
        else:
            # Center is inside box - stay still
            error_x = 0
            error_y = 0
        
        # Calculate distance from center for damping
        distance = np.sqrt(error_x**2 + error_y**2)
        
        # Check zones
        in_deadband = distance < DEADBAND_RADIUS
        in_damping = DEADBAND_RADIUS <= distance < DAMPING_RADIUS
        
        # Calculate delta angles
        if in_deadband:
            delta_az = 0
            delta_alt = 0
        elif in_damping:
            # Progressive damping: 100% at deadband edge, 0% at damping edge
            damping_factor = 1.0 - (distance - DEADBAND_RADIUS) / (DAMPING_RADIUS - DEADBAND_RADIUS)
            delta_az = (error_x / PIXELS_PER_DEGREE) * damping_factor
            delta_alt = (error_y / PIXELS_PER_DEGREE) * damping_factor
        else:
            # Full speed tracking
            delta_az = error_x / PIXELS_PER_DEGREE
            delta_alt = error_y / PIXELS_PER_DEGREE
        
        # Update virtual position
        self.current_az = np.clip(self.current_az + delta_az, AZIMUTH_MIN, AZIMUTH_MAX)
        self.current_alt = np.clip(self.current_alt + delta_alt, ALTITUDE_MIN, ALTITUDE_MAX)
        
        return {
            'has_target': True,
            'face_center': (face_center_x, face_center_y),
            'inner_box': (inner_x1, inner_y1, inner_x2, inner_y2),
            'azimuth': self.current_az,
            'altitude': self.current_alt,
            'error_x': error_x,
            'error_y': error_y,
            'in_deadband': in_deadband,
            'in_damping': in_damping
        }


class DualCameraTracker:
    """Main application with dual cameras"""
    
    def __init__(self, camera_nums=[0, 1]):
        self.camera_nums = camera_nums
        self.hailo_model = "/usr/share/hailo-models/scrfd_2.5g_h8l.hef"
        
        # SHARED Hailo device (only one instance allowed)
        self.hailo = None
        self.hailo_lock = threading.Lock()  # For thread-safe Hailo access
        
        # One camera, parser, and tracker per camera
        self.picam2_list = []
        self.parser_list = []
        self.tracker_list = []
        
        for _ in camera_nums:
            self.picam2_list.append(None)
            self.parser_list.append(SCRFDParser())
            self.tracker_list.append(VirtualTracker())
        
        # Stereo depth calculator
        self.depth_calculator = StereoDepthCalculator(
            baseline_cm=10.0,  # Approximate distance between cameras (adjust if needed)
            focal_length_px=800.0  # Initial estimate, will auto-calibrate
        )
        self.last_depth = None  # Store last calculated depth
        
        # Face recognition manager (Hailo-based template matching)
        self.person_manager = HailoPersonManager(db_path="faces_db_hailo.pkl")
        self.recognition_interval = 15  # run recognition every N frames
        self.last_recognition = [None for _ in camera_nums]
        self.last_recognition_time = [0.0 for _ in camera_nums]
        
        # YuNet face detector (much better than Haar cascade!)
        try:
            self.face_detector = cv2.FaceDetectorYN.create(
                YUNET_MODEL,
                "",
                (CAMERA_WIDTH, CAMERA_HEIGHT),
                score_threshold=0.9,  # Very high threshold to reduce false positives
                nms_threshold=0.3,
                top_k=1  # Only keep best detection
            )
            print("✓ YuNet face detector loaded (score_threshold=0.9)")
        except Exception as e:
            print(f"⚠ YuNet failed ({e}), falling back to Haar cascade")
            self.face_detector = None
        
        self.running = False
        self.latest_frames = [None, None]
        self.fps_list = [0.0, 0.0]
        
    def start(self):
        """Start cameras and Hailo"""
        print(f"Initializing Cameras {self.camera_nums}...")
        
        # Initialize shared Hailo device FIRST (before threads)
        print("Initializing shared Hailo device...")
        self.hailo = Hailo(self.hailo_model)
        print("✓ Hailo initialized (shared between cameras)")
        
        self.running = True
        
        # Start processing threads (one per camera)
        self.threads = []
        for i in range(len(self.camera_nums)):
            thread = threading.Thread(target=self._process_loop, args=(i,), daemon=True)
            thread.start()
            self.threads.append(thread)
        
        # Wait a moment for threads to initialize
        time.sleep(2)
        
        print("\n✓ Dual camera virtual tracking started")
        print("  View at: http://localhost:5000")
        print("  Press Ctrl+C to stop\n")
        
    def stop(self):
        """Stop everything"""
        self.running = False
        
        for picam2 in self.picam2_list:
            if picam2:
                try:
                    picam2.stop()
                    picam2.close()
                except:
                    pass
        
        if self.hailo:
            try:
                self.hailo.close()
            except:
                pass
        
        print("Stopped")
        
    def _process_loop(self, camera_idx):
        """Main processing loop for one camera"""
        cam_num = self.camera_nums[camera_idx]
        
        try:
            # Initialize camera (Hailo is already initialized in main thread)
            print(f"Camera {cam_num}: Initializing camera...")
            picam2 = Picamera2(cam_num)
            
            # Configure for better quality
            config = picam2.create_preview_configuration(
                main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"},
                controls={
                    "FrameDurationLimits": (33333, 66666),  # 15-30 FPS range
                    "NoiseReductionMode": 2,  # High quality noise reduction
                }
            )
            picam2.configure(config)
            picam2.start()
            self.picam2_list[camera_idx] = picam2
            print(f"Camera {cam_num}: ✓ Started at {CAMERA_WIDTH}x{CAMERA_HEIGHT} with quality settings")
            
        except Exception as e:
            print(f"Camera {cam_num}: ❌ Initialization failed - {e}")
            return
        
        frame_count = 0
        fps_start = time.time()
        
        parser = self.parser_list[camera_idx]
        tracker = self.tracker_list[camera_idx]
        
        while self.running:
            try:
                # Capture frame
                frame = picam2.capture_array()
                
                if frame is None or frame.size == 0:
                    print(f"Camera {cam_num}: Empty frame!")
                    continue
                
                # Resize frame for Hailo (640x640) while keeping original for display
                frame_hailo = cv2.resize(frame, (HAILO_WIDTH, HAILO_HEIGHT))
                
                # Run Hailo inference (with lock for thread safety)
                try:
                    with self.hailo_lock:
                        outputs = self.hailo.run(frame_hailo)
                except Exception as hailo_err:
                    print(f"Camera {cam_num}: Hailo error - {hailo_err}")
                    outputs = None
                
                # Parse detections (returns empty for now)
                faces = []
                if outputs:
                    faces = parser.parse(outputs)
                    if faces and frame_count % 60 == 0:
                        print(f"Camera {cam_num}: ✓ Hailo SCRFD detected {len(faces)} face(s)")
                
                # Fallback to YuNet if no Hailo detections
                if not faces and self.face_detector:
                    try:
                        # YuNet expects BGR format
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        _, yunet_faces = self.face_detector.detect(frame_bgr)
                        
                        if yunet_faces is not None and len(yunet_faces) > 0:
                            # Convert YuNet format to (x, y, w, h) and filter by size/confidence
                            faces = []
                            for det in yunet_faces:
                                x, y, w, h = int(det[0]), int(det[1]), int(det[2]), int(det[3])
                                confidence = det[14] if len(det) > 14 else 1.0
                                
                                # Very strict filter:
                                # - Must be reasonable size (80-350px for 800x800 frame)
                                # - High confidence (>0.9 due to score_threshold=0.9)
                                # - Reasonable aspect ratio (face should be roughly square)
                                aspect_ratio = w / h if h > 0 else 0
                                if (w >= 80 and h >= 80 and 
                                    w <= 350 and h <= 350 and 
                                    confidence > 0.85 and
                                    0.7 <= aspect_ratio <= 1.4):  # Face should be roughly square
                                    faces.append((x, y, w, h))
                            
                            if frame_count % 60 == 0:  # Log every 60 frames (2 seconds)
                                if len(faces) > 0:
                                    print(f"Camera {cam_num}: YuNet → {len(faces)} face(s) (conf>0.85)")
                                elif yunet_faces is not None and len(yunet_faces) > 0:
                                    print(f"Camera {cam_num}: YuNet detected faces but filtered out (low quality)")
                    except Exception as cv_err:
                        if frame_count % 30 == 0:
                            print(f"Camera {cam_num}: YuNet error - {cv_err}")
                        faces = []
                
                # Smart face selection with temporal tracking
                face_box = None
                if len(faces) > 0:
                    # If we're already tracking a face, find the best match
                    if tracker.last_face_box:
                        best_match = None
                        best_score = 0
                        
                        for face in faces:
                            iou = tracker._iou(face, tracker.last_face_box)
                            distance = tracker._box_distance(face, tracker.last_face_box)
                            
                            # Scoring: prefer high IoU, but also consider distance
                            # If tracker is lost, distance matters more
                            if tracker.lost_track_frames > 5:
                                # Lost track, prefer closest face
                                score = iou * 0.3 + (1.0 / (1.0 + distance / 100)) * 0.7
                            else:
                                # Good track, prefer IoU overlap
                                score = iou * 0.7 + (1.0 / (1.0 + distance / 100)) * 0.3
                            
                            if score > best_score and score > 0.2:  # Minimum threshold
                                best_score = score
                                best_match = face
                        
                        if best_match:
                            face_box = best_match
                        else:
                            # No good match by IoU/distance, pick largest face
                            faces_list = list(faces)
                            faces_list.sort(key=lambda f: f[2] * f[3], reverse=True)
                            face_box = faces_list[0]
                    else:
                        # No existing track, pick largest face (most likely to be real)
                        faces_list = list(faces)
                        faces_list.sort(key=lambda f: f[2] * f[3], reverse=True)
                        face_box = faces_list[0]
                
                # Update tracker (applies smoothing)
                tracking_info = tracker.update(face_box)

                # Periodic face recognition (CPU) to identify person
                name = None
                try:
                    if face_box is not None and frame_count % self.recognition_interval == 0:
                        x, y, w, h = face_box
                        # clamp
                        x = max(0, x); y = max(0, y)
                        face_crop = frame[y:y+h, x:x+w]
                        if face_crop.size != 0:
                            # frame is RGB already
                            identified = self.person_manager.identify(face_crop)
                            if identified:
                                name = identified
                                self.last_recognition[camera_idx] = name
                                self.last_recognition_time[camera_idx] = time.time()
                            else:
                                # keep previous if still recent
                                if time.time() - self.last_recognition_time[camera_idx] < 5.0:
                                    name = self.last_recognition[camera_idx]
                                else:
                                    name = None
                    else:
                        # use cached name if recent
                        if time.time() - self.last_recognition_time[camera_idx] < 5.0:
                            name = self.last_recognition[camera_idx]
                except Exception:
                    name = None

                # Draw visualization
                vis_frame = self._draw_visualization(frame.copy(), tracking_info)

                # Overlay identity if available
                if name and tracking_info.get('inner_box'):
                    try:
                        x1, y1, x2, y2 = tracking_info['inner_box']
                        label = name
                        cv2.putText(vis_frame, label, (x1, max(y1-10, 20)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                    except Exception:
                        pass
                
                # Store latest frame
                self.latest_frames[camera_idx] = vis_frame
                
                # Update FPS
                frame_count += 1
                if frame_count % 10 == 0:
                    elapsed = time.time() - fps_start
                    self.fps_list[camera_idx] = frame_count / elapsed
                    
            except Exception as e:
                import traceback
                print(f"Camera {cam_num} error: {e}")
                print(traceback.format_exc())
                time.sleep(0.1)
    
    def _calculate_stereo_depth(self):
        """Calculate 3D depth from both camera face positions"""
        try:
            # Get face boxes from both trackers
            tracker0 = self.tracker_list[0]
            tracker1 = self.tracker_list[1]
            
            # Need valid faces from both cameras
            if not tracker0.last_face_box or not tracker1.last_face_box:
                return None
            
            # Extract bounding boxes (x, y, w, h format)
            x1, y1, x2, y2 = tracker0.last_face_box
            w1 = x2 - x1
            h1 = y2 - y1
            
            x1_cam1, y1_cam1, x2_cam1, y2_cam1 = tracker1.last_face_box
            w2 = x2_cam1 - x1_cam1
            h2 = y2_cam1 - y1_cam1
            
            # Calculate depth
            depth_result = self.depth_calculator.calculate_depth(
                x1, y1, w1, h1,  # Camera 0
                x1_cam1, y1_cam1, w2, h2  # Camera 1
            )
            
            if depth_result:
                self.last_depth = depth_result
                return depth_result
            
        except Exception as e:
            pass
        
        return None
    
    def _draw_visualization(self, frame, tracking_info):
        """Draw all tracking visualization on frame"""
        h, w = frame.shape[:2]
        center_x = w // 2
        center_y = h // 2
        
        # Draw deadband circle (light gray)
        cv2.circle(frame, (center_x, center_y), DEADBAND_RADIUS, (200, 200, 200), 2)
        
        # Draw damping circle (darker gray)
        cv2.circle(frame, (center_x, center_y), DAMPING_RADIUS, (128, 128, 128), 2)
        
        # Draw center crosshair (red) - RGB format
        cv2.drawMarker(frame, (center_x, center_y), (255, 0, 0), 
                      cv2.MARKER_CROSS, 20, 2)
        
        if tracking_info['has_target']:
            # Draw face box (green for detected) - RGB format
            if 'inner_box' in tracking_info:
                x1, y1, x2, y2 = tracking_info['inner_box']
                # Expand to show original face box
                margin_x = int((x2 - x1) * BOX_MARGIN / (1 - 2*BOX_MARGIN))
                margin_y = int((y2 - y1) * BOX_MARGIN / (1 - 2*BOX_MARGIN))
                cv2.rectangle(frame, (x1-margin_x, y1-margin_y), (x2+margin_x, y2+margin_y), 
                            (0, 255, 0), 2)
                # Draw inner box (lighter green)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (100, 255, 100), 1)
            
            # Draw face center (blue) - RGB format
            if 'face_center' in tracking_info:
                fx, fy = tracking_info['face_center']
                cv2.circle(frame, (fx, fy), 8, (0, 0, 255), -1)
            
            # Zone indicator
            if tracking_info.get('in_deadband'):
                zone = "CENTERED"
                color = (0, 255, 0)
            elif tracking_info.get('in_damping'):
                zone = "DAMPING"
                color = (255, 165, 0)  # RGB: Orange
            else:
                zone = "TRACKING"
                color = (255, 0, 0)  # RGB: Red
            
            cv2.putText(frame, zone, (10, h-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        else:
            cv2.putText(frame, "NO TARGET", (10, h-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)  # RGB: Red
        
        # Motor angles
        az = tracking_info['azimuth']
        alt = tracking_info['altitude']
        cv2.putText(frame, f"Az: {az:+.2f}deg", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Alt: {alt:+.2f}deg", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def get_combined_frame(self):
        """Get side-by-side combined frame"""
        if self.latest_frames[0] is None or self.latest_frames[1] is None:
            # Return blank frame until both cameras ready
            blank = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH*2, 3), dtype=np.uint8)
            cv2.putText(blank, "Waiting for cameras...", (CAMERA_WIDTH//2, CAMERA_HEIGHT//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            return blank
        
        # Combine frames side-by-side
        combined = np.hstack([self.latest_frames[0], self.latest_frames[1]])
        
        # Calculate stereo depth if both cameras have faces
        depth_info = self._calculate_stereo_depth()
        
        # Add depth overlay in center between cameras
        if depth_info:
            x_cm, y_cm, z_cm = depth_info
            depth_text = f"Distance: {z_cm:.0f}cm"
            position_text = self.depth_calculator.format_position(x_cm, y_cm, z_cm)
            
            # Get color based on distance
            depth_color = self.depth_calculator.get_distance_color(z_cm)
            
            # Draw centered between cameras
            text_x = CAMERA_WIDTH - 100
            cv2.putText(combined, depth_text, (text_x, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, depth_color, 2)
            cv2.putText(combined, position_text, (text_x, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add FPS overlay for each camera
        cv2.putText(combined, f"Cam0: {self.fps_list[0]:.1f}fps", (10, CAMERA_HEIGHT-40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        cv2.putText(combined, f"Cam1: {self.fps_list[1]:.1f}fps", (CAMERA_WIDTH+10, CAMERA_HEIGHT-40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        # Add separator line
        cv2.line(combined, (CAMERA_WIDTH, 0), (CAMERA_WIDTH, CAMERA_HEIGHT), (255, 255, 255), 2)
        
        return combined


# === Flask Web Server ===
app = Flask(__name__)
tracker = None

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dual Camera Virtual Face Tracker</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: #000;
            color: #fff;
            font-family: monospace;
            text-align: center;
        }
        h1 { color: #0f0; }
        img {
            max-width: 100%;
            border: 2px solid #0f0;
            margin: 20px auto;
            display: block;
        }
        .info {
            background: #222;
            padding: 10px;
            margin: 20px auto;
            max-width: 800px;
            border: 1px solid #0f0;
            text-align: left;
        }
    </style>
</head>
<body>
    <h1>🤖 Dual Camera Virtual Face Tracker</h1>
    <div class="info">
        <p><strong>Status:</strong> Calculating motor angles WITHOUT moving</p>
        <p><strong>Display:</strong> Camera 0 (left) | Camera 1 (right)</p>
        <p><strong>Green box:</strong> Face detection boundary</p>
        <p><strong>Red crosshair:</strong> Frame center (target position)</p>
        <p><strong>Blue dot:</strong> Face center</p>
        <p><strong>Circles:</strong> Deadband (inner) and damping (outer) zones</p>
        <p><strong>Angles:</strong> Virtual motor positions (not actually moving)</p>
    </div>
    <img src="{{ url_for('video_feed') }}" />
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/video_feed')
def video_feed():
    def generate():
        frame_skip = 0  # Skip frames to reduce streaming CPU load
        last_frame_time = time.time()
        
        while True:
            if tracker is None:
                time.sleep(0.1)
                continue
            
            # Only encode every 3rd frame to reduce CPU (10fps instead of 30fps)
            frame_skip += 1
            if frame_skip % 3 != 0:
                time.sleep(0.01)
                continue
            
            frame = tracker.get_combined_frame()
            
            # Don't convert - JPEG expects RGB and picamera2 gives us RGB
            # (The cv2.imencode handles it correctly)
            
            # Encode as JPEG with lower quality (50 instead of default 95)
            # This significantly reduces CPU load without affecting detection
            ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            if not ret:
                continue
            
            # Throttle to max 10fps for streaming
            current_time = time.time()
            elapsed = current_time - last_frame_time
            if elapsed < 0.1:  # 10fps = 0.1s per frame
                time.sleep(0.1 - elapsed)
            last_frame_time = time.time()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


def main():
    global tracker
    
    print("=" * 60)
    print("Dual Camera Virtual Face Tracker with Hailo")
    print("=" * 60)
    print("\nThis demonstrates tracking logic WITHOUT moving motors")
    print("Once this works, we'll connect to Klipper\n")
    
    # Create and start tracker
    tracker = DualCameraTracker(camera_nums=[0, 1])
    tracker.start()
    
    # Start Flask server
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()


if __name__ == '__main__':
    main()
