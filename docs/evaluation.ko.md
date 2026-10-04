# 설치형 Evaluation과 배포

[English](evaluation.md) · [채점 규칙](scoring.md) · [교재](course.ko.md)

반복 개발은 설치형 시뮬레이터에서 진행합니다. 공식 채점도 **알고리즘은 내 PC에서 실행**하고, 서버의 독립 Gazebo 월드가 센서와 점수를 기록합니다. 학생 소스·임의 ROS 패키지·실행 파일을 서버에 올려 실행하는 방식이 아닙니다.

## 버튼 하나로 시작

설치한 **WWW-POSIM Evaluation** 앱 또는 `www-posim evaluation`을 엽니다. 서버 API, 이메일, 공개 별명, 과제, 코드 폴더와 JSON 명령 인수 목록을 입력합니다. 예를 들어 `["python3", "my_controller.py"]`는 선택한 폴더의 파일을 실행합니다. Mac/Windows는 강사가 제공하는 ROS 클라이언트 이미지를 사용하고, 네이티브 Linux ROS 터미널에서는 이미지 필드를 비울 수 있습니다. 공식 시뮬레이션은 서버에서 실행되므로 PC의 제어 클라이언트에는 GPU가 필요하지 않습니다.

**Evaluate on server**를 누르면 버전을 확인하고 FIFO 대기열에 들어갑니다. 고정 코스가 준비되면 최신 프로필을 내려받고 실제 Odometry와 추진기 준비를 기다린 뒤, 서버 채점을 시작하고 로컬 명령을 실행합니다. 대기 중에는 사용 시간을 차감하지 않으며 순번과 다음 슬롯 예상 시간을 표시합니다. 종료 시 `result.json`, `relay-report.json`, `relay.log`, `algorithm.log`를 저장하고 자신이 만든 프로세스와 서버 슬롯을 정리합니다. **Cancel**은 실행을 멈추고 채점이 시작됐다면 `interrupted-result.json`도 남깁니다. 중단한 실행은 공식 점수를 받지 않습니다. 정리가 끝날 때까지 앱을 열어 두세요.

비밀번호는 작업마다 한 번 입력하며 설정·명령행·결과 파일에 저장하지 않습니다. 짧은 인증 쿠키는 PC 클라이언트와 중계의 비공개 표준입력으로 전달합니다. Docker 클라이언트에는 선택한 코드와 결과 폴더만 연결합니다. 로컬 ROS 도메인은 73이며 서버 DDS 포트를 공개하지 않습니다.

```sh
www-posim evaluate --server https://YOUR_SERVER/api --email YOU@example.edu \
  --task surface_station --alias MyTeam --project ./my_project \
  --client-image INSTRUCTOR_CLIENT_IMAGE --output ./evaluation-results \
  -- python3 my_controller.py
```

Linux 네이티브 ROS에서는 환경을 source한 뒤 `--client-image`를 생략합니다. **Practice locally**는 실행 중인 설치형 `http://127.0.0.1:3300/api`를 사용합니다. 설치형 실행기의 로그인·시간 권한을 우회하지 않습니다. 샘플 부표 회피 코드는 모든 채점 과제를 해결하는 완성 코드가 아니며, 과제 목표와 유지 조건을 읽어 직접 확장해야 합니다.

## ROS와 기록 신뢰성

서버의 실제 Odometry·LaserScan·IMU·압축 카메라가 로컬 ROS 메시지로 전달됩니다. 알고리즘은 `/wwos/cmd_vel` 또는 `/wwos/thrusters`를 publish합니다. 인증·세션 nonce·독점 제어 lease·증가하는 sequence·힘 제한·0.75초 watchdog이 명령 경로를 보호합니다. `/ros`는 읽기 전용이고 `/control`이 허용된 명령을 전달합니다. 위치 순간이동이나 Gazebo 원시 명령은 허용하지 않습니다.

