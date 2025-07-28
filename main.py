from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import random

# 브라우저 꺼짐 방지 옵션 설정
options = Options()
options.add_experimental_option("detach", True)
options.add_argument("--incognito")
options.add_argument("--log-level=3")

# 크롬 드라이버 실행
driver = webdriver.Chrome(options=options)

# 블로그 링크 리스트
link_list = [
    "https://blog.naver.com/washble2/223870890490",
    "https://blog.naver.com/washble2/223870890490",
    "https://blog.naver.com/washble2/223870890490",
]

# 반복 실행 설정
interval_seconds = 10       # 기본 반복 간격 (초)
extra_random_min = 1.0      # 랜덤 추가 시간 최소값 (초)
extra_random_max = 4.0      # 랜덤 추가 시간 최대값 (초)
repeat_forever = True       # 무한 반복 여부
repeat_count = 5            # 무한 반복이 아닌 경우 반복 횟수

# 반복 시작
iteration = 0
while repeat_forever or iteration < repeat_count:
    iteration += 1
    print(f"\n[반복 {iteration}] 블로그 링크 열기 시작")

    for link in link_list:
        try:
            driver.get("https://www.naver.com")
            time.sleep(2)

            driver.execute_script(f'''window.open("{link}", "_blank");''')
            print(f"[성공] 주소창 입력처럼 {link} 새 창으로 열기 완료")
            time.sleep(2)

        except Exception as e:
            print(f"[오류] {link} 접속 중 문제가 발생했습니다:", e)

    # 랜덤 대기 시간 계산
    random_delay = random.uniform(extra_random_min, extra_random_max)
    total_wait = interval_seconds + random_delay
    if total_wait >= 3600:
        hrs = int(total_wait // 3600)
        mins = int((total_wait % 3600) // 60)
        secs = round(total_wait % 60, 2)
        print(f"[반복 {iteration}] 완료. 총 {hrs}시간 {mins}분 {secs}초 후 다시 시작합니다.")
    elif total_wait >= 60:
        mins = int(total_wait // 60)
        secs = round(total_wait % 60, 2)
        print(f"[반복 {iteration}] 완료. 총 {mins}분 {secs}초 후 다시 시작합니다.")
    else:
        print(f"[반복 {iteration}] 완료. 총 {round(total_wait, 2)}초 후 다시 시작합니다.")
    time.sleep(total_wait)

# 브라우저 유지 루프
try:
    print("\n모든 반복 작업 완료. 브라우저는 계속 열려 있습니다. 종료하려면 Ctrl+C를 누르세요.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[사용자 종료] 스크립트를 종료합니다.")