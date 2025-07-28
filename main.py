from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import random
import threading

link_list = [
    "https://www.naver.com?no=1",
    "https://www.naver.com?no=2",
    "https://www.naver.com?no=3",
]

interval_seconds   = 10
extra_random_min   = 1.0
extra_random_max   = 4.0
repeat_forever     = True
repeat_count       = 5
time_to_close      = 15

# 1) Chrome 옵션 설정
options = Options()
options.add_experimental_option("detach", True)
options.add_argument("--incognito")
options.add_argument("--log-level=3")
driver = webdriver.Chrome(options=options)

# 2) 스크립트 시작 시 메인 윈도우 핸들 저장
main_handle = driver.current_window_handle

# 3) 드라이버 동시 접근용 락
driver_lock = threading.Lock()

def schedule_tab_close(handle, delay):
    """
    handle: 닫을 탭 핸들
    delay: 열린 후 몇 초 뒤에 닫을지
    """
    def close_task():
        time.sleep(delay)
        with driver_lock:
            try:
                if handle not in driver.window_handles:
                    print(f"[스킵] 이미 닫힌 탭: {handle}")
                    return

                # 해당 탭으로 포커스 후 닫기
                driver.switch_to.window(handle)
                driver.close()
                print(f"[닫힘] {handle}")

            except Exception as e:
                print(f"[오류] 닫기 실패 {handle}: {e}")

    t = threading.Thread(target=close_task, daemon=True)
    t.start()


iteration = 0
while repeat_forever or iteration < repeat_count:
    iteration += 1
    print(f"\n[반복 {iteration}] 시작")

    # 반복마다 한 번만 메인 창으로 복귀
    with driver_lock:
        driver.switch_to.window(main_handle)

    newly_opened = []

    # 1) 링크별 새 탭 열기
    for link in link_list:
        with driver_lock:
            driver.get("https://www.naver.com")
            time.sleep(2)

            before = driver.window_handles.copy()
            driver.execute_script(f'window.open("{link}", "_blank");')
            print(f"[열기] {link}")
            time.sleep(2)

            after = driver.window_handles
            new_tabs = [h for h in after if h not in before]
            newly_opened.extend(new_tabs)

    # 2) 열린 순서대로 닫기 예약
    for idx, handle in enumerate(newly_opened):
        schedule_tab_close(handle, time_to_close + idx * 0.1)

    # 3) 다음 반복 전 랜덤 대기
    extra = random.uniform(extra_random_min, extra_random_max)
    total_wait = interval_seconds + extra
    print(f"[반복 {iteration}] 완료 → {round(total_wait,2)}초 후 재시작")
    time.sleep(total_wait)

# 스크립트 종료 후에도 브라우저 유지
try:
    print("모든 반복 완료. Ctrl+C로 종료하세요.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("사용자 종료, 스크립트를 마칩니다.")