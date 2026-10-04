# WWW-POSIM 자율운항 템플릿

[English](README.md) · [한국어 강의계획·실습 교재](docs/course.ko.md) · [채점 규칙](docs/scoring.md)

GitHub의 **Use this template → Create a new repository**로 개인·팀 저장소를 만드세요. 여러분의 ROS 2 자율운항 코드는 여기에서 개발하고, 시뮬레이터와 POSIM은 별도 의존성으로 유지합니다.

실제 Gazebo 라이다를 이용한 수상 로봇의 지도 작성·A* 회피 예제, 수중 로봇 수심 제어 예제, 센서 수신·명령 송신 릴레이, 설치형 실행기를 제공합니다. 예제는 출발점이며 대회 만점 해답이 아닙니다. AI 사용은 허용하지만 생성된 코드를 직접 시험하고 설계 이유를 설명해야 합니다.

```bash
# ROS 환경을 먼저 불러오거나 시뮬레이터의 ROS 컨테이너 터미널을 사용
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
pip install -e .
export ROS_DOMAIN_ID=73
www-posim-connect --server https://YOUR_SERVER/api --email YOU@example.edu --control
# 다른 터미널에서
www-posim-surface
# BlueROV2 세션일 때
www-posim-underwater --depth 2
```

설치형은 `www-posim --server ... --email ... --runtime-image ... --web-image ...`로 실행합니다. ROS·Gazebo는 Docker에 포함되며, 브라우저에서 `http://127.0.0.1:3300`을 엽니다. 실행기는 서버 로그인·버전 확인·시간 제한 갱신을 담당합니다. 비밀번호를 파일이나 명령행 인수로 저장하지 않습니다.

기본 사용 시간은 **설치형 하루 3시간, 웹 하루 1시간**이며 UTC 0시에 초기화됩니다. 웹 서버는 독립 시뮬레이션 최대 2개, 초기 이용 대상 5명입니다. 설치형 Pro는 승인일부터 6개월 또는 지정 학기 동안 무제한이며 웹 시간 제한을 해제하지 않습니다. 실행 권한은 60초마다 만료되고 20초 간격으로 갱신합니다. 유휴·지형 준비에는 권한을 시작하지 않지만 네이티브 월드 시작·센서 준비 시간은 설치형 사용 시간에 포함됩니다.

현재 ARM64 런타임은 로컬에서 빌드되어 있습니다. 공개 다운로드용 AMD64/ARM64 이미지와 Linux/Windows GPU 검증은 별도 배포 절차가 필요합니다. Mac Docker는 Apple GPU를 Gazebo에 전달하지 못해 CPU 렌더링을 사용합니다. Linux/NVIDIA·Windows/WSL2의 GPU 설정과 OS별 설치 절차는 교재에 있습니다. 소스 제공을 모든 OS에서 검증된 앱 배포 완료로 해석하지 마세요.

ROS 토픽과 힘의 단위·좌표계, 안전 중지, 여섯 과제와 채점 식, RViz·rosbag·WSS·SSH 터널 실습은 [한국어 교재](docs/course.ko.md)를 참고하세요. 설치형 기록은 연습이며 공개 순위에는 서버가 직접 측정한 지정 코스 기록만 반영됩니다. 오픈소스 로컬 실행기는 변조 방지 DRM이 아닙니다.

[IOES-Lab, KMOU](https://lab.wschoi.com) · [시뮬레이터 소스](https://github.com/IOES-LAB/WWW-POSIM)

실제 카메라는 프로필의 `sensor_msgs/msg/CompressedImage` 토픽으로 최대 1Hz 전달합니다. 수중 조사 영상은 RGBD 수중 셰이더가 적용됩니다. 공식 채점은 부산 예제의 수면 시작점 35.07446 N / 129.08468 E, 1배속·10ms 물리 간격을 사용하며 연습은 자유롭게 설정합니다.

Linux/macOS는 `sh install.sh`, Windows PowerShell은 `./install.ps1`로 Python 템플릿·실행기를 설치합니다. Python 3.10 이상이 필요하며 ROS/Gazebo 런타임은 별도의 Docker 이미지입니다.
