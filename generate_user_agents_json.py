import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# 기본 설정
BASE_URL = "https://explore.whatismybrowser.com/useragents/explore/software_name/chrome/"
PAGE_RANGE = range(1, 11)               # 페이지 1 ~ 10까지
OUTPUT_FILE = "user_agents.json"        # JSON 형식으로 저장

# 셀레니움 드라이버 설정
options = Options()
options.add_argument("--headless")      # 필요시 주석 처리하여 눈으로 확인
driver = webdriver.Chrome(options=options)

# 결과 저장 리스트
all_user_agents = []

# 페이지 순회
for page_num in PAGE_RANGE:
    print(f"[접속 중] 페이지 {page_num}")
    driver.get(BASE_URL + str(page_num))
    time.sleep(2.5)  # 페이지 로딩 대기

    # 테이블 내 User-Agent 추출
    elements = driver.find_elements("css selector", "table.table-useragents td a.code")
    page_agents = [el.text.strip() for el in elements if el.text.strip()]
    print(f"  ↳ {len(page_agents)}개 추출 완료")

    all_user_agents.extend(page_agents)

# 중복 제거
unique_user_agents = list(set(all_user_agents))

# JSON 형식으로 저장
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(unique_user_agents, f, ensure_ascii=False, indent=2)

driver.quit()
print(f"\n✨ 총 {len(unique_user_agents)}개의 User-Agent 저장 완료 → {OUTPUT_FILE}")