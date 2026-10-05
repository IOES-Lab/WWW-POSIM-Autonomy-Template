# Maritime autonomy laboratory — syllabus and student handbook

[한국어](course.ko.md) · [Scoring specification](scoring.md) · [Template](../README.md)

**Platform:** WWW-POSIM, ROS 2 Lyrical, Gazebo Jetty, optional ArduPilot. **Audience:** undergraduate/graduate students who can write basic Python. **Format:** 12 weeks, one 2-hour lesson and one 2-hour lab each week; teams of 1–3. A surface or underwater track is sufficient for course credit; both tracks are optional. This is an educational competition inspired by existing events, not an official RobotX, VRX or RoboSub qualifying event.

## Learning objectives

By the end students can build a ROS feedback controller; explain ENU/body coordinates and simulation versus wall time; inspect actual sensor messages; plan collision-aware routes; handle stale telemetry and emergency stops; compare a measured default Autopilot baseline; measure robustness over multiple courses; and reproduce an experiment with versioned source, parameters and logs. Students must distinguish a visual effect, a modeled sensor and a validated physical behavior.

AI assistants are permitted for implementation, debugging and writing. Each submission must include an AI-use record, a short explanation of the control/perception/planning loop, at least one failed trial and its fix, and a reproducible test command. Teams remain responsible for unsupported claims and unsafe code. Long-term difficulty comes from continuous precision scores, several wave/course conditions and safety, not obscure API syntax or forbidding AI.

## Weekly syllabus

| Week | Lesson | Lab / deliverable |
|---|---|---|
| 1 | Maritime autonomy; simulator architecture; safety | Email registration, template repository, first ROS echo and Stop test |
| 2 | ROS messages, QoS, frames, clocks | Receive odometry/IMU; record a bag; plot pose and sensor age |
| 3 | Vehicle dynamics and force allocation | WAM-V speed/yaw or BlueROV2 depth controller; explain signs/units |
| 4 | Position/depth/heading feedback | Task 1; steady error and overshoot report under rough waves |
| 5 | Lidar/camera geometry and measurement limits | WAM-V ray projection or underwater marker observation; do not use hidden poses for obstacle detection |
| 6 | Occupancy maps, inflation, A* | Two-buoy example; correct clearance and a return trip |
| 7 | Ordered gates/inspection path | Task 2; sequence state machine and failure recovery |
| 8 | Robustness and stale data | Disconnect the relay; test watchdog/Stop; quantify effects of rate changes |
| 9 | Obstacle course / return / surfacing | Task 3; keep actual collision geometry and depth clearance |
| 10 | Experiment design and scalability | Five practice seeds; compare ArduPilot defaults; measure achieved RTF |
| 11 | Reproducible evaluation | Official server runs, public alias, leaderboard and parameter/source version |
| 12 | Final demonstration and review | Re-run a randomly selected course, explain failure cases and present evidence |

Course assessment: six ROS/safety labs 30%, three chosen-track tasks 30% (10% each, based on the documented simulator score), final reproducibility report 25%, design explanation/demo 15%. An unsafe or unrepeatable run is not rescued by a high leaderboard score. An instructor can adjust academic weights without changing the versioned simulator scoring rules.

## Architecture and safety

The browser submits latitude/longitude, robot and world settings. Terrain processing builds measured seafloor/land collision meshes. A server slot runs its own Gazebo, ROS bridge and optional SITL; the browser draws a view from native state and wave samples. In direct mode the student's Python code receives sensors and emits ROS commands; no Autopilot is launched. In Autopilot mode MAVROS and ArduPilot control propulsion instead. Never run both authorities together.

Web telemetry travels over a read-only rosbridge gateway; approved propulsion commands travel over a separate authenticated `/control` WebSocket. A relay republishes telemetry in the student's local ROS domain and listens for their command topics. There is no publicly exposed DDS multicast, per-user server SSH account or arbitrary service invocation. HTTPS/WSS is sufficient for an internet deployment; SSH forwarding is an optional private deployment tool.

