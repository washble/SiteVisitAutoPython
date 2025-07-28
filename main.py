import json
import os
import time
import random
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 1) config.json 로드
config_path = "config.json"
if not os.path.exists(config_path):
    raise FileNotFoundError(f"{config_path} 파일을 찾을 수 없습니다.")

with open(config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

link_list            = cfg.get("link_list", [])
interval_seconds     = cfg.get("interval_seconds", 10)
extra_random_min     = cfg.get("extra_random_min", 1.0)
extra_random_max     = cfg.get("extra_random_max", 4.0)
time_to_close        = cfg.get("time_to_close", 15)
repeat_forever       = cfg.get("repeat_forever", True)
repeat_count         = cfg.get("repeat_count", 5)
use_random_selection = cfg.get("use_random_selection", True)
selection_min        = cfg.get("selection_min", 1)
selection_max        = cfg.get("selection_max", len(link_list))

# 2) Chrome 옵션 설정
options = Options()
options.add_experimental_option("detach", True)
options.add_argument("--incognito")
options.add_argument("--log-level=3")
driver = webdriver.Chrome(options=options)

driver.get("https://www.naver.com")
main_handle = driver.current_window_handle

driver_lock = threading.Lock()

def schedule_tab_close(handle, delay):
    def close_task():
        time.sleep(delay)
        with driver_lock:
            try:
                if handle not in driver.window_handles:
                    print(f"[스킵] 이미 닫힌 탭: {handle}")
                    return
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

    with driver_lock:
        driver.switch_to.window(main_handle)

    if use_random_selection:
        min_open = max(selection_min, 0)
        max_open = min(selection_max, len(link_list))
        if min_open > max_open:
            min_open = max_open
        num_to_open = random.randint(min_open, max_open)
        selected_links = random.sample(link_list, num_to_open)
        print(f"[선택] 랜덤 사용: 열 링크 {num_to_open}개 →", selected_links)
    else:
        selected_links = link_list.copy()
        print(f"[선택] 랜덤 사용 안 함: 전체 링크 열기 →", selected_links)

    newly_opened = []
    for link in selected_links:
        with driver_lock:
            before = driver.window_handles.copy()
            driver.execute_script(f'window.open("{link}", "_blank");')
            print(f"[열기] {link}")
            after = driver.window_handles
        new_tabs = [h for h in after if h not in before]
        newly_opened.extend(new_tabs)

    for idx, handle in enumerate(newly_opened):
        schedule_tab_close(handle, time_to_close + idx * 0.1)

    extra = random.uniform(extra_random_min, extra_random_max)
    total_wait = interval_seconds + extra
    print(f"[반복 {iteration}] 완료 → {round(total_wait,2)}초 후 재시작")
    time.sleep(total_wait)

try:
    print("모든 반복 완료. Ctrl+C로 종료하세요.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("사용자 종료, 스크립트를 마칩니다.")