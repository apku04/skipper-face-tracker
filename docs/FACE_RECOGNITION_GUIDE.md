# Face Recognition System - User Guide

## Overview

The face tracker uses **stable CPU-based face recognition** (dlib/face_recognition library) for reliable, crash-free operation. The system combines:

- **Hailo-accelerated face detection** (SCRFD) - Fast detection at 30+ FPS
- **Dlib face recognition** - Stable 128D embeddings, no crashes
- **Real-time tracking** - Visual feedback via web interface

---

## Quick Start

### 1. Capture Enrollment Photos

Use the web-based capture interface for guided photo capture:

```bash
sudo python3 scripts/setup/enroll_web.py --name "YourName"
```

Then open in browser: **http://optimus:5001**

**Features:**
- Live camera preview
- Step-by-step instructions for each pose
- Progress bar
- Automatic capture of 15-20 varied photos

**Tips for best results:**
- Stand 50cm-1m from camera
- Good, even lighting
- Follow on-screen pose instructions
- Capture takes ~2-3 minutes

### 2. Enroll Face from Photos

After capturing photos, enroll them into the recognition database:

```bash
python3 scripts/setup/enroll_stable.py --name "YourName" --images enrollment_photos/YourName_*.jpg
```

**Expected output:**
```
✅ SUCCESS: Enrolled 15/20 images for 'YourName'
Database: models/face_db/faces_db_stable.pkl
```

**Recommendations:**
- **5-10 embeddings**: Minimum for basic recognition
- **15-25 embeddings**: Good reliability
- **30+ embeddings**: Excellent accuracy (diminishing returns beyond 40)

### 3. Start Face Tracking

Run the tracker with recognition enabled:

```bash
sudo python3 vision/virtual_tracking_dual.py --single-camera 0
```

Open in browser: **http://optimus:5000**

**What you'll see:**
- Live camera feed
- Green box around detected face
- Name label when recognized: `"YourName (0.65)"`
- Confidence score (0.6+ = recognized)

Press **Ctrl+C** to stop.

---

## Common Tasks

### List Enrolled People

```bash
python3 scripts/setup/enroll_stable.py --list
```

### Remove Someone from Database

```bash
python3 scripts/setup/enroll_stable.py --remove "PersonName"
```

### Re-enroll Someone (Improve Recognition)

If recognition isn't working well:

1. **Remove old enrollment:**
   ```bash
   python3 scripts/setup/enroll_stable.py --remove "YourName"
   ```

2. **Capture fresh photos** (with better lighting/variety):
   ```bash
   sudo python3 scripts/setup/enroll_web.py --name "YourName"
   ```

3. **Enroll new photos:**
   ```bash
   python3 scripts/setup/enroll_stable.py --name "YourName" --images enrollment_photos/YourName_*.jpg
   ```

4. **Restart tracker:**
   ```bash
   sudo python3 vision/virtual_tracking_dual.py --single-camera 0
   ```

### Add More Photos (Without Removing)

To improve recognition without removing existing data:

```bash
# Capture additional photos
sudo python3 scripts/setup/enroll_web.py --name "YourName"

# Enroll them (they will be ADDED to existing embeddings)
python3 scripts/setup/enroll_stable.py --name "YourName" --images enrollment_photos/YourName_*.jpg
```

Note: Embeddings are **appended**, not replaced. Multiple enrollments accumulate.

---

## Tuning Recognition Threshold

If recognition is too strict or too loose, adjust the threshold:

**Edit:** `vision/virtual_tracking_dual.py` line ~764

```python
# Current (moderate)
name_found, score = self._identify_with_threshold(face_crop, min_score=0.5)

# Stricter (fewer false positives)
name_found, score = self._identify_with_threshold(face_crop, min_score=0.6)

# Looser (more permissive)
name_found, score = self._identify_with_threshold(face_crop, min_score=0.4)
```

**Threshold guide:**
- **0.7+**: Very strict (may miss valid matches)
- **0.6**: Strict (good for distinguishing family members)
- **0.5**: Moderate (recommended default)
- **0.4**: Loose (may confuse similar faces)

After changing, restart the tracker.

---

## Troubleshooting

### Face Not Recognized

**Symptoms:** Tracker detects face but shows no name

**Solutions:**

1. **Check enrollment:**
   ```bash
   python3 scripts/setup/enroll_stable.py --list
   ```
   - Is the person enrolled?
   - Do they have at least 5 embeddings?

2. **Check lighting/distance:**
   - Current conditions should match enrollment conditions
   - Optimal distance: 50cm-1m from camera

3. **Lower threshold** (try 0.4-0.5 instead of 0.6)

4. **Re-enroll with better photos:**
   - More varied lighting/angles
   - Closer to current conditions

### Camera Issues

**Blurry image:**
- RPi Camera Module 3 has fixed focus
- Optimal range: 50cm-2m
- Check lens is clean
- Manual focus ring can be gently adjusted

**Camera not detected:**
```bash
# Check camera
libcamera-hello --list-cameras

# Test camera
libcamera-still -o test.jpg
```

### Performance Issues

**Slow recognition:**
- Face recognition runs every 15 frames (configurable)
- CPU-based processing (expected on Pi 5)
- Reduce `CAMERA_WIDTH/HEIGHT` for faster processing

**Edit:** `vision/virtual_tracking_dual.py`
```python
CAMERA_WIDTH = 640   # Lower for faster processing
CAMERA_HEIGHT = 640
```

---

## File Locations

### Databases
- **Active database:** `models/face_db/faces_db_stable.pkl`
- **Enrollment photos:** `enrollment_photos/`

### Scripts
- **Web capture:** `scripts/setup/enroll_web.py`
- **Enrollment:** `scripts/setup/enroll_stable.py`
- **Tracker:** `vision/virtual_tracking_dual.py`

### Recognition System
- **Manager:** `vision/identity/stable_person_manager.py`
- **Library:** `face_recognition` (dlib-based)

---

## Technical Details

### Recognition Pipeline

1. **Detection (Hailo SCRFD):** 
   - Finds faces in frame
   - Returns bounding boxes
   - Runs at ~30 FPS

2. **Recognition (dlib):**
   - Extracts 128D embedding from face crop
   - Compares with enrolled embeddings using cosine similarity
   - Runs every 15 frames to reduce CPU load

3. **Matching:**
   - Compares query embedding against all enrolled embeddings
   - Returns best match if similarity > threshold
   - Caches result for 3 seconds

### Database Format

The `.pkl` file contains a Python dictionary:
```python
{
    "PersonName": [
        np.array([128D embedding]),
        np.array([128D embedding]),
        ...
    ],
    ...
}
```

Each person has a list of 128-dimensional face embeddings (from dlib ResNet model).

### Why Stable vs Deep/Hailo?

**Previous systems tried:**
- ❌ **Template matching** (HailoPersonManager): Pixel-level comparison, can't distinguish family
- ❌ **InsightFace/ArcFace** (DeepPersonManager): ONNX runtime crashes on Pi

**Current system (StablePersonManager):**
- ✅ CPU-based dlib (no ONNX dependencies)
- ✅ 100% stable, no crashes
- ✅ 128D embeddings (proper deep learning)
- ✅ Can distinguish similar faces
- ⚠️ Slower than GPU/Hailo (but acceptable for real-time tracking)

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs: `logs/boot_diagnostics_*.log`
3. Test with debug script: `scripts/test_recognition.py`
