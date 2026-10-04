# Installed Evaluation and package delivery

[한국어](evaluation.ko.md) · [Rules](scoring.md) · [Course](course.md)

Use local simulation for repeated development. For an official result, the **algorithm remains on your PC**, while an exclusive server Gazebo world supplies sensors and records the score. No student source, arbitrary ROS package or executable is uploaded for server execution.

## One-button workflow

Open the installed **WWW-POSIM Evaluation** app (`www-posim evaluation`). Set the server API, email, public alias, task, project directory and a JSON command argument list. For example, `["python3", "my_controller.py"]` runs your file in the mounted project directory. Choose the instructor-provided client image for Mac/Windows, or leave it empty when running the Python/.deb client in a sourced native Linux ROS environment. Frozen Mac/Windows apps use the local client image. The client image contains ROS and the relay; it needs no GPU because the official simulator is on the server.

Select **Evaluate on server**. The app checks version compatibility, joins the existing FIFO queue, prepares the fixed course, downloads the current profile, waits for native odometry and propulsion, starts server scoring, then starts your local command. Waiting does not consume server runtime. It displays queue position and the next-slot estimate. At completion it saves `result.json`, `relay-report.json`, `relay.log` and `algorithm.log`, stops its own local processes and releases its own server slot. **Cancel** also stops the controller, saves `interrupted-result.json` when scoring already started, and releases the slot. An interrupted run cannot earn an official score. Keep the app open until cleanup completes.

The password is entered once per app action and is not saved in settings, command lines or result files. A short-lived cookie reaches the PC-local client/relay through private standard input. Your selected project and result folders are the only folders mounted into that client. ROS uses local domain 76 and local discovery; the server does not expose DDS.

CLI equivalent:

```sh
www-posim evaluate --server https://YOUR_SERVER/api --email YOU@example.edu \
  --task surface_station --alias MyTeam --project ./my_project \
  --client-image INSTRUCTOR_CLIENT_IMAGE --output ./evaluation-results \
  -- python3 my_controller.py
```

For native Linux or the sourced Apple Silicon app environment, load ROS and omit `--client-image`. The child process uses your local ROS Python. `--practice` uses an unverified practice course; **Practice locally** targets the running, licensed installed simulator at `http://127.0.0.1:3300/api`. It does not bypass the launcher or its usage lease.

## ROS control and scoring trust

The relay republishes actual server Odometry, LaserScan, IMU and compressed cameras as local ROS messages. Publish the allowlisted `/wwos/cmd_vel` or `/wwos/thrusters` topics from your algorithm. Authentication, nonce, exclusive controller lease, monotonic sequence, force bounds and the 0.75-second watchdog protect the command path. `/ros` is read-only; `/control` carries the bounded commands. Do not send pose changes or Gazebo commands.

Local scores/logs can be exported for feedback and reports. A native machine owner can change an open-source simulator, its clock or files; a signature/hash made by that same machine does **not** prove a fair run. Official standings therefore use **only native trajectories observed and stored by the server**. The JSON SHA-256 checks accidental file changes, not cheating. Exports are owner-scoped and remain downloadable by run ID after a server slot ends; exports contain no email address. Uploading a JSON score does not award ranking points. Wave/physics checks run throughout an official trial and changes invalidate it. The existing five-seed suite and real Autopilot baseline still apply.

## Install and update

The Evaluation client and the simulator app are separate applications. Install this template's Python package with `python -m pip install .` from its checkout. The command `www-posim evaluation` opens its desktop interface; `www-posim evaluate` runs the same workflow from a terminal. Use the [simulator distribution](https://github.com/woensug-choi/homebrew-www-posim) for the Apple Silicon ROS/Gazebo/Metal engine and the [course installation guide](course.md#installation) for the other platforms.

On Apple Silicon, load the app's ROS environment before installing and running the Python Evaluation client:

```sh
eval "$(/Applications/WWW-POSIM.app/Contents/MacOS/WWW-POSIM --ros-env)"
python -m pip install /PATH/TO/WWW-POSIM-Autonomy-Template
www-posim evaluate --server https://YOUR_SERVER/api --email YOU@example.edu \
  --task surface_station --alias MyTeam --project ./my_project \
  --output ./evaluation-results -- python my_controller.py
```

Omit `--client-image` when this sourced ROS Python is used. The separately frozen Evaluation desktop client uses the instructor's ROS container because its embedded Python does not contain ROS. Neither client mode runs the official simulator on the student's PC.

The client checks versions before execution and every five minutes during a run. Update between runs. Version 0.2.2 includes the Evaluation app and CLI; the server also checks the protocol and scoring-rule version. Runtime dependencies and robot assets are reused until their version changes.
