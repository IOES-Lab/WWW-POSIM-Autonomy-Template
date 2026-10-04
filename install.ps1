$ErrorActionPreference = "Stop"
py -3 -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ required"'
if ($LASTEXITCODE -ne 0) { throw "Install Python 3.10+ from python.org" }
py -3 -m venv --system-site-packages "$PSScriptRoot\.venv"
if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed" }
& "$PSScriptRoot\.venv\Scripts\python.exe" -m pip install -e $PSScriptRoot
if ($LASTEXITCODE -ne 0) { throw "Package installation failed" }
Write-Host "Installed. Activate .venv\Scripts\Activate.ps1, then read docs/course.md."
Write-Host "Docker Desktop/WSL2 and instructor-provided native image tags are required."
