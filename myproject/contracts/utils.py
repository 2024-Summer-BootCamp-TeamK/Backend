import requests
import json
import html
def pdf_to_html_with_pdfco(api_key, file_url):
    url = "https://api.pdf.co/v1/pdf/convert/to/html"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "url": file_url,
        "inline": False,
        "async": False
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    # 응답 내용을 출력하여 디버그
    print("Response status code:", response.status_code)
    print("Response text:", response.text)

    response.raise_for_status()

    # JSON 응답에서 변환된 파일 URL 추출
    result_json = response.json()
    result_url = result_json.get('url')

    if result_url:
        # 변환된 파일 다운로드
        download_response = requests.get(result_url)
        download_response.raise_for_status()

        # 유니코드 이스케이프 시퀀스를 디코딩
        html_content = download_response.content.decode('utf-8')
        decoded_html_content = html.unescape(html_content)

        with open('output.html', "w", encoding="utf-8") as html_file:
            html_file.write(decoded_html_content)

        return decoded_html_content
    else:
        print("Error: No URL found in the API response")
