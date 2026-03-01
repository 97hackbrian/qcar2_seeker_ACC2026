# QCar2 Behavior Tree — Autonomous Mission System

> **Team Seeker UCB** — Universidad Católica Boliviana "San Pablo"

| Role | Member |
|---|---|
| Developer | **Eduardo Vargas** |
| Developer | **Brayan Duran** |
| Developer | **Leyla Lipa** |
| Developer | **Mariel Valeriano** |

---

## Overview

A fully configurable **Behavior Tree (BT)** mission manager for the Quanser QCar2 platform, built on **ROS 2 Humble**.

The main node, `qcar2_behavior_tree_manager`, reads a YAML-defined mission sequence and autonomously:

- Dispatches navigation goals as `PoseStamped` messages.
- Switches between driving modes (`HYBRID`, `LANE_PID`, `STOPPED`, etc.).
- Controls onboard LEDs via topic commands.
- Reacts to real-time object detections: **persons**, **stop signs**, **traffic lights**, and **zebra crossings**.
- Waits for a complete TF chain (`map → odom → base_link`) before starting the mission.
- Monitors goal-reached distance and per-goal timeouts.
- Loops the mission automatically once all goals have been visited.

The mother launch file (`qcar2_behavior_tree_mother.launch.py`) brings up the BT manager together with the hybrid planner from `qcar2_mixer`, providing a single entry point for the full autonomous stack.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Behavior Tree Manager                  │
│                                                          │
│  RepeatForever                                           │
│  └─ Sequence (mission_sequence)                          │
│      ├─ Condition: TF chain ready?                       │
│      ├─ Action: publish runtime state                    │
│      ├─ Condition: has goals?                            │
│      ├─ Action: set_mode (HYBRID / LANE_PID / STOPPED)  │
│      ├─ Action: set_led (init / to_pickup / idle …)     │
│      ├─ Wait: N seconds                                 │
│      ├─ Action: dispatch_next_goal                       │
│      ├─ Action: wait_goal_reached_or_timeout             │
│      └─ … (remaining steps from YAML)                   │
└──────────────────────────────────────────────────────────┘
        │ publishes                     │ subscribes
        ▼                               ▼
  /bt/goal (PoseStamped)       /detections/person
  /bt/state (String)           /detections/stop_sign
  /bt/mode_hybrid (String)     /detections/traffic_light
  /bt/mode_hybrid_numeric      /detections/zebra_crossing
  /btled (String)              /mixer/state
                               /tf, /tf_static
```

---

## Key Dependencies

### Custom packages (in this workspace)

| Package | Description |
|---|---|
| `qcar2_interfaces` | Custom message definitions (`MotorCommands`, etc.) |
| `qcar2_nodes` / `qcar2_nodex` | QCar2 hardware driver nodes |
| `qcar2_mixer` | Hybrid planner / mixer (included via launch) |
| `qcar2_object_detections` | Detection message types & nodes |
| `qcar2_laneseg_acc` | Lane-segmentation pipeline |

### Isaac ROS packages

| Package | Description |
|---|---|
| `isaac_ros_yolov8` | YOLOv8 inference node |
| `isaac_ros_tensor_rt` | TensorRT inference backend |
| `isaac_ros_dnn_image_encoder` | DNN image encoder |

### Standard ROS 2 packages

`nav2_bringup`, `nav2_amcl`, `cartographer_ros`, `tf2_ros`, `cv_bridge`, `grid_map_msgs`, `image_transport`, `message_filters`, among others.

---

## Prerequisites

| Requirement | Install / verify |
|---|---|
| **ROS 2 Humble** | `source /opt/ros/humble/setup.bash` |
| **colcon** | `sudo apt install python3-colcon-common-extensions` |
| **rosdep** | `sudo apt install python3-rosdep && sudo rosdep init && rosdep update` |
| **System libraries** | `sudo apt install python3-opencv python3-numpy libopencv-dev` |
| **NVIDIA Isaac ROS** | Isaac ROS packages must be installed or present in the workspace |

---

## Getting Started

### 1. Create a ROS 2 workspace

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
```

### 2. Clone the repository

Clone this repository into the `src` folder of the workspace:

```bash
cd ~/ros2_ws/src
git clone <REPOSITORY_URL> .
```

