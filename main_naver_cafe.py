import json
import os
import time
import random
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# pip install pyinstaller
# pip install selenium

'''
[exe build]
- Just make exe -
> pyinstaller main_naver_cafe.py

- Only One exe File -
> pyinstaller -F main_naver_cafe.py
'''

# 사용된 user-agent 기록용 집합
used_agents = set()
# user_agents.json을 한 번만 로드해 둘 전역 변수
user_agents_list = None

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

def load_config(path="config.json"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} 파일을 찾을 수 없습니다.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def login_to_naver(driver, naver_id, naver_pw):
    # 네이버 로그인 페이지로 이동
    try:
        driver.find_element(By.CLASS_NAME, 'MyView-module__link_login___HpHMW').click()
        time.sleep(3)
    except Exception:
        print("[경고] 로그인 버튼을 찾지 못했습니다")
    
    # headless 모드에서는 클립보드 사용이 불가 => JS로 직접 input value를 설정합니다.
    driver.execute_script(
        f"document.querySelector('input#id').setAttribute('value', '{naver_id}');"
    )
    time.sleep(0.5)
    driver.execute_script(
        f"document.querySelector('input#pw').setAttribute('value', '{naver_pw}');"
    )
    time.sleep(0.5)

    # 로그인 버튼 클릭
    login_btn = driver.find_element(By.CLASS_NAME, "btn_login")
    login_btn.click()
    time.sleep(3)  # 로그인 처리 안정화 대기
    
    # 로그인 확인을 위한 인증쿠키와 현재 URL체크(로그인 성공 시 네이버 창으로 redirect됨)
    def is_logged_in(driver):
        cookie_ok = any(c['name'] == 'NID_AUT' for c in driver.get_cookies())
        current_url = driver.current_url
        url_ok = current_url.startswith("https://www.naver.com")
        return cookie_ok, url_ok, current_url

    # 로그인 확인 후 출력
    cookie_ok, url_ok, current_url = is_logged_in(driver)

    if cookie_ok and url_ok:
        print(f"로그인 완료. 쿠키: {'유효' if cookie_ok else '없음'}, 현재 URL: {current_url}")
    else:
        print(f"로그인 실패. 쿠키: {'유효' if cookie_ok else '없음'}, 현재 URL: {current_url}")
    
def setup_driver(startup_url, use_headless):
    options = Options()
    options.add_experimental_option("detach", True)
    if use_headless:
        options.add_argument("--headless")
    options.add_argument("--incognito")
    options.add_argument("--log-level=3")
    options.add_argument("--mute-audio")
    driver = webdriver.Chrome(options=options)
    driver.get(startup_url)
    return driver

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

        for idx, link in enumerate(selected_links, start=1):
            rand_num = random.randint(0, 100)
            modified_link = f"{link}/{rand_num}"
            with driver_lock:
                driver.switch_to.window(main_handle)
                before = driver.window_handles.copy()
                driver.execute_script(f'window.open("{modified_link}", "_blank");')
                print(f"[열기] {modified_link}")

            with driver_lock:
                after = driver.window_handles
                new_tabs = [h for h in after if h not in before]
                if not new_tabs:
                    print("[스킵] 새 탭 핸들 못 찾음")
                    continue

                handle = new_tabs[0]
                print(f"[탭 핸들] {handle}")
                
                driver.switch_to.window(handle)
                try:
                    # 최대 2초간 alert 대기
                    WebDriverWait(driver, 2).until(EC.alert_is_present())
                    alert = driver.switch_to.alert
                    print(f"[Alert 감지] 내용: {alert.text}")
                    alert.accept()
                    print("[Alert 닫음]")
                    
                    # alert 닫힌 뒤 탭도 종료
                    driver.close()
                    print(f"[탭 닫힘] {handle} (alert 발생)")
                    
                    # 메인 탭으로 돌아가기
                    driver.switch_to.window(main_handle)
                    continue  # 다음 링크로 넘어감
                except TimeoutException:
                    # alert이 없으면 정상적으로 닫기 예약
                    driver.switch_to.window(main_handle)


                schedule_tab_close(handle, time_to_close + idx * 0.1, driver, driver_lock)

        extra = random.uniform(extra_random_min, extra_random_max)
        total_wait = interval_seconds + extra
        print(f"[반복 {iteration}] 완료 → {round(total_wait,2)}초 후 재시작")
        time.sleep(total_wait)

if __name__ == "__main__":
    # config.json에서 설정 및 네이버 로그인 정보 로드
    config_path = "naver_cafe_config.json"
    cfg = load_config(config_path)
    naver_id = cfg.get("naver_id")
    naver_pw = cfg.get("naver_pw")
    if not naver_id or not naver_pw:
        raise ValueError("config.json에 'naver_id'와 'naver_pw'를 입력해주세요")

    # 드라이버 초기화 (startup URL 고정: 네이버)
    startup_url = cfg.get("startup_url", "https://www.naver.com")
    use_headless = cfg.get("use_headless", False)
    driver = setup_driver(startup_url, use_headless)
    main_handle = driver.current_window_handle
    driver_lock = threading.Lock()

    # 네이버 로그인
    login_to_naver(driver, naver_id, naver_pw)

    # 메인 루프 시작
    run_loop(cfg, driver, main_handle, driver_lock)

    # 종료 대기
    try:
        print("모든 반복 완료. Ctrl+C로 종료하세요.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("사용자 종료, 스크립트를 마칩니다.")