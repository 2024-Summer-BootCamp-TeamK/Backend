from bs4 import BeautifulSoup
import re


def remove_tags(html):
    # BeautifulSoup을 사용하여 HTML 파싱
    soup = BeautifulSoup(html, 'html.parser')
    # 모든 태그 제거 후 텍스트 추출
    text = soup.get_text(separator=' ', strip=True)
    return text


def replace_text(original_text, before, after):
    # before 문자열을 찾아 after 문자열로 치환
    # \b 를 사용하여 단어 경계를 설정하여 정확한 패턴을 찾도록 함
    modified_text = re.sub(r'\b' + re.escape(before) + r'\b', after, original_text, flags=re.IGNORECASE)
    return modified_text


def generate_html(original_html, modified_text):
    # BeautifulSoup을 사용하여 HTML 파싱
    soup = BeautifulSoup(original_html, 'html.parser')
    # body 태그 안의 모든 내용을 추출
    body_content = ''.join([str(tag) for tag in soup.body.contents])
    # body 태그 안의 내용을 기존의 HTML 구조에 수정된 텍스트를 삽입하여 재구성
    reconstructed_html = original_html.replace(body_content, modified_text)
    return reconstructed_html


def replace_and_generate_html(html_string, before, after):
    # 1. HTML에서 태그를 제거하고 순수 텍스트 추출
    pure_text = remove_tags(html_string)
    print(pure_text)
    # 2. 특정 패턴 치환
    modified_text = replace_text(pure_text, before, after)
    print(modified_text)
    # 3. 원본 HTML 구조를 유지하면서 HTML 재구성
    reconstructed_html = generate_html(html_string, modified_text)

    return reconstructed_html