> **Note:** The trailing dot (`.`) clones the contents directly into `src/` without creating an extra subfolder. If the repository only contains the `qcar2_behavior_tree` package, omit the dot.

### 3. Install ROS 2 dependencies

```bash
cd ~/ros2_ws
sudo apt update
rosdep install --from-paths src --ignore-src -r -y
```

### 4. Build with `colcon build --packages-up-to`

Use the `--packages-up-to` flag to build **only** `qcar2_behavior_tree` and every package it depends on, skipping unrelated packages in the workspace:

```bash
cd ~/ros2_ws
colcon build --packages-up-to qcar2_behavior_tree
```

This will resolve and build the full dependency chain automatically:

```
qcar2_interfaces ─► qcar2_nodes ─► qcar2_nodex ─► qcar2_mixer ─┐
qcar2_object_detections ─► qcar2_laneseg_acc ────────────────────┤
                                                                  ▼
                                                   qcar2_behavior_tree
```

> **Why `--packages-up-to`?** In large workspaces with dozens of packages, this flag avoids wasting time compiling packages that are not part of the dependency tree, while still ensuring every required package is built in the correct order.

### 5. Source the workspace

```bash
source ~/ros2_ws/install/setup.bash
```

> **Tip:** Add this line to your `~/.bashrc` so it runs automatically in every new terminal session.

---

## Running

### Launch the full stack

```bash
ros2 launch qcar2_behavior_tree qcar2_behavior_tree_mother.launch.py
```

This single command starts:

1. **`qcar2_hybrid_planner.launch.py`** from `qcar2_mixer` — brings up the hybrid planner with its default configuration.
2. **`qcar2_behavior_tree_manager`** — the BT node that orchestrates the mission.

### Use a custom configuration file

```bash
ros2 launch qcar2_behavior_tree qcar2_behavior_tree_mother.launch.py \
  bt_config:=/absolute/path/to/your/behavior_tree.yaml
```

---

## Configuration (`behavior_tree.yaml`)

The default configuration file is located at `qcar2_behavior_tree/config/behavior_tree.yaml`:

```yaml
qcar2_behavior_tree_manager:
  ros__parameters:
    tick_hz: 5.0                    # BT tick frequency (Hz)
    require_tf: true                # Wait for TF chain map→odom→base_link
    goal_reached_distance: 0.35     # Goal proximity threshold (meters)
    goal_timeout_sec: 900.0         # Per-goal timeout (seconds)
    goal_frame_id: map

    # Navigation goals [x, y, yaw]
    goal_1: [-1.75, 5.16, 0.0]
    goal_2: [-0.75, 1.64, 0.0]
    goal_3: [1.155, 4.433, 0.0]
    goal_4: [0.0, 0.0, 0.0]
    additional_goals: []            # Optional extra goals

    # Driving mode topic configuration
    default_mode_hybrid: HYBRID
    mode_code_stop: 0.0
    mode_code_hybrid: 1.0
    mode_code_pid: 2.0

    # Mission sequence — executed top-to-bottom, then loops
    mission_loop:
      - set_mode:HYBRID
      - set_led:init
      - wait:3.0
      - set_led:to_pickup
      - dispatch_next_goal
      - wait_goal_reached_or_timeout
      - wait:5.0
      - set_led:pickup_done
      - dispatch_next_goal
      - wait_goal_reached_or_timeout
      - set_led:dropoff_done
      - wait:5.0
      - set_mode:STOPPED
```

### Available `mission_loop` commands

| Command | Description |
|---|---|
| `set_mode:<MODE>` | Switch driving mode. Supported: `HYBRID`, `LANE_PID`, `LANE_ONLY`, `NAV2_TURN`, `NAV2_FORCED`, `STOPPED` |
| `set_led:<command>` | Publish an LED command string to the `/btled` topic |
| `wait:<seconds>` | Pause mission execution for the given number of seconds |
| `dispatch_next_goal` | Publish the next goal in the list as a `PoseStamped` |
| `wait_goal_reached_or_timeout` | Block until the robot reaches the current goal or the timeout expires |

### Driving modes

