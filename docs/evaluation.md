# Installed Evaluation and package delivery

[한국어](evaluation.ko.md) · [Rules](scoring.md) · [Course](course.md)

Use local simulation for repeated development. For an official result, the **algorithm remains on your PC**, while an exclusive server Gazebo world supplies sensors and records the score. No student source, arbitrary ROS package or executable is uploaded for server execution.

## One-button workflow

Open the installed **WWW-POSIM Evaluation** app (`www-posim evaluation`). Set the server API, email, public alias, task, project directory and a JSON command argument list. For example, `["python3", "my_controller.py"]` runs your file in the mounted project directory. Choose the instructor-provided client image for Mac/Windows, or leave it empty when running the Python/.deb client in a sourced native Linux ROS environment. Frozen Mac/Windows apps use the local client image. The client image contains ROS and the relay; it needs no GPU because the official simulator is on the server.

Select **Evaluate on server**. The app checks version compatibility, joins the existing FIFO queue, prepares the fixed course, downloads the current profile, waits for native odometry and propulsion, starts server scoring, then starts your local command. Waiting does not consume server runtime. It displays queue position and the next-slot estimate. At completion it saves `result.json`, `relay-report.json`, `relay.log` and `algorithm.log`, stops its own local processes and releases its own server slot. **Cancel** also stops the controller, saves `interrupted-result.json` when scoring already started, and releases the slot. An interrupted run cannot earn an official score. Keep the app open until cleanup completes.

The password is entered once per app action and is not saved in settings, command lines or result files. A short-lived cookie reaches the PC-local client/relay through private standard input. Your selected project and result folders are the only folders mounted into that client. ROS uses local domain 73 and local discovery; the server does not expose DDS.

CLI equivalent:

```sh
www-posim evaluate --server https://YOUR_SERVER/api --email YOU@example.edu \
  --task surface_station --alias MyTeam --project ./my_project \
  --client-image INSTRUCTOR_CLIENT_IMAGE --output ./evaluation-results \
  -- python3 my_controller.py
```

For native Linux, source ROS and omit `--client-image`. The child process uses your local ROS Python. `--practice` uses an unverified practice course; **Practice locally** targets the running, licensed installed simulator at `http://127.0.0.1:3300/api`. It does not bypass the launcher or its usage lease.

## ROS control and scoring trust

The relay republishes actual server Odometry, LaserScan, IMU and compressed cameras as local ROS messages. Publish the allowlisted `/wwos/cmd_vel` or `/wwos/thrusters` topics from your algorithm. Authentication, nonce, exclusive controller lease, monotonic sequence, force bounds and the 0.75-second watchdog protect the command path. `/ros` is read-only; `/control` carries the bounded commands. Do not send pose changes or Gazebo commands.

Local scores/logs can be exported for feedback and reports. A native machine owner can change an open-source simulator, its clock or files; a signature/hash made by that same machine does **not** prove a fair run. Official standings therefore use **only native trajectories observed and stored by the server**. The JSON SHA-256 checks accidental file changes, not cheating. Exports are owner-scoped and remain downloadable by run ID after a server slot ends; exports contain no email address. Uploading a JSON score does not award ranking points. Wave/physics checks run throughout an official trial and changes invalidate it. The existing five-seed suite and real Autopilot baseline still apply.

## Installer status

Target-OS [installer CI](https://github.com/IOES-Lab/WWW-POSIM-Autonomy-Template/actions/runs/37191524725) completed successfully for Linux, macOS and Windows. Each frozen client passed `--version`; Windows also created the Inno Setup `.exe`, and Linux created the `.deb`. Download the job artifacts while retained by GitHub. These are client builds; they do not prove that the full simulator engine or GUI installation works on every target.

| Artifact | Contents | Verified here |
|---|---|---|
| Python wheel | Starter, launcher, Evaluation GUI and CLI | Built at 0.2.2; pure unit tests |
| Mac ARM64 `.app` archive | Frozen Python/Tk client, about 12 MB compressed | Build and CLI version succeeded; native app screen inspection blocked by a locked Mac |
| Debian `.deb` | Python client plus desktop entry, system dependencies | Built, extracted and version checked in Ubuntu container; not a full native engine installer |
| Homebrew Cask | SHA-256-pinned Mac app archive | Generated for local archive; public URL requires publishing the identical archive |
| Windows installer `.exe` | Frozen client wrapped with Inno Setup | Windows CI built the `.exe` and passed CLI version smoke test; GUI installation and native GPU engine not yet tested |
| Simulator / client OCI images | Gazebo/ROS/POSIM/waves, or ROS controller client | ARM64 local builds retained; matching public AMD64/ARM64 releases are still required |

Build with `python tools/build_installer.py wheel`, `desktop`, or `deb`. Desktop builds must run on their target OS; [PyInstaller is not a cross-compiler](https://pyinstaller.org/en/latest/). `packaging/windows.iss` wraps the Windows result, and `.github/workflows/installers.yml` builds target-OS artifacts without automatically publishing a release. Render a local Cask with:

```sh
python tools/homebrew_cask.py --archive dist/WWW-POSIM-Evaluation.app-0.2.2-darwin-arm64.tar.gz \
  --output .local/www-posim.rb
# After publishing the identical archive, also pass --url https://.../archive.tar.gz
```

The client and simulator engine are separate deliveries. For native engine distribution, validate Linux first, then package POSIM, the independently licensed wave dependency, ROS/Gazebo and assets with their licenses intact. ROS Lyrical's [official platform table](https://github.com/ros2/ros2_documentation/blob/rolling/source/Get-Started/Releases/lyrical/supported-platforms.rst) governs the native target. Gazebo's [Mac installation](https://gazebosim.org/docs/latest/install_osx/) alone does not prove the full ROS/POSIM plugin stack works on Mac; its [Windows Jetty installation remains experimental](https://gazebosim.org/docs/latest/install_windows/). Docker remains the tested engine path here. [Docker Desktop GPU support](https://docs.docker.com/desktop/features/gpu/) does not expose Apple's GPU to this Gazebo container; Linux NVIDIA/Windows WSL2 GPU paths need real hardware validation.

Version checks occur before local execution and every five minutes during it. Update between runs. Small client/adapter changes reuse unchanged large Docker layers; a complete dependency/model revision can still require a large download. Client 0.2.2 adds Evaluation; minimum compatible legacy client remains 0.2.1. A public release needs checksums, matching runtime/client images, signed/notarized installers where applicable, HTTPS/SMTP deployment and target-OS acceptance tests. Local build artifacts are not presented as a finished public release.