The command watchdog uses **wall time** because network failures must not become harmless merely by pausing simulation time. Use 10Hz commands, reject odometry older than 0.5s, and send neutral on shutdown. Server freshness, force/speed limits, session nonce and exclusive control lease remain mandatory. Zero thrust is not a guaranteed stationary vehicle: inertia, gravity and waves remain. Stop latches off; Enable requires a ready direct-mode world.

## Installation

### Account and class entitlement

Register using an email address and a password of at least 12 characters. Verify the email through Account → Send verification code → Verify email. Production email delivery requires the operator's SMTP configuration; if it is not configured, the UI reports this and an operator must verify the address. A merely typed university domain never grants unlimited use.

Default local quota is 3 wall-hours/day; web quota is 1 wall-hour/day. UTC midnight resets daily accounting. Web access is initially admitted to five members and two independent worlds can run simultaneously. A busy slot shows its current deadline estimate; you can queue, return later, or use local practice. Earlier release/startup/cleanup can change that estimate. Waiting is not running time.

Account → Request more usage collects affiliation, status, estimated total hours, optional class/invitation code, purpose and requested period. An operator can approve standalone Pro starting immediately for six calendar months, or use a dated semester coupon. Pro never automatically increases web quota. One installed session per account prevents parallel devices multiplying the allowance. The open-source local client is not secure DRM; a modified local report cannot become an official leaderboard score.

### Choose an operating-system path

| System | Supported installation approach | GPU reality |
|---|---|---|
| Linux | Docker Engine, instructor-provided native AMD64/ARM64 runtime; native ROS optional | NVIDIA driver + Container Toolkit + `--gpu`; confirm EGL actually uses NVIDIA |
| Windows PC | Docker Desktop with WSL2; launch Python/controller from an Ubuntu WSL terminal | Supported NVIDIA GPU passthrough path; actual graphics/EGL and sensor validation still required |
| Apple Silicon Mac · macOS 27+ | Native WWW-POSIM DMG/Homebrew app; bundled ROS environment | Gazebo Metal rendering on the Mac GPU |

