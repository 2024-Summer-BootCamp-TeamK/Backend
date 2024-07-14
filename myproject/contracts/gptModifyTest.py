import re
import os
import requests
from dotenv import load_dotenv

from myproject.contracts.openAICallModify import use_ai

# 환경 변수 로드
load_dotenv()


# HTML 태그 제거 함수
def remove_html_tags(text):
    clean_text = re.sub('<.*?>', '', text)  # HTML 태그 제거
    return clean_text.strip()  # 앞뒤 공백 제거


# 줄바꿈 문자 제거 함수
def remove_newlines(text):
    result = text.replace('\n', '')  # 줄바꿈 문자를 공백으로 치환
    print("After removing newlines:", result)  # 디버깅 출력
    return result


# 공백을 제거한 텍스트 생성 함수
def normalize_whitespace(text):
    result = re.sub(r'\s+', '', text)
    print("After normalizing whitespace:", result)  # 디버깅 출력
    return result


# 문장 치환 함수
def replace_target_text_in_text(text, target_sentence, replacement):
    # 공백을 제거한 텍스트 생성
    normalized_text = text.replace(" ", "")
    normalized_target = target_sentence.replace(" ", "")

    if normalized_target in normalized_text:
        print("normalized_target:", normalized_target)
        start_index = normalized_text.find(normalized_target)
        print("start_index: ", start_index)

        # 실제 텍스트에서 해당 부분을 치환
        actual_start_index = text.find(target_sentence.split()[0])
        actual_end_index = actual_start_index + len(target_sentence)

        text_before = text[:actual_start_index]
        text_after = text[actual_end_index:]

        # 타겟 텍스트를 치환 텍스트로 대체
        modified_text = text_before + replacement + text_after
        return modified_text
    else:
        print("Target sentence not found in the text.")
        return text


# S3에서 HTML 파일을 가져오는 함수
def fetch_html_from_s3(url):
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'  # 인코딩 설정
        response.raise_for_status()  # 요청이 성공하지 않을 경우 예외 발생
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


# S3 URL 설정
url = f'https://{os.getenv("AWS_STORAGE_BUCKET_NAME")}.s3.ap-northeast-2.amazonaws.com/contracts/html/f64ab470-3641-4b68-ba7c-8cc0ac459809.html'

# HTML 파일 가져오기
html_content = fetch_html_from_s3(url)
if html_content:
    print("Original HTML content fetched.")  # 디버깅 출력
    # 타겟 문장과 교체할 문장 설정
    old_text1 = "고용주는 근로자의 안전과 건강을 보호하기 위해 필요한 조치를 취해야 하며, 근로자는 안전규정을 준수해야 합니다. 안전규정 위반시, 고용주는 즉시 계약을 해지할 수 있습니다. (산업안전보건법 제4조)"
    new_text1 = "(산업안전보건법 제4조) 고용주는 근로자의 안전을 보장하기 위해 필요한 조치를 취해야 하며, 근로자는 안전규정을 준수해야 합니다. 안전규정 위반 시, 고용주는 즉시 조치를 취해야 합니다."
    old_text2 = "근로자가 무단 결근할 경우, 그 날의 일급은 지급되지 않습니다. 무단 결근이 3회를 초과할 경우, 고용주는 계약을 해지할 수 있습니다. (근로기준법 제60조)"
    new_text2 = "(근로기준법 제60조) 무단 결근 시 일급은 지급되어야 하며, 무단 결근 횟수에 따라 적절한 조치를 취해야 합니다."

    # HTML의 텍스트를 교체
    text_content = remove_html_tags(html_content)
    text_content = remove_newlines(text_content)
    text_content = ' '.join(text_content.split())
    print("Text content after removing HTML and newlines:", text_content)  # 디버깅 출력

    modified_content1 = replace_target_text_in_text(text_content, old_text1, new_text1)
    print("\nModified content 1: ", modified_content1)

    modified_content2 = replace_target_text_in_text(modified_content1, old_text2, new_text2)
    print("\nModified content 2: ", modified_content2)

    # AI 모델을 사용하여 최종 수정된 텍스트를 HTML로 변환
    modified_text_html = use_ai(modified_content2)
    print("\nModified text to HTML: ", modified_text_html)
else:
    print("Failed to fetch the HTML content.")