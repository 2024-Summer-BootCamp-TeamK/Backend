import groupdocs_conversion_cloud
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Get your app_sid and app_key at https://dashboard.groupdocs.cloud (free registration is required).
app_sid = "8eb0beac-e3aa-418c-b460-eb1f7ccc895a"
app_key = "1e8044e26747bf9a23a75b56ea5cdb62"

# Create instance of the API
convert_api = groupdocs_conversion_cloud.ConvertApi.from_keys(app_sid, app_key)
file_api = groupdocs_conversion_cloud.FileApi.from_keys(app_sid, app_key)

# S3에서 PDF 파일을 다운로드하여 로컬에 저장하는 함수
def download_pdf_from_s3(url, local_path):
    try:
        response = requests.get(url)
        response.raise_for_status()  # 요청이 성공하지 않을 경우 예외 발생
        with open(local_path, 'wb') as file:
            file.write(response.content)
        print(f"PDF 파일이 {local_path}에 저장되었습니다. 파일 크기: {os.path.getsize(local_path)} 바이트")
        with open(local_path, 'rb') as file:
            print(f"파일 헤더: {file.read(10)}")
            file.seek(0)
            print(f"파일 내용 일부: {file.read(400)}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return False
    return True

# S3 URL 설정
s3_bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")
file_key = 'contracts/af720c36-f9e8-42c9-97e8-228e1b85222a.pdf'
url = f'https://{s3_bucket_name}.s3.ap-northeast-2.amazonaws.com/{file_key}'
pdf_file = 'downloaded.pdf'

# PDF 파일을 다운로드하여 로컬에 저장
if not download_pdf_from_s3(url, pdf_file):
    raise Exception("PDF 파일 다운로드 실패")

# PDF 파일이 존재하는지 확인
if not os.path.isfile(pdf_file):
    raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_file}")

# PDF 파일이 손상되지 않았는지 확인
try:
    with open(pdf_file, 'rb') as file:
        header = file.read(4)
        if header[:4] != b'%PDF':
            raise ValueError("손상된 PDF 파일입니다.")
    print("PDF 파일이 손상되지 않았습니다.")
except Exception as e:
    raise ValueError(f"PDF 파일 확인 중 오류 발생: {e}")


try:
    # 로컬 파일을 원격 저장소에 업로드
    filename = pdf_file
    remote_name = 'input.pdf'
    output_name = 'modified.docx'
    strformat = 'docx'

    request_upload = groupdocs_conversion_cloud.UploadFileRequest(remote_name, filename)
    response_upload = file_api.upload_file(request_upload)
    print(f"파일이 업로드되었습니다: {response_upload}")

    # PDF를 DOCX로 변환
    settings = groupdocs_conversion_cloud.ConvertSettings()
    settings.file_path = remote_name
    settings.format = strformat
    settings.output_path = output_name

    loadOptions = groupdocs_conversion_cloud.PdfLoadOptions()
    loadOptions.hide_pdf_annotations = True
    loadOptions.remove_embedded_files = False
    loadOptions.flatten_all_fields = True
    loadOptions.detect_italics = True  # 이 옵션은 이탤릭체를 감지하도록 시도합니다.
    loadOptions.detect_bold = True     # 이 옵션은 굵은 글씨를 감지하도록 시도합니다.
    loadOptions.autospace = True       # 자동 띄어쓰기 설정을 활성화합니다.

    settings.load_options = loadOptions

    convertOptions = groupdocs_conversion_cloud.DocxConvertOptions()
    convertOptions.from_page = 1
    convertOptions.pages_count = 2
    convertOptions.preserve_font = True  # 글꼴 보존 옵션을 설정합니다.

    settings.convert_options = convertOptions

    request = groupdocs_conversion_cloud.ConvertDocumentRequest(settings)
    response = convert_api.convert_document(request)
    print("문서가 성공적으로 변환되었습니다: " + str(response))

    # 변환된 파일 URL
    file_url = response[0].url
    print(f"변환된 파일의 URL: {file_url}")

    # HTTPS 프로토콜을 사용하여 변환된 파일 다운로드
    file_response = requests.get(file_url.replace('http://', 'https://'), stream=True)

    # HTTP 상태 코드 확인
    if file_response.status_code == 200:
        # 파일이 제대로 다운로드되었으면 파일을 저장합니다.
        with open('modified.docx', 'wb') as f:
            for chunk in file_response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print("변환된 파일이 다운로드되었습니다.")
    else:
        print(f"파일 다운로드 실패. HTTP 상태 코드: {file_response.status_code}")

except groupdocs_conversion_cloud.ApiException as e:
    print(f"API 호출 중 예외 발생: {e}")
except Exception as e:
    print(f"알 수 없는 오류 발생: {e}")