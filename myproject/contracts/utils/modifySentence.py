import os

import requests
import json

def replaceStringFromPdf(api_key, file_url, search_strings, replace_strings):

    # api 엔드포인트
    url = "https://api.pdf.co/v1/pdf/edit/replace-text"

    # 아마존 S3 전체 링크
    source_url = f'https://{os.getenv("AWS_STORAGE_BUCKET_NAME")}.s3.ap-northeast-2.amazonaws.com/{file_url}'

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    parameters = {
        "name": "output.pdf",
        "password": "",
        "url": source_url,  # 아마존 pdf 주소(수정 전)
        "searchStrings": search_strings,  # search_strings = ["Your Company Name", "Client Name", "Item"]
        "replaceStrings": replace_strings,  # replace_strings = ["XYZ LLC", "ACME", "SKU"]
        "replacementLimit": 0
    }

    response = requests.post(url, headers=headers, data=json.dumps(parameters))

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

        with open('output.pdf', "wb") as pdf_file:
            pdf_file.write(download_response.content)
        return download_response.content
    else:
        print("Error: No URL found in the API response")