import os
import pickle
from typing import Optional, Dict, List

try:
    import face_recognition
except Exception:
    face_recognition = None


class PersonManager:
    """Simple face embedding manager using the `face_recognition` library.

    Stores named embeddings in a pickle file and can identify faces by
    comparing embeddings with cosine distance.
    If `face_recognition` is not available, identify() will always return None.
    """

    def __init__(self, db_path: str = "faces_db.pkl"):
        self.db_path = db_path
        self._data: Dict[str, List] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "rb") as f:
                    self._data = pickle.load(f)
            except Exception:
                self._data = {}

    def _save(self):
        try:
            with open(self.db_path, "wb") as f:
                pickle.dump(self._data, f)
        except Exception:
            pass

    def add_person_from_image(self, name: str, image_rgb) -> bool:
        """Add a person by providing an RGB image (numpy array).

        Returns True if an embedding was stored, False otherwise.
        """
        if face_recognition is None:
            return False

        # Get face encodings (list) from image
        encs = face_recognition.face_encodings(image_rgb)
        if not encs:
            return False

        emb = encs[0]
        self._data.setdefault(name, []).append(emb)
        self._save()
        return True

    def identify(self, image_rgb, tolerance: float = 0.6) -> Optional[str]:
        """Identify the given face image (RGB). Returns name or None."""
        if face_recognition is None:
            return None

        encs = face_recognition.face_encodings(image_rgb)
        if not encs:
            return None

        emb = encs[0]
        best_name = None
        best_dist = 1.0

        # Compare to each stored embedding
        for name, embs in self._data.items():
            for e in embs:
                # face_recognition uses euclidean distance; smaller is better
                dist = ( (emb - e) ** 2 ).sum() ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_name = name

        if best_name is not None and best_dist <= tolerance:
            return best_name
        return None
