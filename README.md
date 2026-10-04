# WWW-POSIM Autonomy Template

[한국어](README.ko.md) · [Class syllabus and labs](docs/course.md) · [Competition rules](docs/scoring.md)

A student-owned ROS 2 autonomy project for the **World Wide Web Platform for Ocean Simulation**. Click **Use this template → Create a new repository** on GitHub. Keep your controller in your own repository; the simulator and POSIM remain independent dependencies.

The starter contains a real LaserScan → occupancy map → A* → bounded body-velocity surface example, a small six-thruster underwater depth controller, a read-only telemetry / explicit command relay, and a licensed local-runtime launcher. The samples are starting points, not full-score solutions. Use AI, but test its code and explain your decisions.

Linux/macOS installer: `sh install.sh` (set `WWW_POSIM_PYTHON` if needed). Windows PowerShell: `./install.ps1`. These install the small Python starter/launcher; the ROS/Gazebo runtime is a separately cached Docker image.

## Quick start

Requirements: Python 3.10+, Git, and either a sourced ROS 2 installation or the instructor-provided Docker runtime (ROS 2 Lyrical / Gazebo Jetty). ROS `rclpy` is supplied by ROS, not by pip.

```bash
git clone https://github.com/YOUR_ACCOUNT/YOUR_CLASS_PROJECT.git
cd YOUR_CLASS_PROJECT
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
pip install -e .
```

