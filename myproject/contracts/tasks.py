import json
import os
import uuid

import fitz
import requests
from celery import shared_task
from django.core.files.base import ContentFile
from contracts.models import Type, Contract
from .utils.openAICall import analyze_contract
from .utils.pdfToHtml import pdf_to_html_with_pdfco
from .serializers import ArticleMainSerializer


@shared_task()
def type_save_task(article, name):
    type_instance = Type.objects.get(name=name)
    article.type.add(type_instance)


@shared_task()
def pdf_to_html_task(contract):
    # S3 url 가져오기
    pdf_url = contract.origin_url.url

    # pdf -> html 코드 변환
    pdfco_api_key = os.getenv('PDFCO_API_KEY')

    html_content = pdf_to_html_with_pdfco(pdfco_api_key, pdf_url)

    # html 코드 S3에 업로드
    if html_content:
        html_file_name = f'{uuid.uuid4()}.html'

        contract.origin.save(html_file_name, ContentFile(html_content.encode('utf-8')))
        contract.save()


@shared_task(bind=True, autoretry_for=(requests.exceptions.RequestException, fitz.FileDataError),
             retry_kwargs={'max_retries': 5, 'countdown': 60 * 3})
def review_get_task(self, contractId):
    try:
        # contractId로 계약서 인스턴스 생성
        contract = Contract.objects.get(id=contractId)

        pdf_url = contract.origin_url.url
        html_url = contract.origin.url

        # 텍스트 추출
        html_response = requests.get(html_url)
        html_response.raise_for_status()
        uploaded_html_content = html_response.content.decode('utf-8')

        response = requests.get(pdf_url)
        pdf_content = response.content

        # 페이지 텍스트 추출
        pdf_document = fitz.open(stream=pdf_content, filetype='pdf')
        extracted_text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            extracted_text += page.get_text()

        raw_result = analyze_contract(extracted_text)

        # 검토 결과 JSON 형태로 변경
        parsed_result = json.loads(raw_result)
        articles = []
        for i in range(len(parsed_result)):
            article_data = {
                "contract_id": contract.id,
                "sentence": parsed_result[i].get("sentence", ""),
                "description": parsed_result[i].get("description", ""),
                "law": parsed_result[i].get("law", ""),
            }
            # 시리얼라이저를 이용해 데이터 저장
            serializer = ArticleMainSerializer(data=article_data)

            if serializer.is_valid():
                article_instance = serializer.save()

                type_instance = Type.objects.get(name="main")
                article_instance.type.add(type_instance)

                article_response = {
                    "articleId": article_instance.id,
                    "sentence": article_instance.sentence,
                    "law": article_instance.law,
                    "description": article_instance.description,
                }
                articles.append(article_response)
            else:
                return {'status': 'error', 'message': serializer.error}

        # celery의 작업 결과는 JSON 형태나, Python 형태로 반환하기
        return {
            'contractId': contract.id,
            'contract': uploaded_html_content,
            'type': "main",
            'articles': articles
        }

    except Contract.DoesNotExist:
        return {'status': 'error', 'message': 'Contract does not exist'}
    except FileNotFoundError as e:
        return {'status': 'error', 'message': 'Error fetching the file: ' + str(e)}
    except json.JSONDecodeError as e:
        return {'status': 'error', 'message': 'Error decoding JSON: ' + str(e)}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
