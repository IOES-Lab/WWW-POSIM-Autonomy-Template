# Scoring specification — maritime-class-1

This is the class's scoring system, not an official RobotX/VRX/RoboSub scoring table. Source of truth is the simulator's `competition_core.py`; a client cannot submit a claimed numeric score.

## One run

Let `c` be ordered targets reached divided by total targets, `e_p` the time-weighted RMS cross-track error (or full horizontal error during station holding), `e_h` the time-weighted yaw RMS in radians, `e_d` underwater depth RMS in metres (zero for surface), `t` elapsed simulation time, `T` task timeout and `I` ideal completion time.

```
completion = 60 c
precision  = 20 c exp(-max(0,e_p-0.15)/2
                     -max(0,e_h-5π/180)/0.5
                     -max(0,e_d-0.05)/0.5)
speed      = 10 c clamp((T-t)/(T-I), 0, 1)
safety     = 10 c clamp(minimum_hull_clearance / 2, 0, 1)
raw        = completion + precision + speed + safety - 15 × struck_obstacles
score      = clamp(raw, 0, 100)
```

With no obstacle geometry safety is `10c`. Hull envelopes are conservative 3.5m radius for WAM-V and 0.5m for BlueROV2, with vertical overlap against each cylinder. This is a documented geometry proxy, **not measured contact force**, and can penalize a near pass before exact mesh contact. The same proxy applies to all entrants. A collision caps the score at 50. Each obstacle is counted once per run. Land/seafloor collision force integration is not an additional invented scoring input; native terrain safety/motion checks can stop or invalidate the run.

Arrival envelopes: horizontal error <2m surface / <1m underwater, depth error <0.5m; a holding target additionally requires yaw error <0.35rad. Consecutive hold time resets on leaving its envelope. Ordered target arrival is used in the simplified gate task; arbitrary segment crossings are not yet a separate gate-plane detector. Stationkeeping precision measurement starts on first entry into the target envelope, so time spent approaching is counted for speed rather than as holding error. Route accuracy projects onto the current bounded segment. Final hold error is measured once inside its arrival envelope.

| Task | T / seconds | I / seconds | Required final hold |
|---|---:|---:|---:|
| surface_station | 120 | 50 | 30s |
| surface_gates | 240 | 150 | 5s |
| surface_slalom | 300 | 210 | 10s |
| underwater_gate | 180 | 100 | 15s |
| underwater_path | 240 | 170 | 5s |
| underwater_return | 300 | 220 | 5s at the surface |

Examples: a collision-free complete run with all precision thresholds met, at or before `I`, and ≥2m hull clearance gets 100. With `c=0.5`, only half completion and bonus weights are available. A complete run with one struck obstacle is capped at 50 even if its raw score is higher. No meaningful trajectory, nonfinite values, backward/discontinuous simulation time, a pose jump, expired ownership or session change invalidates the run; invalid runs do not enter the official leaderboard. Timeouts produce the earned partial score if native data stayed valid.

RMS is integrated over native simulation time, not the number of browser polls. Physics timestep and scoring tolerances are versioned; official runs cannot change waves/physics during scoring. Full-score thresholds are strict but nonzero. If measured model/sensor limits make them unattainable, the instructor must change the rules version and remeasure the baseline instead of relabeling old scores.

## Five-seed suite and standings

Practice seeds can be chosen. Official server queue requests use `graded=true`; the server chooses the next of five common deterministic suite seeds based on rule version, task and suite index. All participants see the same conditions at that index. The choice does not trust the client's seed field. Seeded changes are geometry scale ±10%, lateral shift ±3m, wind speed 5.5–6.5m/s, wind bearing 110–160° and holding heading ±0.25rad. No unimplemented currents/noise/dropouts are scored.

For a task, `suite_score = 0.8 × mean(five scores) + 0.2 × min(five scores)`. A track result is the arithmetic mean of its three task scores. Fewer than five distinct seeds is provisional and displayed with a run count. Within a suite, the most recent valid result for a seed replaces its previous result; report retries and compute budgets in your class report. A completed five-seed suite starts its next retry at index zero in the current implementation; the operator can schedule a new series/rules version for a finals round.

Server stores timestamp, owner ID, public alias, task, rules version, course seed, native trajectory, metrics, controller type and baseline parameter hash. Email addresses are excluded from public responses. Installed local trials stay practice-only: an open-source client can change its own code/data. Server observation protects score provenance; it is not proof the student wrote the code or used a real navigation estimator. Ground-truth simulated odometry is currently allowed for navigation, explicitly. Obstacle planning exercises should use measured lidar/camera rather than world obstacle poses; stronger perception-only enforcement requires a separate sensor/navigation profile and should be versioned.

## ArduPilot baseline

Pinned rows use a freshly started Autopilot world with the bundled vehicle-default parameter profile and simulator navigation integration. The operator invokes the identical ordered targets, measures native state and records the parameter digest. No parameter-edit session can be used as a baseline; parameter changes during a run invalidate it. Default avoidance/perception is not presumed. Parameters required for Gazebo/SITL/external navigation are part of the shipped profile, so this is not a claim about pure factory hardware settings.

Unmeasured rows say **Not measured**, never a made-up zero or 100. One real seed is a provisional baseline, not a completed five-seed ranking. Course or parameter/model changes require a new baseline/rules version. The baseline remains visible even when students exceed its score.
