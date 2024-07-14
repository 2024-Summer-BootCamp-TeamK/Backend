import os
import re
from pdf2docx import Converter
from docx import Document
import requests
from dotenv import load_dotenv
from kiwipiepy import Kiwi
from docx2pdf import convert
import io

load_dotenv()


def process_and_convert_pdf(url: str, replacement_map: dict) -> bytes:
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

    download_pdf_from_s3(url, pdf_file)

    # PDF 파일이 존재하는지 확인
    if not os.path.isfile(pdf_file):
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_file}")

    # PDF를 Word로 변환
    cv = Converter(pdf_file)
    cv.convert(docx_file, start=0, end=None)  # 모든 페이지 변환
    cv.close()

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

    # Word 파일을 PDF로 변환
    pdf_file_output = 'output_corrected.pdf'
    convert(corrected_docx_file, pdf_file_output)
    print(f"Word 파일이 PDF로 변환되어 {pdf_file_output}에 저장되었습니다.")

    # 변환된 PDF 파일 읽기
    with open(pdf_file_output, 'rb') as pdf_file:
        pdf_data = pdf_file.read()

    return pdf_data
