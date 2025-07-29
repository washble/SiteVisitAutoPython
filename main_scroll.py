import json
import os
import time
import random
import threading
# pip install selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# pip install pyinstaller

'''
[exe build]
- Just make exe -
> pyinstaller main_scroll.py

- Only One exe File -
> pyinstaller -F main_scroll.py
'''

# 사용된 user-agent 기록용 집합
used_agents = set()
# user_agents.json을 한 번만 로드해 둘 전역 변수
user_agents_list = None

# user_agents.json 로드 및 관리 함수
def get_random_user_agent(path="user_agents.json"):
    global user_agents_list

    if user_agents_list is None:
        if not os.path.exists(path):
            print("[경고] user_agents.json 파일을 찾을 수 없습니다. 기본 user-agent를 사용합니다.")
            user_agents_list = []
        else:
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        raise ValueError
                    user_agents_list = data
                except Exception:
                    print("[경고] user_agents.json 파싱 실패 또는 형식 오류. 기본 user-agent를 사용합니다.")
                    user_agents_list = []

    if not user_agents_list:
        return None

    available_agents = [ua for ua in user_agents_list if ua not in used_agents]
    if not available_agents:
        used_agents.clear()
        available_agents = user_agents_list.copy()
        print("[초기화] 모든 user-agent를 사용했으므로 목록을 초기화합니다.")

    selected = random.choice(available_agents)
    used_agents.add(selected)
    return selected

# config.json 로드 함수
def load_config(path="config.json"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} 파일을 찾을 수 없습니다.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Chrome 드라이버 초기화 함수
def setup_driver(startup_url):
    options = Options()
    options.add_experimental_option("detach", True)
    options.add_argument("--headless")
    options.add_argument("--incognito")
    options.add_argument("--log-level=3")
    options.add_argument("--mute-audio")
    driver = webdriver.Chrome(options=options)
    driver.get(startup_url)
    return driver

# 탭 자동 닫기 스케줄링 함수
def schedule_tab_close(handle, delay, driver, driver_lock):
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

# 메인 반복 동작 함수
def run_loop(cfg, driver, main_handle, driver_lock):
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

    iteration = 0
    while repeat_forever or iteration < repeat_count:
        iteration += 1
        print(f"\n[반복 {iteration}] 시작")

        ua = get_random_user_agent()
        if ua:
            try:
                driver.execute_cdp_cmd(
                    "Network.setUserAgentOverride",
                    {"userAgent": ua}
                )
                print(f"[USER-AGENT 적용] {ua}")
            except Exception:
                print("[경고] CDP로 user-agent 적용 실패, 기본 user-agent 유지")
        else:
            print("[USER-AGENT 적용] 기본 user-agent 사용")

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
        for idx, link in enumerate(selected_links, start=1):
            with driver_lock:
                driver.switch_to.window(main_handle)
                before = driver.window_handles.copy()
                driver.execute_script(f'window.open("{link}", "_blank");')
                print(f"[열기] {link}")

            with driver_lock:
                after = driver.window_handles
                new_tabs = [h for h in after if h not in before]
                if not new_tabs:
                    print("[스킵] 새 탭 핸들 못 찾음")
                    continue

                handle = new_tabs[0]
                driver.switch_to.window(handle)

                # 새 탭 전환 후, body 태그 로딩 대기
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # 새 탭이 열리면 맨 아래로 스크롤 (iframe 있으면 내부에서, 없으면 문서에서)
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                if iframes:
                    # 첫 번째 iframe 내부로 들어가서 스크롤
                    driver.switch_to.frame(iframes[0])
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    driver.switch_to.default_content()
                else:
                    # iframe 없으면 문서 전체에서 스크롤
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                print(f"[스크롤 완료] {handle}")

            newly_opened.append(handle)
            schedule_tab_close(handle, time_to_close + idx * 0.1, driver, driver_lock)

        extra = random.uniform(extra_random_min, extra_random_max)
        total_wait = interval_seconds + extra
        print(f"[반복 {iteration}] 완료 → {round(total_wait,2)}초 후 재시작")
        time.sleep(total_wait)

if __name__ == "__main__":
    config_path = "config.json"
    cfg = load_config(config_path)

    startup_url = cfg.get("startup_url", "https://www.google.com")

    driver = setup_driver(startup_url)
    main_handle = driver.current_window_handle
    driver_lock = threading.Lock()

    run_loop(cfg, driver, main_handle, driver_lock)

    try:
        print("모든 반복 완료. Ctrl+C로 종료하세요.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("사용자 종료, 스크립트를 마칩니다.")