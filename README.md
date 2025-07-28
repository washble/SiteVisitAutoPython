# README #

이 프로젝트는 Selenium을 활용해 다수의 웹 페이지를 자동으로 탐색 및 관리할 수 있도록 구성된 Python 스크립트입니다. 탭 자동 열기/닫기, 랜덤 링크 선택, 반복 실행 등 다양한 자동화 동작을 제공합니다.

### What is this repository for? ###

* 웹 페이지 자동화 및 테스트 시나리오용
* 반복적인 페이지 열기/닫기 자동 처리
* 설정 파일 기반 유연한 구성
* Version: v1.0.0
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)

### How do I get set up? ###

#### Summary of set up

1. Python 3 설치
2. 필요한 패키지 설치
3. `config.json` 파일 설정
4. `main.py` 실행

#### Configuration

`config.json` 설정을 통해 자동화의 동작 방식을 제어합니다:

| Key 이름               | 설명 |
|------------------------|------|
| `startup_url`          | 프로그램이 시작할 때 접속할 첫 번째 웹페이지 주소입니다. 예: 네이버 메인 |
| `interval_seconds`     | 반복 사이의 기본 대기 시간(초)입니다. 예: 10초마다 다시 실행 |
| `extra_random_min` / `extra_random_max` | 기본 대기 시간 외에 랜덤으로 추가될 지연 시간 범위입니다. |
| `repeat_forever`       | 무한 반복 실행 여부입니다. `true`면 사용자가 종료하기 전까지 계속 실행됩니다. |
| `repeat_count`         | 반복할 총 횟수입니다. `repeat_forever`가 `false`일 경우에만 사용됩니다.
| `time_to_close`        | 새로 연 탭이 열리고 나서 자동으로 닫히기까지 걸리는 시간(초)입니다. |
| `use_random_selection`| 링크 중 일부를 무작위로 선택해 열지 여부입니다. `true`면 매번 다른 링크가 열립니다. |
| `selection_min` / `selection_max` | 한 번에 열 링크 개수의 최소/최댓값입니다. |
| `link_list`            | 자동으로 열릴 링크들의 목록입니다. 각 링크는 새 탭으로 열리고 일정 시간 후 닫힙니다. |


#### Dependencies

```bash
pip install selenium
pip install pyinstaller
```

#### Generating user_agents.json
최신 Chrome User-Agent 목록을 수집하려면 generate_user_agents_json.py 스크립트를 실행하세요.
스크립트 실행 후 프로젝트 루트에 user_agents.json 파일이 생성됩니다.

python generate_user_agents_json.py
