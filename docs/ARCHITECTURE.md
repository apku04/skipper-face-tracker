# Skipper Architecture

## 📁 Folder Structure

```
skipper/
├── core/                          # Core application logic
│   ├── __init__.py
│   ├── app.py                    # Main application orchestrator
│   └── config_manager.py         # Configuration management
│
├── vision/                        # Computer vision & face tracking
│   ├── __init__.py
│   ├── face_detector.py          # Hailo face detection
│   ├── face_recognizer.py        # Face recognition & embeddings
│   ├── face_tracker.py           # Face tracking logic
│   ├── camera_manager.py         # Camera abstraction (single/dual)
│   └── enrollment.py             # Face enrollment system
│
├── motors/                        # Motor control & movement
│   ├── __init__.py
│   ├── klipper_client.py         # Klipper API client
│   ├── movement_controller.py    # High-level movement logic
│   ├── calibration.py            # Motor calibration tools
│   └── face_follower.py          # Face following behavior
│
├── sensors/                       # Environmental sensors
│   ├── __init__.py
│   ├── i2c_multiplexer.py        # TCA9548A multiplexer
│   ├── temperature_humidity.py   # SHT3x sensor
│   ├── pressure.py               # BMP280 sensor
│   └── sensor_manager.py         # Unified sensor interface
│
├── ai/                            # AI/LLM integration (future)
│   ├── __init__.py
│   ├── llm_client.py             # LLM API client (Ollama, OpenAI, etc)
│   ├── context_manager.py        # Conversation context
│   ├── prompt_templates.py       # System prompts
│   └── embeddings.py             # Vector embeddings for RAG
│
├── audio/                         # Audio I/O (future voice features)
│   ├── __init__.py
│   ├── speech_to_text.py         # STT interface
│   ├── text_to_speech.py         # TTS interface
│   └── audio_device.py           # Audio hardware abstraction
│
├── utils/                         # Shared utilities
│   ├── __init__.py
│   ├── logging.py                # Logging configuration
│   ├── validators.py             # Input validation
│   ├── image_utils.py            # Image processing helpers
│   └── system_info.py            # System diagnostics
│
├── config/                        # Configuration files
│   ├── default.yaml              # Default configuration
│   ├── camera.yaml               # Camera settings
│   ├── motors.yaml               # Motor parameters
│   ├── sensors.yaml              # Sensor configuration
│   └── printer.cfg.example       # Klipper config template
│
├── models/                        # ML models & weights
│   ├── hailo/                    # Hailo model files
│   │   └── scrfd_10g.hef
│   └── face_db/                  # Face recognition database
│       └── faces_db.pkl
│
├── data/                          # Runtime data & logs
│   ├── logs/                     # Application logs
│   ├── enrollment/               # Enrollment photos
│   └── cache/                    # Temporary cache
│
├── tests/                         # Unit & integration tests
│   ├── __init__.py
│   ├── test_vision.py
│   ├── test_motors.py
│   ├── test_sensors.py
│   └── test_integration.py
│
├── scripts/                       # Standalone utility scripts
│   ├── capture_enrollment.py     # Face enrollment capture
│   ├── calibrate_motors.py       # Motor calibration
│   ├── test_hardware.py          # Hardware diagnostics
│   └── setup/                    # Setup scripts
│       ├── install_dependencies.sh
│       └── configure_system.sh
│
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md           # This file
│   ├── API.md                    # API documentation
│   ├── HARDWARE.md               # Hardware setup
│   └── DEVELOPMENT.md            # Development guide
│
├── web/                           # Web interface (Flask/FastAPI)
│   ├── __init__.py
│   ├── app.py                    # Web server
│   ├── routes/                   # API routes
│   ├── static/                   # CSS, JS, images
│   └── templates/                # HTML templates
│
├── main.py                        # Main entry point
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
├── README.md                      # Project documentation
└── .env.example                   # Environment variables template
```

---

## 🎯 Design Principles

### 1. **Separation of Concerns**
Each module has a single, well-defined responsibility:
- `vision/` - Everything related to cameras and face detection
- `motors/` - All motor control and movement logic
- `sensors/` - Environmental sensor reading and management
- `ai/` - LLM and AI-related features (future-ready)

### 2. **Abstraction Layers**
```
High-level API → Business Logic → Hardware Abstraction → Hardware Drivers
```

Example:
```
face_follower.py → movement_controller.py → klipper_client.py → Klipper Firmware
```

### 3. **Dependency Injection**
Components receive dependencies through constructors, making testing easier:

```python
class FaceFollower:
    def __init__(self, detector, tracker, motor_controller):
        self.detector = detector
        self.tracker = tracker
        self.motors = motor_controller
```

### 4. **Configuration Management**
All configuration in YAML files, no hardcoded values:
- Environment-specific configs (dev, prod)
- Easy parameter tuning without code changes
- Version controlled configuration

