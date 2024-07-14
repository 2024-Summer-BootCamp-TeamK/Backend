import groupdocs_conversion_cloud
from shutil import copyfile
import requests
import os
from dotenv import load_dotenv
from docx import Document

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
        print(f"PDF 파일이 {local_path}에 저장되었습니다.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# S3 URL 설정
url = f'https://{os.getenv("AWS_STORAGE_BUCKET_NAME")}.s3.ap-northeast-2.amazonaws.com/contracts/5b3bdd00-2f6b-45c5-9ae4-27becc5bad94.pdf'
pdf_file = 'downloaded.pdf'

# PDF 파일을 다운로드하여 로컬에 저장
download_pdf_from_s3(url, pdf_file)

# PDF 파일이 존재하는지 확인
if not os.path.isfile(pdf_file):
    raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_file}")

try:

    # upload soruce file to storage
    filename = 'downloaded.pdf'
    remote_name = 'input.pdf'
    output_name = 'modified.docx'
    strformat = 'docx'

    request_upload = groupdocs_conversion_cloud.UploadFileRequest(remote_name, filename)
    response_upload = file_api.upload_file(request_upload)

    # Convert PDF to DOCX
    settings = groupdocs_conversion_cloud.ConvertSettings()
    settings.file_path = remote_name
    settings.format = strformat
    settings.output_path = output_name

    loadOptions = groupdocs_conversion_cloud.PdfLoadOptions()
    loadOptions.hide_pdf_annotations = True
    loadOptions.remove_embedded_files = False
    loadOptions.flatten_all_fields = True

    settings.load_options = loadOptions

    convertOptions = groupdocs_conversion_cloud.DocxConvertOptions()
    convertOptions.from_page = 1
    convertOptions.pages_count = 20

    settings.convert_options = convertOptions

    request = groupdocs_conversion_cloud.ConvertDocumentRequest(settings)
    response = convert_api.convert_document(request)
    print("Document converted successfully: " + str(response))

    # Download Document from Storage
    request_download = groupdocs_conversion_cloud.DownloadFileRequest(output_name)
    response_download = file_api.download_file(request_download)

    copyfile(response_download, 'sample_copy.docx')
    print("Result {}".format(response_download))
    docx_file = 'sample_copy.docx'

    # 변환된 Word 파일 읽기
    doc = Document(docx_file)

 # 변환된 Word 파일 읽기
    for paragraph in doc.paragraphs:
        print(paragraph.text)


except groupdocs_conversion_cloud.ApiException as e:
    print("Exception when calling get_supported_conversion_types:")