| Mode | Numeric code | Behavior |
|---|---|---|
| `HYBRID` | 1.0 | Combined lane-following + Nav2 navigation |
| `LANE_PID` | 2.0 | Lane-following PID only |
| `LANE_ONLY` | 2.0 | Lane-following only (alias) |
| `NAV2_TURN` | 1.0 | Nav2-driven turning maneuver |
| `NAV2_FORCED` | 1.0 | Force Nav2 path following |
| `STOPPED` | 0.0 | Motors stopped |

---

## ROS 2 Interface

### Published topics

| Topic | Type | Description |
|---|---|---|
| `/bt/goal` | `geometry_msgs/PoseStamped` | Current navigation goal |
| `/bt/state` | `std_msgs/String` | BT runtime state (e.g., `GOAL_DISPATCHED`, `GOAL_REACHED`, `WAITING_TF_CHAIN`) |
| `/bt/mode_hybrid` | `std_msgs/String` | Current driving mode (text) |
| `/bt/mode_hybrid_numeric` | `std_msgs/Float32` | Current driving mode (numeric code) |
| `/btled` | `std_msgs/String` | LED command for `led_sequence_node` |

### Subscribed topics

| Topic | Type | Description |
|---|---|---|
| `/detections/person` | `PersonDetection` | Person detection flag |
| `/detections/stop_sign` | `StopSignDetection` | Stop sign detection flag |
| `/detections/traffic_light` | `TrafficLightDetection` | Traffic light detection + state |
| `/detections/zebra_crossing` | `ZebraCrossingDetection` | Zebra crossing detection flag |
| `/mixer/state` | `std_msgs/String` | Hybrid mixer state feedback |
| `/qcar2_motor_speed_cmd` | `MotorCommands` | Motor command feedback |
| `/tf`, `/tf_static` | `tf2_msgs/TFMessage` | TF transforms for localization |

### Parameters (set via YAML)

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tick_hz` | `float` | `5.0` | BT tick rate in Hz |
| `require_tf` | `bool` | `true` | Block mission until full TF chain is available |
| `goal_reached_distance` | `float` | `0.35` | Distance threshold to consider a goal reached (m) |
| `goal_timeout_sec` | `float` | `900.0` | Max seconds to wait per goal before skipping |
| `goal_frame_id` | `string` | `map` | Frame ID for published goal poses |
| `default_mode_hybrid` | `string` | `HYBRID` | Initial driving mode on startup |
| `goal_1` … `goal_4` | `float[]` | — | Navigation waypoints as `[x, y, yaw]` |
| `additional_goals` | `float[][]` | `[]` | Optional extra waypoints |
| `mission_loop` | `string[]` | — | Ordered list of mission step commands |

---

## Package Structure

```
qcar2_behavior_tree/
├── config/
│   └── behavior_tree.yaml               # Mission configuration
├── launch/
│   └── qcar2_behavior_tree_mother.launch.py  # Main launch file
├── qcar2_behavior_tree/
│   ├── __init__.py
│   ├── behavior_tree_manager_node.py     # BT manager ROS 2 node
│   └── bt_nodes.py                       # BT primitives (Sequence, Selector, Wait, Action, Condition…)
├── resource/
│   └── qcar2_behavior_tree              # ament resource index marker
├── test/
│   ├── test_copyright.py
│   ├── test_flake8.py
│   └── test_pep257.py
├── package.xml
├── setup.cfg
└── setup.py
```

---

## Troubleshooting

| Symptom | Probable cause | Fix |
|---|---|---|
| `WAITING_TF_CHAIN map->odom->base_link` stays forever | SLAM / localization not running | Launch Cartographer or AMCL first, or set `require_tf: false` in the YAML |
| BT ticks but no goals are dispatched | Empty or malformed goal parameters | Verify `goal_1` … `goal_4` are valid `[x, y, yaw]` lists in the YAML |
| `qcar2_object_detections msgs not available` warning | Detection package not built | Rebuild with `colcon build --packages-up-to qcar2_behavior_tree` |
| `qcar2_interfaces msgs not available` warning | Interfaces package not built | Same as above — ensure `qcar2_interfaces` is in `src/` |
| Goal reached immediately | `goal_reached_distance` too large | Lower the threshold in the YAML (default `0.35` m) |

---

## License

Apache-2.0

---

**Team Seeker UCB** — Universidad Católica Boliviana "San Pablo" — Eduardo Vargas · Brayan Duran · Leyla Lipa · Mariel Valeriano
