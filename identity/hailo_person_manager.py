"""
Hailo-Based Person Manager
===========================

Uses Hailo SCRFD for face detection and simple template matching for recognition.
Much faster than CPU-based face_recognition library.
"""

import os
import pickle
import numpy as np
import cv2
from typing import Optional, Dict, List, Tuple


class HailoPersonManager:
    """Manage known faces using Hailo detection + template matching"""
    
    def __init__(self, db_path: str = "faces_db_hailo.pkl"):
        self.db_path = db_path
        self.people: Dict[str, List[np.ndarray]] = {}  # name -> list of face templates
        self.face_size = (112, 112)  # Normalized face size
        self.load_database()
    
    def load_database(self):
        """Load existing face database"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'rb') as f:
                    self.people = pickle.load(f)
                print(f"✓ Loaded {len(self.people)} person(s) from {self.db_path}")
            except Exception as e:
                print(f"⚠ Failed to load database: {e}")
                self.people = {}
        else:
            self.people = {}
    
    def save_database(self):
        """Save face database to disk"""
        try:
            with open(self.db_path, 'wb') as f:
                pickle.dump(self.people, f)
            print(f"✓ Saved database to {self.db_path}")
        except Exception as e:
            print(f"❌ Failed to save database: {e}")
    
    def _preprocess_face(self, face_img: np.ndarray) -> np.ndarray:
        """Normalize face image for comparison"""
        # Resize to standard size
        face_resized = cv2.resize(face_img, self.face_size)
        
        # Convert to grayscale for better matching
        if len(face_resized.shape) == 3:
            face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        else:
            face_gray = face_resized
        
        # Normalize histogram for lighting invariance
        face_norm = cv2.equalizeHist(face_gray)
        
        # Normalize values to 0-1
        face_float = face_norm.astype(np.float32) / 255.0
        
        return face_float
    
    def _compute_similarity(self, face1: np.ndarray, face2: np.ndarray) -> float:
        """Compute similarity between two face templates (0-1, higher is more similar)"""
        # Normalized cross-correlation
        corr = cv2.matchTemplate(face1.reshape(self.face_size), 
                                 face2.reshape(self.face_size), 
                                 cv2.TM_CCORR_NORMED)[0][0]
        
        # Convert to 0-1 range where 1 is perfect match
        similarity = (corr + 1.0) / 2.0
        
        return float(similarity)
    
    def add_person_from_face(self, name: str, face_img: np.ndarray) -> bool:
        """
        Add a face template for a person
        
        Args:
            name: Person's name
            face_img: Cropped face image (BGR format)
        
        Returns:
            True if successfully added
        """
        try:
            # Preprocess face
            face_template = self._preprocess_face(face_img)
            
            # Add to database
            if name not in self.people:
                self.people[name] = []
            
            self.people[name].append(face_template)
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding face for {name}: {e}")
            return False
    
    def add_person_from_images(self, name: str, image_paths: List[str]) -> int:
        """
        Add multiple face templates from image files
        
        Args:
            name: Person's name
            image_paths: List of image file paths
        
        Returns:
            Number of faces successfully added
        """
        count = 0
        for img_path in image_paths:
            try:
                img = cv2.imread(img_path)
                if img is not None:
                    # Assume whole image is the face (already cropped)
                    if self.add_person_from_face(name, img):
                        count += 1
            except Exception as e:
                print(f"⚠ Failed to load {img_path}: {e}")
        
        if count > 0:
            self.save_database()
        
        return count
    
    def identify(self, face_img: np.ndarray, threshold: float = 0.65) -> Optional[str]:
        """
        Identify a person from a face image
        
        Args:
            face_img: Cropped face image (BGR format)
            threshold: Similarity threshold (0-1, higher is stricter)
        
        Returns:
            Person's name if recognized, None otherwise
        """
        if not self.people:
            return None
        
        try:
            # Preprocess query face
            query_template = self._preprocess_face(face_img)
            
            # Find best match across all people
            best_name = None
            best_similarity = threshold
            
            for name, templates in self.people.items():
                # Compare against all templates for this person
                for template in templates:
                    similarity = self._compute_similarity(query_template, template)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_name = name
            
            return best_name
            
        except Exception as e:
            print(f"⚠ Error during identification: {e}")
            return None
    
    def get_all_people(self) -> List[Tuple[str, int]]:
        """Get list of all enrolled people with template counts"""
        return [(name, len(templates)) for name, templates in self.people.items()]
    
    def remove_person(self, name: str) -> bool:
        """Remove a person from database"""
        if name in self.people:
            del self.people[name]
            self.save_database()
            return True
        return False
