import requests

def get_html_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 발생
        response.encoding = 'utf-8'  # 인코딩 설정
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

# 테스트 함수
url = 'https://lawbotttt.s3.ap-northeast-2.amazonaws.com/contracts/html/96143e86-2b4e-4a2e-a71d-38af88676ce7.html'
html_content = get_html_from_url(url)
if html_content:
    print(html_content)
else:
    print("Failed to fetch HTML from URL")