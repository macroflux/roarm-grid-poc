# RoArm Grid POC

Proof-of-concept: overhead USB camera watches a table with a **blue origin square** and **black target square**.  
If an object is detected in the blue square, a Waveshare **RoArm-M2-S** robot arm will attempt to pick it up and place it in the black square.

This is a standalone lab repo designed with a "Monad-ish" structure:
- `vision/` – camera + color-based detection of origin/target/object
- `arm/` – thin HTTP JSON client for RoArm-M2-S
- `controller/` – pick-and-place routine
- `telemetry/` – simple JSONL logging
- `main.py` – orchestrator loop

## Quickstart

1. Create and activate a virtualenv (optional but recommended), then install deps:

```bash
pip install -r requirements.txt
```

2. Edit `config/settings.yaml`:
   - Set your camera index (usually 0 on Windows).
   - Set the RoArm IP address (shown on the OLED when in STA/AP mode).
   - Tune HSV ranges for blue and black tape if needed.

3. Run the main loop:

```bash
python main.py
```

You should see:
- A live camera window with drawn boxes around the blue origin and black target.
- When an object is detected in the blue square and the controller is configured with valid poses, the arm will execute a simple scripted pick-and-place.

⚠️ **Safety**: keep clear of the arm's workspace when first testing. Use conservative speeds.
