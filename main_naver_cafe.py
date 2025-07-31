import json
import os
import time
import random
import threading
import subprocess
import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# pip install pyinstaller
# pip install selenium
# pip install pyperclip

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
    driver.get("https://www.naver.com")
    time.sleep(3)
    try:
        driver.find_element(By.CLASS_NAME, 'MyView-module__link_login___HpHMW').click()
        time.sleep(3)
    except Exception:
        print("[경고] 로그인 버튼을 찾지 못했습니다")
    
    # ID 입력 (pyperclip 사용)
    id_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "id"))
    )
    id_field.clear()
    pyperclip.copy(naver_id)
    id_field.send_keys(Keys.CONTROL, 'v')
    time.sleep(0.5)

    # PW 입력 (pyperclip 사용)
    pw_field = driver.find_element(By.ID, "pw")
    pw_field.clear()
    pyperclip.copy(naver_pw)
    pw_field.send_keys(Keys.CONTROL, 'v')
    time.sleep(0.5)

    # 보안을 위해 클립보드 비우기
    pyperclip.copy('')

    # 로그인 버튼 클릭
    login_btn = driver.find_element(By.CLASS_NAME, "btn_login")
    login_btn.click()
    print("[네이버 로그인] 완료")
    time.sleep(3)  # 로그인 처리 안정화 대기
    
def find_chrome_exe(paths):
    for path in paths:
        for root, dirs, files in os.walk(path):
            if 'chrome.exe' in files:
                return os.path.join(root, 'chrome.exe')
    return None

def init_driver(use_headless=False):
    paths_to_search = [
        'C:\\Program Files\\Google\\Chrome\\Application',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application'
    ]
    chrome_path = find_chrome_exe(paths_to_search)
    if chrome_path:
        try:
            subprocess.Popen(fr'{chrome_path} --remote-debugging-port=19440 '
                            r' --user-data-dir="C:\chromeTemp32"')
        except FileNotFoundError:
            print(f"[오류] Chrome 실행 실패: {e}")
    else:
        print("[에러] chrome.exe 경로를 찾지 못했습니다.")

    try:
        service = ChromeService(ChromeDriverManager().install())
        options = setup_driver_option()
        if(use_headless):
            options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(3)
        print("WebDriver 초기화 성공")
        return driver
    except WebDriverException as e:
        print(f"WebDriver 초기화 실패: {e}")
        return None

def setup_driver_option(use_headless=False):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:19440")
    # options.add_argument("--headless")
    # options.add_argument("--incognito")
    options.add_argument("--log-level=3")
    options.add_argument("--mute-audio")
    options.add_argument("--disable-popup-blocking")
    return options

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
    use_headless = cfg.get("use_headless", False)
    driver = init_driver(use_headless=use_headless)
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