For Apple Silicon, install the native simulator app from [the public Homebrew/DMG distribution](https://github.com/woensug-choi/homebrew-www-posim). Open the app, sign in and prepare a ROS 2 direct-control world. In every controller terminal run:

```sh
eval "$(/Applications/WWW-POSIM.app/Contents/MacOS/WWW-POSIM --ros-env)"
```

Create the student virtual environment with this bundled Python and `--system-site-packages`, then install your template project with `pip install -e .`. The following Docker setup is for Linux and Windows. Ubuntu host ROS commands apply after sourcing the matching installation.

1. Install Docker from its official vendor/distribution instructions and Python 3.10 or newer. On Windows enable WSL2 and use an Ubuntu terminal. Allocate at least 8GB to the Docker VM for this example, preferably 12GB on a machine with 24GB+ RAM. Close unrelated heavy builds while measuring.
2. On GitHub choose **Use this template → Create a new repository**, clone your copy and `cd` into it.
3. `python3 -m venv --system-site-packages .venv`; activate it; `pip install -e .`.
4. Obtain architecture-matching runtime/web image tags from the instructor. The image version must match the class server; retain its upstream dependency source and license notices. Do not use CPU-emulated ARM on an x86 GPU server as a performance benchmark.
5. Run:

```bash
www-posim --server https://YOUR_SERVER/api --email YOU@example.edu \
  --runtime-image INSTRUCTOR_NATIVE_RUNTIME --web-image INSTRUCTOR_WEB_IMAGE
# Linux/Windows NVIDIA, after driver/toolkit/EGL validation:
www-posim --server https://YOUR_SERVER/api --email YOU@example.edu \
  --runtime-image INSTRUCTOR_NATIVE_RUNTIME --web-image INSTRUCTOR_WEB_IMAGE --gpu
```

Open `http://127.0.0.1:3300`. Keep the launcher running; Ctrl+C ends the lease and stops Compose. Data and downloaded terrain remain in `~/.www-posim/data`. The launcher holds a random device ID, not the password. Local ROS/Gazebo/web dependencies live in cached image layers. Server lease renewal is 20s, expiry 60s; renewal/connection failures stop the local runtime. Initial native startup and camera warm-up count in this local lease; idle preparation and queue time do not.

The initial images are large because ROS, rendering, GIS, simulator and SITL are included. Later releases should retain dependency layers and update small versioned Python/web layers. The client checks compatibility before running and every five minutes. An incompatible protocol/minimum version requires an update between runs. Image tags/release checksums must come from the operator; the launcher does not execute arbitrary update URLs. The simulator package is installed separately from these student tools; the account server renews its running-time permission.

### ROS terminal without native ROS installation

Linux and Windows can run student code inside a separate local ROS terminal container; Apple Silicon uses the bundled native environment. For the container workflow, use the same instructor runtime image. Mount only your template project, choose a different ROS domain, and connect through the local or remote gateway:

```bash
docker run --rm -it --cpus 1 --memory 1g \
  -e ROS_DOMAIN_ID=76 -e ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST \
  -v "$PWD:/student" -w /student --entrypoint bash INSTRUCTOR_NATIVE_RUNTIME
source /opt/ros/lyrical/setup.bash
python3 -m venv --system-site-packages /tmp/student-env
. /tmp/student-env/bin/activate
pip install -e .
```

On Linux add `--add-host host.docker.internal:host-gateway` when the simulator/SSH tunnel is on the host. Inside this container use `http://host.docker.internal:3300/api` for local controls, or the real HTTPS server. The Docker loopback is the container itself, so `127.0.0.1` will not reach a host browser server. Run a second terminal in the **same client container** via `docker exec -it CONTAINER_ID bash`, source ROS and activate `/tmp/student-env`; this lets your node communicate with the relay. Separate `docker run` invocations with LOCALHOST discovery do not automatically share ROS discovery.

## Lab A — native messages, units and a safe command

In an active WAM-V direct-control world download `/api/rviz/profile` or use `www-posim-connect`. Inspect:

```bash
ros2 topic list -t
ros2 topic echo /model/wamv/odometry --once
ros2 topic echo /model/wamv/scan --once
ros2 topic hz /model/wamv/scan
```

Odometry position is world ENU: +X east, +Y north, +Z up. Quaternion yaw 0 faces east; compass labels are derived separately. The command's `header.frame_id` is **base_link**. Body X is forward and positive angular Z turns counterclockwise viewed from above. WAM-V command bounds are X ±1.5m/s and Z ±0.5rad/s. Sideways/vertical speeds are not accepted. Force bounds are ±200N for two WAM-V thrusters and ±50N for six BlueROV2 thrusters; the supplied underwater starter uses a smaller ±20N clamp.

```bash
ros2 topic pub -r 10 /wwos/cmd_vel geometry_msgs/msg/TwistStamped \
  '{header: {frame_id: base_link}, twist: {linear: {x: 0.25}, angular: {z: 0.0}}}'
```

Send only in a clear-water practice world, watch motion, then Ctrl+C. Confirm commands become stale and propulsion reaches zero after the watchdog. Do not test this in a scored gate course before starting scoring. Record the observed response, not just the command publication.

## Lab B — server controls from a student's own computer

1. Log into the browser; select robot, ROS2 mode, optional two-buoy example; start and wait for live sensors.
2. In the local ROS terminal:

```bash
www-posim-connect --server https://YOUR_SERVER/api --email YOU@example.edu --control
# second terminal, same client ROS domain:
www-posim-surface --distance 38 --speed 0.8
```

3. Read the source. `receive_pose` stores measured state. `receive_scan` projects lidar rays using the measured quaternion and known sensor extrinsic `(0,0,2.5)`. Water returns below the simple height filter are rejected; this is a teaching heuristic, not a production maritime detector. Occupied cells are inflated by 4m, A* plans around them, and the steering loop publishes a fresh command at 10Hz. The sample does not receive obstacle coordinates or teleport the robot.
4. Disconnect the relay; verify neutral propulsion, reconnect, and test browser Stop/Enable. Document the difference between control timeout and position drift in waves.
5. Replace the hard-coded out-and-back goals with the public mission targets in `profile.json`. Add heading/hold-state logic for the competition. Topic names/session nonce must be downloaded again after restarting the world.

For a private server, an administrator-provided SSH account may forward its HTTPS gateway; this is not required by the application:

```bash
ssh -N -L 19090:127.0.0.1:3000 YOUR_EXISTING_SSH_ACCOUNT@SERVER
# API: http://127.0.0.1:19090/api; WebSocket: ws://127.0.0.1:19090/ros
```

The relay's Origin must match an operator-configured allowed origin. The project does not generate SSH accounts, unique user subdomain tunnels or Kubernetes/ngrok services. Public deployment needs ordinary TLS/DNS and a reviewed reverse proxy; cookie login assigns your API/WebSocket traffic to your own native worker.

## Lab C — installed simulator controls

Start the licensed local application, create terrain and a direct-mode world. Its loopback gateway has the same approved topic/command contracts. The local simulator's beta login is disabled because the launcher already authenticates with the central service; no server account is copied into the local runtime.

```bash
# Download the profile without central credentials from the local application:
curl http://127.0.0.1:3300/api/rviz/profile -o profile.json
# In a sourced ROS terminal:
python3 -m www_posim_autonomy.relay --url ws://127.0.0.1:3300/ros \
  --profile profile.json --control
# Inside a client container, substitute host.docker.internal for 127.0.0.1.
# Second terminal:
www-posim-underwater --depth 2
```

BlueROV2 command order is thrusters 1…6. The native joint axes are local −Z. Their horizontal rotations mean surge signs `[-,-,+,+]`, yaw signs `[-,+,+,-]`, and both vertical axes point down. The allocation helper converts a desired upward force to negative vertical thrust. Change inertia/thruster transforms in your SDF and you must re-derive this map. The starter holds depth for 45 simulation seconds then requests the surface; its simple PD loop is not a robust 6-DOF controller or a complete underwater slalom solution. Mission phases follow the received ROS odometry simulation timestamp, including accelerated runs; communications still use wall-age checks. Body-frame vertical velocity is transformed to ENU before depth damping.

Use RViz2 in a client with a supported display, `ros2 bag record /model/bluerov2/odometry /model/bluerov2/imu /wwos/thrusters`, and plots of depth error/force. The default profile currently provides odometry, IMU, TF and WAM-V lidar, not an invented underwater sonar. Camera data are available through the browser pane/API and the profile's `sensor_msgs/msg/CompressedImage` topics: `/model/bluerov2/camera/compressed`, `/model/bluerov2/inspection/image/compressed`, or `/model/wamv/camera/compressed`. JPEG transmission is capped at 1Hz simulation time and activates on subscription. Inspection uses the documented RGBD water shader. Decode `msg.data` with OpenCV or use RViz Image/Compressed transport. RAW Image, PointCloud2 and sonar require an additional reviewed sensor profile. Native autonomy can use further ROS packages in its local client container without installing unreviewed packages into the shared server.

## Official evaluation conditions

Official evaluation uses the fixed Busan example and starts at 35.07446 N / 129.08468 E on the sea surface, with fixed terrain, 10ms physics and 1× target speed. Practice remains user-selectable and can run faster locally. A changed official wave field or physics setting is rejected when scoring begins; environment controls are locked during a scored run. Restart a world before another official attempt. Rule `maritime-class-2` uses 13m-wide surface gates so the 3.5m hull proxy can earn the full 2m clearance bonus; underwater gates remain 10m wide. Earlier development records use a separate rules version.

## Six tasks

Every course starts in clear water, uses a 6m/s default wave field (seeded ±0.5m/s variation), offsets geometry by up to 3m and scales route distances by ±10%. Wind bearing is varied. These changes are implemented; stochastic currents, sensor dropout injection, pingers and moving obstacle behavior are not silently assumed.

| Track/task | Student objective | Geometry / timeout | Reference inspiration |
|---|---|---|---|
| Surface 1 | Reach a specified pose and hold 30s | Goal about 12m away; 120s | VRX Stationkeeping |
| Surface 2 | Three ordered gates then return | Three red/green pairs; nominal 12/26/40m; 240s | RobotX channel navigation, VRX Wayfinding |
| Surface 3 | Route around obstacles then hold at home berth | Four posts, alternating offset goals, 10s final hold; 300s | RobotX Follow the Path; simplified docking position hold |
| Underwater 1 | Dive to 2m, pass a gate, hold 15s | Two underwater posts and a goal; 180s | RoboSub gate |
| Underwater 2 | Follow an inspection route at 3m depth then return | Three orange seabed markers; 240s | RoboSub path-marker navigation and WUURC pipeline inspection |
| Underwater 3 | Slalom at 2m, return through the gate and surface | Three submerged posts, gate and final surface goal; 300s | RoboSub Avoid Debris and Return Home |

The underwater path is marker inspection, not a simulated damaged pipe/sonar classifier. The berth task is position holding, not visual scan-code docking. RoboSub does not award points simply for following its path markers; **this class adds its own path score**. Gate width and scoring weights below are our teaching design. References establish real task families, not equivalence to their complete rules.

## Scoring and leaderboard

Detailed equations, tolerances and examples are in [scoring.md](scoring.md). Each task is 0–100: completion 60, precision 20, speed 10, safety clearance 10. Completion is ordered targets reached / total. Precision uses route cross-track or holding position RMS, yaw RMS and underwater depth RMS. Every hold must be consecutive within the arrival envelope. A hull-envelope obstacle overlap subtracts 15 per obstacle and caps the run at 50. Nonfinite data, teleportation, invalid time or session changes invalidate the run.

Navigation thresholds for full precision are demanding but nonzero: 0.15m position/cross-track RMS, 5° yaw RMS and 0.05m depth RMS. They are intentionally tighter than target-arrival envelopes (surface 2m, underwater 1m, depth 0.5m). Multiple different rough-wave layouts make copying one trajectory a weak strategy. Reaching 100 is mathematically possible; it requires meeting all precision, time and safety criteria across the suite. Score formulas must be revised/versioned if physical model limits make a threshold unattainable in testing; do not arbitrarily lower a student's measured score.

Practice allows chosen seeds 0…4. Official evaluation selects a common five-seed suite on the server from the versioned rule set, the same for all entrants. Each task's result is `0.8×mean + 0.2×minimum`; overall track score is the mean of its three tasks. Before five seeds, records are **provisional**. The leaderboard button on login and the main view explains entry and links this syllabus/template. It publishes aliases, never account email addresses. Server records include native trajectory, source condition/rules and parameter hash for baselines. Local source-controlled scores are practice-only.

The pinned ArduPilot rows are measured using the **included vehicle-default profiles**, including simulator navigation integration. They are not claimed to be untouched real-hardware factory EEPROM parameters. The operator starts a fresh Autopilot world without parameter edits and runs the same targets. That supplies a repeatable basic position/depth controller baseline; it does not give the Autopilot automatic semantic perception, underwater sonar or obstacle avoidance. ArduPilot Rover supports configured avoidance such as BendyRuler, but enabling sensors/avoidance changes this baseline. The parent terrain detour planner is not equivalent to lidar-based dynamic avoidance.

## Experiment report and debugging

Submit Git commit, platform/rules version, robot/SDF and parameter revisions, sensor rates, wave values, target speed and achieved RTF, each seed's score/trace, collision proxy, controller logs and a short actual camera/follow recording. Preserve failures and explain them. A simulation target of 3× is not proof that 3× was achieved. Faster-than-real-time runs disable live AIS ships because wall-clock AIS cannot accelerate with simulation time.

Common faults:

- No topics: check active world, profile nonce, relay cookie, allowed Origin, ROS_DOMAIN_ID and same client network namespace. LOCALHOST discovery in different containers does not connect itself.
- No thrust: choose direct mode, start the command relay with `--control`, Enable after Stop, check `base_link`, bounds and fresh odometry. Autopilot mode deliberately rejects direct commands.
- Vehicle dives the wrong way: verify thruster local axes and body/world transforms. Test one small pulse in clear water; do not guess force signs.
- Sky-only camera: choose the underwater inspection camera or correct the camera pose/range. A decorative browser sea surface is not sensor evidence.
- Poor score: ordered target/hold logic, cross-track/yaw/depth error and conservative hull clearance may differ from visual impressions. Read the native report.
- Server busy: read the estimated deadline, return later or practice locally. Class Pro does not reserve a web slot.
- Email not delivered: SMTP is an operator dependency. Do not accept a user-provided domain as proof of affiliation.
- GPU is idle: verify renderer/device, not only `nvidia-smi` availability. The native Apple Silicon app uses Metal; a Mac Docker engine uses software rendering. Profile CPU physics, renderer, sensor conversion and memory before buying hardware.

## Primary references

- [VRX 2023 Stationkeeping](https://github.com/osrf/vrx/wiki/vrx_2023-stationkeeping_task) and [Wayfinding](https://github.com/osrf/vrx/wiki/vrx_2023-wayfinding_task).
- [RobotX 2024 Team Handbook](https://robonation.org/app/uploads/sites/2/2024/09/2024-RobotX_Team-Handbook_v2.0.pdf), navigation demonstration and Follow the Path.
- [RoboSub task descriptions](https://robonation.gitbook.io/robosub-resources/section-3-autonomy-challenge/3.2-task-descriptions) and [scoring](https://robonation.gitbook.io/robosub-resources/section-4-scoring-and-awards/4.2-autonomy-challenge-scoring); the live handbook may change edition.
- [WUURC 2025 official rules](https://www.w2urc.org/static/upload/file/20250428/1745809633622443.pdf), pipeline inspection and return families.
- [ArduPilot Rover object avoidance](https://ardupilot.org/rover/docs/common-object-avoidance-landing-page.html).
- [Docker Windows/WSL2 GPU support](https://docs.docker.com/desktop/features/gpu/), [Gazebo macOS installation](https://gazebosim.org/docs/latest/install_osx/) and [Gazebo headless rendering](https://gazebosim.org/api/sim/10/headless_rendering.html).

Reference check: 2026-10-04. These resources inform our course design; WWW-POSIM rules and measurements determine this class's results.

The installed launcher compares the runtime version, protocol, rule version and adapter content hash with the server before granting local operation, then rechecks every five minutes. An incompatible source/image update stops the local runtime; update between runs.

## Measured acceptance and release status

Baseline scores and the five-seed ranking rules are described in [Scoring](scoring.md).

Minimum installed client: **0.2.1**. Previous 0.2.0 requires updating for the simulation-time and neutral-shutdown fixes. Compatibility is checked every five minutes; required updates stop execution and are applied between runs.

## Installed Evaluation lab

After improving your local controller, use the installed Evaluation app to select the task and local argument list, then Evaluate on server. The algorithm remains on your PC while the server Gazebo observes the official run. The app manages admission, relay, scoring and cleanup; it saves finished or interrupted diagnostic evidence. Read [the step-by-step GUI/CLI workflow and trust model](evaluation.md). Local JSON exports are practice evidence and cannot award public points.