On Ubuntu with native ROS, first source `/opt/ros/lyrical/setup.bash`. On Mac or Windows use the ROS terminal in the simulator container. [Detailed operating-system setup](docs/course.md#installation) includes the Docker workflow, WSL2, CPU/GPU differences and troubleshooting.

## Web-server controls

Register with your **email address** on the WWW-POSIM server and verify it. Choose WAM-V or BlueROV2, **ROS2 direct control**, a course and **Start world**. Once ready:

```bash
export ROS_DOMAIN_ID=73
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
www-posim-connect --server https://YOUR_SERVER/api --email YOU@example.edu --control
# another terminal, same ROS domain
www-posim-surface
# or, in a BlueROV2 session:
www-posim-underwater --depth 2
```

For localhost testing use `http://127.0.0.1:3000/api`. The connection uses authenticated HTTPS/WSS; an SSH tunnel is optional. Passwords are prompted, never command-line arguments. The helper downloads a fresh `profile.json`. Login is prompted once; a short-lived cookie reaches the relay through private standard input and is not persisted.

The surface starter solves the original **two-buoy practice example**, not all competition tasks. Extend it to read the course targets from `profile.json` and to maintain position/heading, identify markers, route around obstacles and return safely. Underwater force allocation is explicitly documented and bounded; start with depth holding before adding horizontal movement.

## One-button official evaluation

Open **WWW-POSIM Evaluation** (`www-posim evaluation`), choose your local project, command and task, then select **Evaluate on server**. Your algorithm runs on your PC; the server provides native Gazebo sensors and stores the score. Queue admission, ROS relay, scoring start, result export and cleanup run together. **Practice locally** uses your licensed installed simulator. [GUI, CLI, scoring trust and installer status](docs/evaluation.md).

## Installed standalone simulator

```bash
www-posim --server https://YOUR_SERVER/api --email YOU@example.edu \
  --runtime-image INSTRUCTOR_RUNTIME_IMAGE --web-image INSTRUCTOR_WEB_IMAGE
```

Open `http://127.0.0.1:3300`. Keep the launcher running. It stops the local simulator on logout, expired permission, quota exhaustion or loss of its server lease. Idle world preparation does not start a lease; launching a native world does. Initial renderer warm-up counts in the local lease. Repeated local runs can request a faster simulation target; achieved speed depends on CPU, GPU and sensors.

**Release status:** the thin installer and Compose application are provided. The current simulator images are built locally on ARM64; publicly downloadable AMD64/ARM64 runtime releases are not yet published. Ask the instructor for images, or build the simulator repository. Do not interpret a source download as a validated Windows/Linux GPU release. Docker caches unchanged layers for later updates.

Defaults: installed simulator **3 wall-hours/day**; web server **1 wall-hour/day**, **two isolated slots**, initially five admitted web members. Daily limits reset at 00:00 UTC. Class coupons or operator approval can grant **standalone-only unlimited use** for six calendar months or a specified semester. Web access is separate. License leases are 60 seconds, refreshed every 20 seconds; only one installed run per account. This open-source client is not tamper-proof DRM. Only server-measured, approved course runs count for the public leaderboard.

## ROS interface

| Direction | Topic | Type | Meaning |
|---|---|---|---|
| Receive | `/model/wamv/odometry` | `nav_msgs/msg/Odometry` | Simulated pose/velocity, ENU world |
| Receive | `/model/wamv/scan` | `sensor_msgs/msg/LaserScan` | Actual Gazebo lidar, including waves/land |
| Receive | `/model/bluerov2/odometry` | `nav_msgs/msg/Odometry` | Underwater pose/velocity |
| Receive | `/model/{robot}/imu` | `sensor_msgs/msg/Imu` | Native inertial sensor |
| Receive | `/clock`, `/tf`, `/tf_static` | Standard ROS types | Simulation time/transforms |
| Send | `/wwos/cmd_vel` | `geometry_msgs/msg/TwistStamped` | WAM-V body X speed and Z yaw rate |
| Send | `/wwos/thrusters` | `std_msgs/msg/Float64MultiArray` | WAM-V 2 or BlueROV2 6 forces, newtons |

Only the command topics are forwarded through `/control`. `/ros` remains read-only; arbitrary publishes/services/actions, server shell access and pose teleportation are not allowed. Commands need a current session nonce, controller lease and increasing sequence. A **0.75s wall-time watchdog** returns propulsion to zero on stale commands; inertia and waves still move a vehicle. Browser Stop latches propulsion off until Enable. Multiple students never share one native world or ROS domain.

Use `ros2 topic echo /model/wamv/scan`, RViz2 locally, and `ros2 bag record` for debugging. The profile also includes `/model/{robot}/camera/compressed` and the BlueROV2 inspection camera as `sensor_msgs/msg/CompressedImage` (JPEG, up to 1Hz simulation time). These are native sensor pixels; inspection applies the documented RGBD underwater shader. RViz Image can subscribe to the compressed transport. Raw Image, PointCloud2 and sonar are not promised by this default profile. No sonar, acoustic pinger or COLREG implementation is claimed. Official evaluation uses the fixed Busan example, a surface spawn at 35.07446 N / 129.08468 E, 1× speed and 10ms physics; practice regions remain user-selectable.

## Files to study

| File | Responsibility |
|---|---|
| `www_posim_autonomy/buoy_avoidance.py` | ROS callbacks, lidar projection, planning and 10Hz control |
| `planner.py` | Inflated occupancy, A*, line-of-sight and steering |
| `underwater.py` | Small bounded depth controller using native odometry |
| `control_math.py` | Documented stock thruster allocation |
| `connect.py` | Account login and fresh profile download |
| `relay.py`, `control_client.py` | Local telemetry and approved remote commands |
| `standalone.py` | Version check, runtime lease and local Compose lifecycle |
| `docs/course.md` | Syllabus, six tasks, labs and troubleshooting |

Run `python -m unittest discover -s tests`. The pure tests need no Gazebo; they do not replace real robot/ROS integration tests. Never commit passwords, cookies, AIS keys, simulator administrator configuration or private evaluation data. GPL wave/simulator dependencies are not bundled into this MIT student source repository; retain their own licenses when distributing runtime images.

Developed at [IOES-Lab, KMOU](https://lab.wschoi.com). Simulator source: [IOES-Lab/WWW-POSIM](https://github.com/IOES-LAB/WWW-POSIM).

The installed launcher compares the runtime version, protocol, rule version and adapter content hash with the server before granting local operation, then rechecks every five minutes. An incompatible source/image update stops the local runtime; update between runs.

[Measured native acceptance, real baseline scores and release limits](docs/validation.md).

Current client is **0.2.2**, adding the Evaluation app; the minimum compatible legacy client remains 0.2.1. Updates reuse unchanged Docker layers.
