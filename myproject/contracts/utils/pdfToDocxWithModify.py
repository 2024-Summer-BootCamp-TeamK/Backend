import re
from kiwipiepy import Kiwi
import groupdocs_conversion_cloud
from shutil import copyfile
import requests
import os
from dotenv import load_dotenv
from docx import Document
from .docxUpload import docx_upload

load_dotenv()


def pdf_convert_docx(url: str, replacement_map: dict) -> bytes:
    """
    S3에서 PDF를 다운로드하고, 텍스트 교체 후 Word로 변환하고, 최종적으로 PDF로 변환하여 반환합니다.

    :param url: PDF 파일의 S3 URL
    :param replacement_map: 교체할 문장과 그에 대응하는 대체 문장 딕셔너리
    :return: 변환된 PDF 파일의 바이트 데이터
    """

    # PDF 파일의 로컬 경로 설정
    pdf_file = 'downloaded.pdf'
    docx_file = 'output.docx'
    corrected_docx_file = 'output_corrected.docx'

    # PDF를 다운로드하여 로컬에 저장
    def download_pdf_from_s3(url: str, local_path: str):
        try:
            response = requests.get(url)
            response.raise_for_status()  # 요청이 성공하지 않을 경우 예외 발생
            with open(local_path, 'wb') as file:
                file.write(response.content)
            print(f"PDF 파일이 {local_path}에 저장되었습니다.")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"PDF 다운로드 중 오류 발생: {e}")

    source_url = f'https://{os.getenv("AWS_STORAGE_BUCKET_NAME")}.s3.ap-northeast-2.amazonaws.com/{url}'

    download_pdf_from_s3(source_url, pdf_file)

    # PDF 파일이 존재하는지 확인
    if not os.path.isfile(pdf_file):
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_file}")

    try:
        # Get your app_sid and app_key at https://dashboard.groupdocs.cloud (free registration is required).
        app_sid = "8eb0beac-e3aa-418c-b460-eb1f7ccc895a"
        app_key = "1e8044e26747bf9a23a75b56ea5cdb62"

        # Create instance of the API
        convert_api = groupdocs_conversion_cloud.ConvertApi.from_keys(app_sid, app_key)
        file_api = groupdocs_conversion_cloud.FileApi.from_keys(app_sid, app_key)

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
        docx_file = 'sample_copy.docx'
        copyfile(response_download, docx_file)
        print("Result {}".format(response_download))
    except groupdocs_conversion_cloud.ApiException as e:
        print("Exception when calling get_supported_conversion_types:")

    # 변환된 Word 파일 열기
    doc = Document(docx_file)

    # Kiwi 형태소 분석기 초기화
    kiwi = Kiwi()

    # 공백과 줄바꿈을 제거한 교체 문장 목록 생성
    replacement_map_normalized = {
        re.sub(r'\s+', '', k): re.sub(r'\s+', '', v) for k, v in replacement_map.items()
    }

    # 원하는 문장을 교체하고, 자동 띄어쓰기 적용
    for paragraph in doc.paragraphs:
        normalized_paragraph = re.sub(r'\s+', '', paragraph.text)
        changed = False
        for before, after in replacement_map_normalized.items():
            if before in normalized_paragraph:
                corrected_paragraph = normalized_paragraph.replace(before, after)
                corrected_text = kiwi.space(corrected_paragraph)
                paragraph.text = corrected_text
                changed = True
                break
        if not changed:
            paragraph.text = kiwi.space(paragraph.text)

    # 자동 띄어쓰기가 적용된 Word 파일 저장
    doc.save(corrected_docx_file)
    uploaded_file_key = docx_upload(corrected_docx_file)

    if uploaded_file_key:
        print(f'업로드된 파일의 S3 경로: {uploaded_file_key}')
        # 여기서 필요한 작업을 수행 (예: 다운로드 URL 생성 또는 다른 처리 등)
        return uploaded_file_key
    else:
        print('파일 업로드 실패')