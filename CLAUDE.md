# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

basic_bot is a Python-centric robotics platform that provides an ultra-lightweight, websockets-based pub/sub service for robotics applications. It includes hardware support for motors, servos, sensors, computer vision, and object detection capabilities.

## Essential Commands

### Build
```bash
# Build the entire project using the `python -m build`
./build.sh

# Run both linting and type checking
./lint.sh

# Run linting only
python -m flake8 src/basic_bot

# Run type checking only
python -m mypy src/basic_bot
```

### Testing
```bash
# Run all tests (unit, integration, e2e)
./test.sh

# Run specific test types
python -m pytest -vv tests/unit_tests/
python -m pytest -vv tests/integration_tests/
python -m pytest -vv tests/e2e_tests/

# Run single test with verbose output
python -m pytest -vv tests/integration_tests/test_central_hub.py -k test_connect_identify
```

### Development Installation
```bash
# Install development dependencies
python -m pip install -r requirements.txt

# Install as editable package for development
./install-dev.sh

# Install mypy types
python -m mypy --install-types
```

### Package Management
```bash
# Install the basic_bot package
./install.sh

# Create new robot project
bb_create my_new_robot_project

# Start/stop services
bb_start    # Start all services defined in basic_bot.yml
bb_stop     # Stop all services
bb_ps       # Show running services
bb_killall  # Kill all basic_bot processes
```

## Architecture Overview

### Core Services Architecture
The platform uses a microservices architecture where all services communicate through the `central_hub` via websockets:

- **central_hub**: Ultra-lightweight pub/sub service (<5ms latency) that maintains shared state in memory
- **web_server**: Serves the web interface (looks in `./webapp/dist` for static files)
- **vision**: Computer vision service using OpenCV and TensorFlow Lite for object detection and video feed
- **system_stats**: System monitoring and statistics collection
- **motor_control_2w**: Two-wheel motor control service
- **servo_control**: Servo motor control service

### Key Components

**Services** (`src/basic_bot/services/`): Each service is a standalone Python module that connects to central_hub for state management and communication. Services can also be written in other languages as long as they support websockets and JSON parsing.

**Commons** (`src/basic_bot/commons/`): Shared utilities including:
- `hub_state.py`: State management for central_hub
- `camera_*.py`: Camera abstraction layers (OpenCV, PiCamera)
- `tflite_detect.py`: TensorFlow Lite object detection
- `messages.py`: Message schemas for websocket communication
- `log.py`: Centralized logging utilities

**Configuration**: Services are defined in `basic_bot.yml` with environment variables and run commands.

### Central Hub Message Protocol
All websocket communication uses JSON format:
```json
{
    "type": "string",
    "data": { ... }  // Optional, message-specific payload
}
```

**Core Message Types:**
- `getState`: Request current state (specific keys or all state)
- `updateState`: Merge new state data (requires full data for each key)
- `subscribeState`: Subscribe to state key changes (use "*" for all keys)
- `identity`: Register subsystem name and receive client IP info
- `ping/pong`: Keepalive mechanism

**Automatic State Keys:**
- `hub_stats`: Tracks state update counts
- `subsystem_stats`: Online status of connected subsystems

### Environment Variables
- `BB_ENV=production`: Required on robot hardware to enable real hardware interfaces
- `BB_LOG_ALL_MESSAGES`: Enable verbose message logging
- `BB_CAMERA_MODULE`: Specify camera module (e.g., "basic_bot.commons.camera_picamera")

## Development Notes

### Project Creation Flow
The `bb_create` command creates a complete robotics project with:
- Web application template (Vite-based React app with LCARS-styled UI)
- Example service with counter functionality
- Shell scripts for build, test, start, stop, upload (via rsync/ssh)
- Integration test examples
- Example `basic_bot.yml` configuration file
- Debug scripts and test images

**Upload Process**: Uses `upload.sh` script with rsync over SSH:
```bash
./upload.sh pi@my_raspberry_bot.local /home/pi/my_bot
```

### Testing Strategy
- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test service interactions with central_hub
- **E2E tests**: Test complete workflows including bb_create functionality
- **Field tests**: Hardware-specific tests (run on target hardware)

### Vision System
The vision service provides:
- Video feed via HTTP endpoint (`http://<ip>:5001/video_feed`) as multipart JPEG stream
- Object recognition using TensorFlow Lite with COCO labels
- Real-time bounding box detection published to central_hub with format:
```json
{
    "recognition": [
        {
            "bounding_box": [x1, y1, x2, y2],
            "classification": "person",
            "confidence": 0.99
        }
    ]
}
```

### Hardware Environment
Platform supports development on macOS/Linux with deployment to Raspberry Pi 4/5. Hardware-specific modules use mock implementations in development environment unless `BB_ENV=production` is set. The platform requires:
- Python >= 3.9
- Node.js >= v20.18 for web interface development
- `--system-site-packages` when creating venv on Raspberry Pi (for Picamera2 support)

### Debugging Tools
Available via `basic_bot.debug` package:
- `python -m basic_bot.debug.test_opencv_capture`: Test OpenCV camera functionality
- `python -m basic_bot.debug.test_picam2_opencv_capture`: Test PiCamera2 integration on Raspberry Pi
- Logs available in `./logs/*` directory for each service

## Code Quality Standards

- **Linting**: Flake8 with max line length 120, configured in `.flake8`
- **Type Checking**: MyPy with ignore_missing_imports enabled
- **Python Version**: Requires Python ≥3.9
- **Dependencies**: Managed in `pyproject.toml`, development deps in `requirements.txt`

### Code guidelines (like suggestions)

- when importing constants.py use `from commons import constants as c`. reason: I'm not a big fan of making person or AI type out `constants.` everywhere they need a constant.  I also don't see the value in forcing each individual const to be imported like `from common.constants import BB_WHATEVER`.  Import once as `c` and then just `c.BB_WHATEVER`.  This guidence may only apply to heavily used imports like constants.py