### 5. **Future-Ready AI Integration**
Pre-planned `ai/` module structure for:
- **LLM Integration**: Chat with the robot about what it sees
- **Context Awareness**: Remember faces, conversations, preferences
- **RAG (Retrieval-Augmented Generation)**: Search through face database with natural language
- **Multimodal AI**: Combine vision, sensor data, and language

---

## 🔄 Data Flow

### Face Tracking Flow
```
Camera → FaceDetector (Hailo) → FaceRecognizer → FaceTracker → FaceFollower → MotorController → Klipper
```

### Sensor Reading Flow
```
TCA9548A → SensorManager → [SHT3x, BMP280] → Data Aggregation → Storage/Display/AI
```

### Future LLM Integration Flow
```
User Query → LLM Client → Context Manager → [Vision Data, Sensor Data, Face DB] → LLM Response
```

Example:
- User: "Who is in front of me?"
- System: Vision → Face Recognition → Context → LLM → "I see Achuthan standing 2 meters away"

---

## 🧩 Module Details

### `core/` - Application Core
**Purpose**: Orchestrate all subsystems, manage lifecycle

**Key Classes**:
- `Application` - Main app coordinator
- `ConfigManager` - Load/validate configs

**Responsibilities**:
- Initialize all subsystems
- Handle graceful shutdown
- Coordinate between modules
- Global error handling

---

### `vision/` - Computer Vision
**Purpose**: All camera and face-related functionality

**Key Classes**:
- `HailoFaceDetector` - SCRFD face detection
- `FaceRecognizer` - Template matching, embeddings
- `FaceTracker` - Track faces across frames
- `CameraManager` - Manage single/dual cameras
- `EnrollmentManager` - Face enrollment pipeline

**Hardware**:
- Hailo-8L HAT (AI accelerator)
- IMX708 CSI cameras

**Data Flow**:
```python
camera.capture() → detector.detect() → recognizer.identify() → tracker.update()
```

---

### `motors/` - Movement Control
**Purpose**: Motor control and face following

**Key Classes**:
- `KlipperClient` - Communicate with Klipper API
- `MovementController` - High-level movement commands
- `CalibrationManager` - Motor calibration tools
- `FaceFollower` - Face following behavior

**Hardware**:
- Stepper motors (pan/tilt)
- Klipper firmware on MCU

**Example Usage**:
```python
motor_controller.move_to(pan=45, tilt=15)
face_follower.follow(face_position)
```

---

### `sensors/` - Environmental Sensing
**Purpose**: Read and manage I2C sensors

**Key Classes**:
- `TCA9548A` - I2C multiplexer controller
- `SHT3xSensor` - Temperature & humidity
- `BMP280Sensor` - Temperature & pressure
- `SensorManager` - Unified sensor interface

**Hardware**:
- TCA9548A I2C multiplexer
- SHT3x (0x44, channel 0)
- BMP280 (0x76, channel 1)

**Example Usage**:
```python
sensor_manager.read_all()  # Returns all sensor data
sensor_manager.get_temperature()  # Average temperature
```

---

### `ai/` - AI & LLM (Future)
**Purpose**: Intelligent conversation and reasoning

**Planned Features**:

#### 1. **LLM Integration**
```python
class LLMClient:
    def chat(self, message, context):
        """Chat with multimodal context"""
        
    def describe_scene(self, vision_data, sensor_data):
        """Describe what the robot sees"""
```

#### 2. **Context Management**
- Remember previous interactions
- Track face appearances over time
- Build user profiles

#### 3. **RAG (Retrieval-Augmented Generation)**
```python
# Search face database with natural language
llm.query("Who did I meet last Tuesday?")
# → Searches embeddings, finds faces, generates response
```

#### 4. **Multimodal Understanding**
Combine multiple data sources:
```python
context = {
    "vision": "Face detected: Achuthan",
    "sensors": "Temperature: 24.5°C, Humidity: 48%",
    "time": "2025-11-01 10:30",
    "history": "Last seen 2 hours ago"
}
llm.chat("What's the environment like?", context)
# → "The room is comfortable at 24.5°C with Achuthan present."
```

#### 5. **Planned Integrations**
- **Ollama** - Local LLM (Llama 3.2, Mistral)
- **OpenAI API** - GPT-4, GPT-4 Vision
- **Anthropic Claude** - Advanced reasoning
- **Vector DB** - ChromaDB, Qdrant for embeddings

---

### `utils/` - Shared Utilities
**Purpose**: Common helper functions

**Modules**:
- `logging.py` - Structured logging
- `validators.py` - Input validation
- `image_utils.py` - Image processing
- `system_info.py` - System diagnostics

---

### `web/` - Web Interface
**Purpose**: Browser-based control and monitoring

**Features**:
- Live camera feed
- Face recognition display
- Sensor data dashboard
- Motor control panel
- Configuration interface

**Tech Stack**:
- Backend: Flask or FastAPI
- Frontend: HTML, CSS, JavaScript
- Real-time: WebSockets for live feed

