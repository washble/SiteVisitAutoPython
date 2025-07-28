from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

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
interval_seconds = 10   # 반복 간격 (초)
repeat_forever = True   # True일 경우 무한 반복, False일 경우 정해진 횟수만 반복
repeat_count = 5        # 무한 반복이 아닌 경우 사용할 횟수

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

    print(f"[반복 {iteration}] 완료. {interval_seconds}초 후 다시 시작합니다.")
    time.sleep(interval_seconds)

# 브라우저 유지 루프 (사용자가 직접 종료할 때까지 유지)
try:
    print("\n모든 반복 작업 완료. 브라우저는 계속 열려 있습니다. 종료하려면 Ctrl+C를 누르세요.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[사용자 종료] 스크립트를 종료합니다.")