"""
Stable CPU-Based Person Manager
================================

Uses face_recognition library (dlib-based) for rock-solid face recognition.
Slower than InsightFace but 100% stable - no ONNX crashes.

Key advantages:
- 128D embeddings (dlib ResNet)
- Battle-tested, stable on all platforms
- No ONNX/runtime dependencies
- Works with cropped faces directly
"""

import os
import pickle
import numpy as np
import cv2
from typing import Optional, Dict, List, Tuple
import face_recognition


class StablePersonManager:
    """
    Manages face recognition using dlib face_recognition library
    
    CPU-based but very reliable - no crashes
    """
    
    def __init__(self, db_path: str = "models/face_db/faces_db_stable.pkl"):
        self.db_path = db_path
        self.people = {}  # name -> list of 128D embeddings
        
        print("✓ Initialized face_recognition (dlib-based, stable)")
        
        # Load existing database
        self.load_database()
    
    def load_database(self):
        """Load face database from disk"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'rb') as f:
                    self.people = pickle.load(f)
                print(f"✓ Loaded {len(self.people)} people from {self.db_path}")
            except Exception as e:
                print(f"⚠ Failed to load database: {e}")
                self.people = {}
        else:
            print(f"No existing database at {self.db_path}")
            self.people = {}
    
    def save_database(self):
        """Save face database to disk"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        try:
            with open(self.db_path, 'wb') as f:
                pickle.dump(self.people, f)
            print(f"✓ Saved database to {self.db_path}")
        except Exception as e:
            print(f"⚠ Failed to save database: {e}")
    
    def _get_embedding(self, face_img: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract 128D embedding from face image
        
        Args:
            face_img: Face image (BGR format from OpenCV)
        
        Returns:
            128D embedding vector, or None if face not detected
        """
        try:
            # face_recognition expects RGB
            if len(face_img.shape) == 3 and face_img.shape[2] == 3:
                face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            else:
                face_rgb = face_img
            
            # Get face encodings (128D embeddings)
            # model='large' uses more accurate CNN model
            encodings = face_recognition.face_encodings(face_rgb, model='large')
            
            if len(encodings) == 0:
                return None
            
            # Return first encoding (largest face usually detected first)
            return encodings[0]
            
        except Exception as e:
            print(f"⚠ Error extracting embedding: {e}")
            return None
    
    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Returns value between 0 and 1, where:
        - 1.0 = identical
        - 0.6+ = same person (typical threshold)
        - 0.4-0.6 = uncertain
        """
        # Normalize
        emb1_norm = emb1 / np.linalg.norm(emb1)
        emb2_norm = emb2 / np.linalg.norm(emb2)
        
        # Compute similarity
        similarity = np.dot(emb1_norm, emb2_norm)
        
        # Convert to 0-1 range (cosine is -1 to 1)
        return float((similarity + 1.0) / 2.0)
    
    def add_person_from_face(self, name: str, face_img: np.ndarray) -> bool:
        """
        Add a face embedding for a person
        
        Args:
            name: Person's name
            face_img: Face image (BGR format from OpenCV)
        
        Returns:
            True if successfully added, False otherwise
        """
        embedding = self._get_embedding(face_img)
        
        if embedding is None:
            return False
        
        if name not in self.people:
            self.people[name] = []
        
        self.people[name].append(embedding)
        print(f"✓ Added embedding for {name} (total: {len(self.people[name])})")
        
        return True
    
    def add_person_from_images(self, name: str, image_paths: List[str]) -> int:
        """
        Add multiple face embeddings for a person
        
        Args:
            name: Person's name
            image_paths: List of image file paths
        
        Returns:
            Number of successfully added embeddings
        """
        count = 0
        for img_path in image_paths:
            try:
                img = cv2.imread(img_path)
                if img is not None:
                    if self.add_person_from_face(name, img):
                        count += 1
            except Exception as e:
                print(f"⚠ Failed to load {img_path}: {e}")
        
        if count > 0:
            self.save_database()
        
        return count
    
    def identify(self, face_img: np.ndarray, threshold: float = 0.6) -> Optional[str]:
        """
        Identify a person from a face image
        
        Args:
            face_img: Face image (BGR format)
            threshold: Similarity threshold (0.5-0.7 typical)
        
        Returns:
            Person's name if recognized, None otherwise
        """
        name, _ = self.identify_with_score(face_img, threshold)
        return name
    
    def identify_with_score(self, face_img: np.ndarray, threshold: float = 0.6) -> Tuple[Optional[str], float]:
        """
        Identify a person and return confidence score
        
        Args:
            face_img: Face image (BGR format)
            threshold: Similarity threshold
        
        Returns:
            Tuple of (person's name or None, similarity score)
        """
        if not self.people:
            return None, 0.0
        
        try:
            # Get embedding for query face
            query_embedding = self._get_embedding(face_img)
            
            if query_embedding is None:
                return None, 0.0
            
            # Find best match across all people
            best_name = None
            best_similarity = 0.0
            
            for name, embeddings in self.people.items():
                # Compare against all embeddings for this person
                for embedding in embeddings:
                    similarity = self._cosine_similarity(query_embedding, embedding)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_name = name
            
            # Only return name if it exceeds threshold
            if best_similarity >= threshold:
                return best_name, best_similarity
            else:
                return None, best_similarity
            
        except Exception as e:
            print(f"⚠ Error during identification: {e}")
            return None, 0.0
    
    def get_all_people(self) -> List[Tuple[str, int]]:
        """Get list of all enrolled people with embedding counts"""
        return [(name, len(embeddings)) for name, embeddings in self.people.items()]
    
    def remove_person(self, name: str) -> bool:
        """Remove a person from database"""
        if name in self.people:
            del self.people[name]
            self.save_database()
            return True
        return False
    
    def clear_database(self):
        """Clear all enrolled people"""
        self.people = {}
        self.save_database()
        print("✓ Database cleared")


if __name__ == "__main__":
    # Test the manager
    print("Testing StablePersonManager...")
    manager = StablePersonManager()
    
    # List enrolled people
    people = manager.get_all_people()
    print(f"\nEnrolled people: {people}")
