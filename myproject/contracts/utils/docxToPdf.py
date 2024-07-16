import os
import requests
import json
from dotenv import load_dotenv


def docx_to_pdf(api_key, file_url):
    # PDF.co API 엔드포인트
    upload_url = "https://api.pdf.co/v1/file/upload"
    convert_url = "https://api.pdf.co/v1/pdf/convert/from/doc"

    try:

        source_url = f"https://lawbotttt.s3.ap-northeast-2.amazonaws.com/{file_url}"
        print("\ndocxToPdf.source_url: ", source_url)
        # 파일 다운로드
        response = requests.get(source_url)
        response.raise_for_status()  # HTTP 오류가 발생한 경우 예외 발생

        # 다운로드한 파일을 로컬에 저장
        local_filename = "downloaded_file.docx"
        with open(local_filename, 'wb') as f:
            f.write(response.content)

        print(f"파일 다운로드 완료: {local_filename}")

        # 파일을 PDF.co에 업로드
        with open(local_filename, 'rb') as file:
            files = {'file': (local_filename, file)}
            headers = {"x-api-key": api_key}
            response = requests.post(upload_url, files=files, headers=headers)
            response.raise_for_status()
            upload_result = response.json()

        print("파일 업로드 결과:", upload_result)

        # 업로드된 파일의 URL
        uploaded_file_url = upload_result['url']

        # PDF.co API 호출을 위한 데이터 설정
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "url": uploaded_file_url,
            "name": "modify_result.pdf"
        }

        # PDF.co API 호출
        response = requests.post(convert_url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # HTTP 오류가 발생한 경우 예외 발생
        convert_result = response.json()

        print("PDF.co API 요청 성공:", convert_result)

        # 변환된 PDF 파일 URL
        pdf_url = convert_result['url']

        # 변환된 PDF 파일 다운로드
        response = requests.get(pdf_url)
        response.raise_for_status()  # HTTP 오류가 발생한 경우 예외 발생

        return response.content

    except requests.exceptions.RequestException as e:
        print("오류 발생:", e)
        return None
