from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# 브라우저 꺼짐 방지 옵션 설정
options = Options()
options.add_experimental_option("detach", True)

# 브라우저 시크릿 모드
options.add_argument("--incognito")

# 크롬 드라이버 실행
driver = webdriver.Chrome(options=options)

# 블로그 링크 리스트
link_list = [
    "https://blog.naver.com/test1",
    "https://blog.naver.com/test2",
    "https://blog.naver.com/test3"
]

for link in link_list:
    try:
        driver.get(link)
        time.sleep(5)  # 페이지 로딩 대기
        print(f"[성공] {link} 접속 완료")
    except Exception as e:
        print(f"[오류] {link} 접속 중 문제가 발생했습니다:", e)

# 브라우저 종료
# driver.quit()