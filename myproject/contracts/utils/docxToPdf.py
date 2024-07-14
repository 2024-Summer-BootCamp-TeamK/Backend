import json
import requests


def docx_to_pdf(api_key, file_url):
    """PDF.co 웹 API를 사용하여 DOC를 PDF로 변환"""

    # api 엔드포인트
    url = "https://api.pdf.co/v1/pdf/convert/from/doc"

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "url": file_url,
        "pages": "0-",
        "async": False,
        "name": "modify_result.pdf",

    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    response.raise_for_status()

    # JSON 응답에서 변환된 파일 URL 추출
    result_json = response.json()
    result_url = result_json.get('url')

    if result_url:
        # 변환된 파일 다운로드
        download_response = requests.get(result_url)
        download_response.raise_for_status()

        with open('output.pdf', "wb") as pdf_file:
            pdf_file.write(download_response.content)
        return download_response.content
    else:
        print("Error: No URL found in the API response")