---

## 🚀 Entry Points

### `main.py` - Main Application
```python
# Run full face tracking system
python3 main.py --mode tracking --cameras 0 1

# Single camera mode
python3 main.py --mode tracking --single-camera 0

# Web interface only
python3 main.py --mode web --port 5000
```

### `scripts/` - Utility Scripts
```bash
# Enroll new face
python3 scripts/capture_enrollment.py --name "Person" --camera 0

# Calibrate motors
python3 scripts/calibrate_motors.py

# Test hardware
python3 scripts/test_hardware.py --component sensors
```

---

## 📦 Package Structure

Make `skipper` a proper Python package:

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="skipper",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "opencv-python",
        "numpy",
        "flask",
        "pyyaml",
        "smbus2",
        "picamera2",
    ],
    entry_points={
        "console_scripts": [
            "skipper=core.app:main",
            "skipper-enroll=scripts.capture_enrollment:main",
            "skipper-calibrate=scripts.calibrate_motors:main",
        ],
    },
)
```

Then install in development mode:
```bash
pip3 install -e .
```

Use clean imports:
```python
from skipper.vision import FaceDetector
from skipper.motors import MovementController
from skipper.sensors import SensorManager
```

---

## 🧪 Testing Strategy

### Unit Tests (`tests/`)
```python
# tests/test_vision.py
def test_face_detection():
    detector = FaceDetector()
    faces = detector.detect(test_image)
    assert len(faces) > 0

# tests/test_motors.py
def test_movement_range():
    controller = MovementController()
    controller.move_to(pan=45, tilt=30)
    assert controller.get_position() == (45, 30)
```

### Integration Tests
```python
# tests/test_integration.py
def test_face_following_pipeline():
    """Test complete face detection → tracking → motor control"""
    camera = CameraManager()
    detector = FaceDetector()
    follower = FaceFollower()
    
    frame = camera.capture()
    faces = detector.detect(frame)
    follower.follow(faces[0])
    
    assert motor_controller.is_moving()
```

---

## 🔮 Future Enhancements

### Phase 1: Current (Face Tracking + Sensors)
- ✅ Hailo face detection
- ✅ Face recognition
- ✅ Motor control via Klipper
- ✅ Environmental sensors

### Phase 2: AI Integration
- 🔄 LLM client (Ollama)
- 🔄 Context-aware conversations
- 🔄 Scene description
- 🔄 Natural language queries

### Phase 3: Advanced AI
- ⏳ RAG with face database
- ⏳ Multimodal understanding (vision + sensors + language)
- ⏳ Predictive behavior (anticipate user needs)
- ⏳ Voice interaction (STT/TTS integration)

### Phase 4: Edge AI
- ⏳ On-device LLM (Llama.cpp, GGUF models on Hailo)
- ⏳ Real-time video understanding
- ⏳ Gesture recognition
- ⏳ Emotion detection

---

## 📊 Configuration Management

### Environment Variables (`.env`)
```bash
# Hardware
HAILO_DEVICE=/dev/hailo0
KLIPPER_HOST=localhost
KLIPPER_PORT=7125

# AI/LLM (future)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OPENAI_API_KEY=sk-...

# Paths
DATA_DIR=/home/pi/work/skipper/data
MODEL_DIR=/home/pi/work/skipper/models
```

### YAML Configs
```yaml
# config/camera.yaml
camera:
  resolution: [1640, 1232]
  framerate: 30
  format: RGB888
  dual_mode: true
  cameras: [0, 1]

# config/motors.yaml
motors:
  pan:
    limits: [-180, 180]
    speed: 50
    acceleration: 100
  tilt:
    limits: [-90, 90]
    speed: 40
    acceleration: 80

# config/sensors.yaml
sensors:
  multiplexer:
    address: 0x70
    bus: 1
  sht3x:
    channel: 0
    address: 0x44
  bmp280:
    channel: 1
    address: 0x76
```

---

## 🔗 Dependencies Between Modules

```
core/
├── vision/ (uses)
├── motors/ (uses)
├── sensors/ (uses)
├── ai/ (uses, future)
└── utils/ (uses)

vision/
├── utils/ (uses)
└── models/ (reads)

motors/
└── utils/ (uses)

sensors/
└── utils/ (uses)

ai/ (future)
├── vision/ (uses)
├── sensors/ (uses)
├── utils/ (uses)
└── models/ (reads)
```

**Rule**: No circular dependencies. Dependencies flow downward.

---

## 📝 Summary

This architecture is:
- **Modular**: Easy to add/remove features
- **Testable**: Clear boundaries for unit testing
- **Scalable**: Ready for LLM and AI integration
- **Maintainable**: Well-organized, easy to navigate
- **Professional**: Follows Python packaging best practices

The structure separates hardware concerns (vision, motors, sensors) from future AI features (ai/, audio/), making it easy to evolve the project as LLM integration becomes ready.