로컬 점수·로그를 보고서용으로 내보낼 수 있습니다. 그러나 기기 소유자는 오픈소스 시뮬레이터·시간·로그를 수정할 수 있으므로, 같은 기기가 만든 해시나 서명만으로 부정행위를 막을 수 없습니다. 공식 순위는 **서버가 직접 관측하고 저장한 실제 궤적만** 반영합니다. JSON의 SHA-256은 파일 변경 확인용이며 공정성 증명이 아닙니다. 내보내기는 소유자만 가능하고 서버 슬롯을 종료한 뒤에도 run ID로 받을 수 있습니다. 이메일은 포함하지 않습니다. JSON 점수 업로드만으로 순위 점수를 받는 API는 제공하지 않습니다. 공식 실행 중에도 파도·물리 조건을 검사하고 변화가 있으면 무효 처리합니다. 5개 seed 묶음과 실제 기본 Autopilot 기준선은 기존 규칙을 사용합니다.

## 실제 배포 범위

| 형식 | 포함 내용 | 이번 검증 |
|---|---|---|
| Python wheel | 템플릿·실행기·채점 GUI/CLI | 0.2.2 빌드, 단위 검사 통과 |
| Mac ARM64 `.app` | Python/Tk를 포함한 클라이언트, 압축 약 12 MB | 빌드·CLI 버전 확인. Mac 잠금으로 앱 화면 직접 검증은 미완료 |
| Debian `.deb` | Python 클라이언트·데스크톱 진입점 | Ubuntu 컨테이너에서 빌드·추출·버전 확인. 전체 네이티브 엔진 설치본은 아님 |
| Homebrew Cask | 해시를 고정한 Mac 앱 archive | 로컬 파일용 생성 완료. 같은 파일을 공개한 뒤 URL 설정 필요 |
| Windows `.exe` | PyInstaller 클라이언트와 Inno Setup | 대상 OS CI·빌드 레시피 제공. Windows 실행 검증은 미완료 |
| Docker 이미지 | 엔진 또는 PC용 ROS 제어 클라이언트 | 로컬 ARM64 빌드 유지. 공개 AMD64/ARM64 릴리스는 추가 필요 |

`python tools/build_installer.py wheel`, `desktop`, `deb`로 빌드합니다. 데스크톱 바이너리는 대상 OS에서 만들어야 합니다([PyInstaller](https://pyinstaller.org/en/latest/)). `packaging/windows.iss`와 GitHub Actions 워크플로는 Windows 설치본 생성을 준비하며 공개 릴리스를 자동 발행하지 않습니다.

엔진 네이티브 배포는 Linux부터 검증하는 순서를 권합니다. ROS/Gazebo/POSIM과 독립 파도 의존성·자산·각 라이선스를 함께 유지해야 합니다. [ROS Lyrical 공식 플랫폼](https://github.com/ros2/ros2_documentation/blob/rolling/source/Get-Started/Releases/lyrical/supported-platforms.rst), [Gazebo Mac 설치](https://gazebosim.org/docs/latest/install_osx/), [실험 단계 Windows 설치](https://gazebosim.org/docs/latest/install_windows/)를 기준으로 검증하며, Gazebo 하나가 설치됐다고 전체 POSIM 스택의 호환성이 확인되지는 않습니다. 현재 검증한 엔진 경로는 Docker입니다. [Docker Desktop GPU 지원](https://docs.docker.com/desktop/features/gpu/)은 이 Gazebo 컨테이너에 Apple GPU를 전달하지 않으며 NVIDIA/WSL2도 실제 하드웨어 검증이 필요합니다.

실행 전과 실행 중 5분마다 버전을 확인하며 업데이트는 실행 사이에 적용합니다. 클라이언트·어댑터 변경은 작은 패키지와 바뀐 Docker layer만 받지만 의존성·모델 변경은 큰 다운로드가 될 수 있습니다. 새 Evaluation은 0.2.2이며 기존 최소 호환 버전은 0.2.1입니다. 공개 설치 릴리스에는 일치하는 엔진/클라이언트 이미지, 체크섬, 필요한 서명·notarization, HTTPS·SMTP 운영 설정과 대상 OS 검증이 추가로 필요합니다.
