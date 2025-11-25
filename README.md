# RoArm Grid POC

Proof-of-concept for vision-driven robot control: an overhead USB camera watches a table with a **blue origin square** and **red target square**. The system can operate in two modes:

1. **Scripted Pick/Place** - Uses pre-recorded joint poses to pick objects from origin and place in target
2. **Visual Push** (NEW!) - Uses image-based visual servoing to align the robot tip with objects and push them toward the target

This is a standalone lab repo designed with a "Monad-ish" structure:
- `vision/` – camera + color-based detection of origin/target/object + arm tip tracking
- `arm/` – thin HTTP JSON client for RoArm-M2-S
- `controller/` – scripted pick-and-place + visual push primitives
- `telemetry/` – simple JSONL logging for all operations
- `main.py` – orchestrator loop with dual-mode control

## Features

### Vision System
- **Zone Detection**: Identifies blue origin square and red target square using HSV color filtering
- **Object Detection**: Finds colored objects in origin zone while ignoring white background and black robot arm
- **Tip Tracking**: Detects neon pink marker on robot gripper for visual servoing
- **Color Semantics**: Can distinguish between red, green, and other colored objects

### Control Modes

#### 1. Scripted Pick/Place (Default)
Traditional hard-coded motion using pre-recorded joint angles:
- Safe homing sequence
- Move to origin → pick object → move to target → place object
- Configurable speeds, grip angles, and lift heights

#### 2. Visual Push (Press 'V' to toggle)
Image-based visual servoing that uses real-time camera feedback:
- **Tip-to-Object Alignment**: Moves robot tip to object center in image space
- **Push Primitive**: Pushes object from origin toward target along image vector
- No hard-coded poses - driven entirely by vision
- Foundation for learning-based control

## Quickstart

### 1. Install Dependencies

Create and activate a virtualenv (optional but recommended):

```bash
pip install -r requirements.txt
```

### 2. Physical Setup

- **Table**: Place white paper inside both the blue and red tape squares (helps with background subtraction)
- **Camera**: Mount overhead USB camera with view of both squares and robot workspace
  - Slight off-axis angle recommended so gripper doesn't block origin square
- **Robot Marker**: Attach a bright neon pink sticker to the robot gripper tip (for visual push mode)

### 3. Configuration

Edit `config/settings.yaml`:

**Camera Settings**
```yaml
camera:
  index: 1            # USB camera index (0, 1, 2...)
  width: 1280
  height: 720
```

**Arm Settings**
```yaml
arm:
  ip: "192.168.4.1"   # RoArm IP (shown on OLED display)
```

**Vision Tuning** (adjust based on your lighting/colors)
```yaml
vision:
  blue_lower: [90, 80, 50]      # Origin square HSV range
  blue_upper: [130, 255, 255]
  
  red_lower: [0, 100, 50]       # Target square HSV range
  red_upper: [10, 255, 255]
  
  tip_pink_lower: [140, 80, 80] # Pink tip marker HSV range
  tip_pink_upper: [170, 255, 255]
  
  # Object detection thresholds
  object_min_saturation: 60     # Filters out white background
  object_min_value: 60          # Filters out black robot arm
  object_max_value: 220         # Filters out blown-out whites
```

**Controller Settings**
- Record joint poses using the RoArm web UI
- Update `pose_home`, `pose_above_origin`, `pose_pick_origin`, etc.
- Tune visual push parameters (`push_gain_xy`, `push_steps`, etc.)

### 4. Run the System

```bash
python main.py
```

## Usage

### Live Camera View

The overhead view window shows:
- **Blue box** around origin square (labeled "ORIGIN")
- **Red box** around target square (labeled "TARGET")
- **Yellow dot** on detected objects (labeled "OBJECT")
- **Magenta dot** on robot tip marker (labeled "TIP")
- **Mode indicator** in top-left corner

### Keyboard Controls

| Key | Action |
|-----|--------|
| `ESC` | Exit program |
| `H` | Return to home position |
| `V` | Toggle between Scripted Pick/Place ↔ Visual Push modes |

### Operation

**Scripted Pick/Place Mode** (default):
1. System homes the robot and waits (configurable delay)
2. When object detected in blue square → executes pre-programmed pick-and-place
3. Returns to home position

**Visual Push Mode** (press 'V'):
1. System homes the robot and waits
2. When object detected in blue square AND tip marker visible:
   - Aligns robot tip with object center (image-based servo)
   - Pushes object toward red target square
3. All movements driven by real-time vision feedback

### Telemetry Logging

All operations are logged to `telemetry.log` in JSONL format:
- `pick_place_start`, `pick_place_success`, `pick_place_error`
- `visual_push_start`, `visual_push_success`, `visual_push_error`
- Complete state information (box positions, object centers, tip location)

This structured log enables future learning/optimization of control parameters.

## Architecture

### Vision Pipeline
- `vision/camera.py` - Camera interface with cross-platform backend detection
- `vision/grid_detector.py` - HSV-based zone detection (origin/target squares)
- `vision/object_detector.py` - Object detection with background/arm filtering
- `vision/arm_detector.py` - Pink tip marker tracking

### Control Layer
- `arm/roarm_client.py` - HTTP JSON client for RoArm-M2-S commands
- `controller/pick_place.py` - Scripted pick-and-place with joint poses
- `controller/visual_push.py` - Image-based visual servoing primitives

### Orchestration
- `main.py` - Main loop integrating vision, control, and telemetry
- `telemetry/logger.py` - JSONL event logging with context manager support
- `config/settings.yaml` - Centralized configuration for all subsystems

## Next Steps / Future Work

This POC establishes the foundation for learning-based robot control:

1. **Current State**: Vision-driven control primitives with complete telemetry
2. **Next**: Parameterized skill learning (tune `push_gain_xy`, `push_step_px`, etc. from logged data)
3. **Future**: RL/evolutionary approaches to discover optimal pushing strategies
4. **Beyond**: Multi-object scenarios, failure recovery, adaptive behaviors

The "Monad-ish" structure (sensor → perception → actuator with logging) makes it straightforward to swap hand-coded controllers for learned policies without redesigning the system.

## Safety

⚠️ **Important Safety Notes**:
- Keep clear of the arm's workspace during operation
- Start with conservative speeds (`speed_deg_per_s: 10-30`)
- Test scripted poses manually via web UI before automation
- Emergency stop: Press `ESC` or power off the arm
- Visual push mode is experimental - monitor closely during initial testing
