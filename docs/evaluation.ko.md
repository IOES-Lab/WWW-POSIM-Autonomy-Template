# 설치형 Evaluation과 배포

[English](evaluation.md) · [채점 규칙](scoring.md) · [교재](course.ko.md)

반복 개발은 설치형 시뮬레이터에서 진행합니다. 공식 채점도 **알고리즘은 내 PC에서 실행**하고, 서버의 독립 Gazebo 월드가 센서와 점수를 기록합니다. 학생 소스·임의 ROS 패키지·실행 파일을 서버에 올려 실행하는 방식이 아닙니다.

## 버튼 하나로 시작

설치한 **WWW-POSIM Evaluation** 앱 또는 `www-posim evaluation`을 엽니다. 서버 API, 이메일, 공개 별명, 과제, 코드 폴더와 JSON 명령 인수 목록을 입력합니다. 예를 들어 `["python3", "my_controller.py"]`는 선택한 폴더의 파일을 실행합니다. Mac/Windows는 강사가 제공하는 ROS 클라이언트 이미지를 사용하고, 네이티브 Linux ROS 터미널에서는 이미지 필드를 비울 수 있습니다. 공식 시뮬레이션은 서버에서 실행되므로 PC의 제어 클라이언트에는 GPU가 필요하지 않습니다.

**Evaluate on server**를 누르면 버전을 확인하고 FIFO 대기열에 들어갑니다. 고정 코스가 준비되면 최신 프로필을 내려받고 실제 Odometry와 추진기 준비를 기다린 뒤, 서버 채점을 시작하고 로컬 명령을 실행합니다. 대기 중에는 사용 시간을 차감하지 않으며 순번과 다음 슬롯 예상 시간을 표시합니다. 종료 시 `result.json`, `relay-report.json`, `relay.log`, `algorithm.log`를 저장하고 자신이 만든 프로세스와 서버 슬롯을 정리합니다. **Cancel**은 실행을 멈추고 채점이 시작됐다면 `interrupted-result.json`도 남깁니다. 중단한 실행은 공식 점수를 받지 않습니다. 정리가 끝날 때까지 앱을 열어 두세요.

비밀번호는 작업마다 한 번 입력하며 설정·명령행·결과 파일에 저장하지 않습니다. 짧은 인증 쿠키는 PC 클라이언트와 중계의 비공개 표준입력으로 전달합니다. Docker 클라이언트에는 선택한 코드와 결과 폴더만 연결합니다. 로컬 ROS 도메인은 76이며 서버 DDS 포트를 공개하지 않습니다.

```sh
www-posim evaluate --server https://YOUR_SERVER/api --email YOU@example.edu \
  --task surface_station --alias MyTeam --project ./my_project \
  --client-image INSTRUCTOR_CLIENT_IMAGE --output ./evaluation-results \
  -- python3 my_controller.py
```

Linux 네이티브 ROS 또는 Apple Silicon 앱의 ROS 환경을 불러온 뒤 `--client-image`를 생략합니다. **Practice locally**는 실행 중인 설치형 `http://127.0.0.1:3300/api`를 사용합니다. 설치형 실행기의 로그인·시간 권한을 우회하지 않습니다. 샘플 부표 회피 코드는 모든 채점 과제를 해결하는 완성 코드가 아니며, 과제 목표와 유지 조건을 읽어 직접 확장해야 합니다.

## ROS와 기록 신뢰성

서버의 실제 Odometry·LaserScan·IMU·압축 카메라가 로컬 ROS 메시지로 전달됩니다. 알고리즘은 `/wwos/cmd_vel` 또는 `/wwos/thrusters`를 publish합니다. 인증·세션 nonce·독점 제어 lease·증가하는 sequence·힘 제한·0.75초 watchdog이 명령 경로를 보호합니다. `/ros`는 읽기 전용이고 `/control`이 허용된 명령을 전달합니다. 위치 순간이동이나 Gazebo 원시 명령은 허용하지 않습니다.

로컬 점수·로그를 보고서용으로 내보낼 수 있습니다. 그러나 기기 소유자는 오픈소스 시뮬레이터·시간·로그를 수정할 수 있으므로, 같은 기기가 만든 해시나 서명만으로 부정행위를 막을 수 없습니다. 공식 순위는 **서버가 직접 관측하고 저장한 실제 궤적만** 반영합니다. JSON의 SHA-256은 파일 변경 확인용이며 공정성 증명이 아닙니다. 내보내기는 소유자만 가능하고 서버 슬롯을 종료한 뒤에도 run ID로 받을 수 있습니다. 이메일은 포함하지 않습니다. JSON 점수 업로드만으로 순위 점수를 받는 API는 제공하지 않습니다. 공식 실행 중에도 파도·물리 조건을 검사하고 변화가 있으면 무효 처리합니다. 5개 seed 묶음과 실제 기본 Autopilot 기준선은 기존 규칙을 사용합니다.

## 설치와 업데이트

Evaluation 클라이언트와 시뮬레이터 앱은 별도로 설치합니다. 템플릿 저장소에서 `python -m pip install .`을 실행하면 Python 패키지가 설치됩니다. `www-posim evaluation`은 데스크톱 화면을, `www-posim evaluate`는 같은 절차를 터미널에서 실행합니다. Apple Silicon용 ROS·Gazebo·Metal 엔진은 [시뮬레이터 배포판](https://github.com/woensug-choi/homebrew-www-posim)을 사용하고, 다른 운영체제의 준비 절차는 [교재의 설치 안내](course.ko.md#installation)를 참고하세요.

Apple Silicon에서는 앱에 포함된 ROS 환경을 불러온 뒤 Python Evaluation 클라이언트를 설치하고 실행합니다.

```sh
eval "$(/Applications/WWW-POSIM.app/Contents/MacOS/WWW-POSIM --ros-env)"
python -m pip install /PATH/TO/WWW-POSIM-Autonomy-Template
www-posim evaluate --server https://YOUR_SERVER/api --email YOU@example.edu \
  --task surface_station --alias MyTeam --project ./my_project \
  --output ./evaluation-results -- python my_controller.py
```

이 ROS Python을 사용할 때는 `--client-image`를 생략합니다. 별도로 제공되는 컴파일된 Evaluation 앱은 내장 Python에 ROS가 없으므로 강사의 ROS 클라이언트 컨테이너를 사용합니다. 공식 시뮬레이션과 채점은 두 방식 모두 서버에서 실행됩니다.

실행 전과 실행 중 5분마다 버전을 확인하고 업데이트는 실행 사이에 적용합니다. 0.2.2에는 Evaluation 화면과 CLI가 포함되어 있으며 서버는 통신 프로토콜과 채점 규칙 버전도 확인합니다. 엔진 의존성과 로봇 자산은 버전이 바뀌기 전까지 재사용합니다.
