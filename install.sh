#!/usr/bin/env sh
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
task_python=${WWW_POSIM_PYTHON:-python3}
"$task_python" -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ required"'
"$task_python" -m venv --system-site-packages "$task_root/.venv"
"$task_root/.venv/bin/python" -m pip install -e "$task_root"
printf '%s\n' 'Installed. Activate .venv/bin/activate, then read docs/course.md.' 'Docker and instructor-provided runtime/web image tags are required for www-posim.'
